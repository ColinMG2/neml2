from __future__ import annotations

from neml2.factory import register_neml2_object
from neml2.models.chain_rule import ChainRuleDict, ChainRuleAction
from neml2.models.model import Model
from neml2.schema import HitSchema, buffer, input, output, parameter, option
from neml2.types import Scalar, sqrt, pow
import math

@register_neml2_object("MeanFreePath")
class MeanFreePath(Model):

    hit = HitSchema(
        input("rho_m", Scalar, "Mobile dislocation density", attr="_rho_m_name"),
        output("L", Scalar, "Mean free path"),
        option("use_L2", bool, "Whether to include grain or sub-grain barriers", default=True, attr="use_L2"),
        option("use_L3", bool, "Whether to include precipitate obstacles", default=True, attr="use_L3"),
        parameter("c_lath", Scalar, "Geometric factor for lath boundary", default=0.0),
        parameter("d_lath", Scalar, "Martensitic lath width", default=0.0),
        parameter("c_block", Scalar, "Geometric factor for block boundary", default=0.0),
        parameter("d_block", Scalar, "Mean block width", default=0.0),
        parameter("c_packet", Scalar, "Geometric factor for packet boundary", default=0.0),
        parameter("d_packet", Scalar, "Mean packet size", default=0.0),
        parameter("c_PAG", Scalar, "Geometric factor for prior-austenite grain (PAG) boundary", default=0.0),
        parameter("d_PAG", Scalar, "Mean PAG size", default=0.0),
        parameter("c_MX", Scalar, "Geometric factor for MX precipitate", default=0.0),
        parameter("d_MX", Scalar, "Mean MX precipitate spacing", default=0.0),
        parameter("c_M23C6", Scalar, "Geometric factor for M23C6 precipitate", default=0.0),
        parameter("d_M23C6", Scalar, "Mean M23C6 precipitate spacing", default=0.0)
    )

    _rho_m_name: str
    use_L2: bool
    use_L3: bool
    c_lath: Scalar
    d_lath: Scalar
    c_block: Scalar
    d_block: Scalar
    c_packet: Scalar
    d_packet: Scalar
    c_PAG: Scalar
    d_PAG: Scalar
    c_MX: Scalar
    d_MX: Scalar
    c_M23C6: Scalar
    d_M23C6: Scalar

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.use_L2:
            required_deps = ["c_lath", "d_lath", "c_block", "d_block", "c_packet", "d_packet", "c_PAG", "d_PAG"]
            missing = [dep for dep in required_deps if math.isnan(float(kwargs[dep]))]
            if missing:
                raise ValueError(
                f"{type(self).__name__}: use_L2=True requires the following parameters "
                f"to be defined in the input file: {missing}"
            )
        if self.use_L3:
            required_deps = ["c_MX", "d_MX", "c_M23C6", "d_M23C6"]
            missing = [dep for dep in required_deps if float(kwargs[dep]) == 0.0]
            if missing:
                raise ValueError(
                    f"{type(self).__name__}: use_L3=True requires the following parameters "
                    f"to be defined in the input file: {missing}"
                )

    def forward(
            self,
            *args: Scalar,
            v: ChainRuleDict | None = None,
            **_: object,
    ) -> Scalar | tuple[Scalar, ChainRuleDict]:
        names = list(self.input_spec)
        n_in = len(names)
        inputs, promoted_params = args[:n_in], args[n_in:]
        bound = dict(zip(names, inputs, strict=True))

        rho_m = bound[self._rho_m_name]
        inv_L = sqrt(rho_m)

        if self.use_L2:
            c_lath = self._get_param("c_lath", promoted_params, Scalar)
            d_lath = self._get_param("d_lath", promoted_params, Scalar)
            c_block = self._get_param("c_block", promoted_params, Scalar)
            d_block = self._get_param("d_block", promoted_params, Scalar)
            c_packet = self._get_param("c_packet", promoted_params, Scalar)
            d_packet = self._get_param("d_packet", promoted_params, Scalar)
            c_PAG = self._get_param("c_PAG", promoted_params, Scalar)
            d_PAG = self._get_param("d_PAG", promoted_params, Scalar)

            inv_L2 = (c_lath/d_lath + c_block/d_block + c_packet/d_packet + c_PAG/d_PAG)
            inv_L += inv_L2

        if self.use_L3:
            c_MX = self._get_param("c_MX", promoted_params, Scalar)
            d_MX = self._get_param("d_MX", promoted_params, Scalar)
            c_M23C6 = self._get_param("c_M23C6", promoted_params, Scalar)
            d_M23C6 = self._get_param("d_M23C6", promoted_params, Scalar)

            inv_L3 = (c_MX/d_MX + c_M23C6/d_M23C6)
            inv_L += inv_L3

        else:
            lambda_micro = 0.0
            inv_L += lambda_micro

        L = 1.0 / inv_L

        if v is None:
            return L

        actions: dict[str, ChainRuleAction] = {}

        # Let S = inv_L = sqrt(rho_m) + lambda_micro
        dS_drho_m = 1/(2 * sqrt(rho_m))
        dL_drho_m = -pow(L, 2.0) * dS_drho_m
        actions["rho_m"] = lambda V, c=dL_drho_m: c * V

        return L, self.apply_chain_rule(v, "L", actions, output=L)