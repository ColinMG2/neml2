from __future__ import annotations

from neml2.factory import register_neml2_object
from neml2.models.chain_rule import ChainRuleDict, ChainRuleAction
from neml2.models.model import Model
from neml2.schema import HitSchema, buffer, input, output, parameter, option
from neml2.types import Scalar, exp, pow

from ._validation import unsupplied

@register_neml2_object("KocksMeckingMobileDensityStorageRecovery")
class KocksMeckingMobileDensityStorageRecovery(Model):

    hit = HitSchema(
        input("flow_rate", Scalar, "Equivalent plastic strain rate", attr="_flow_rate_name"),
        input("L", Scalar, "Mean free path", attr="_L_name"),
        input("rho_m", Scalar, "Mobilie dislocation density", attr="_rho_m_name"),
        input("T", Scalar, "Temperature", default=None, attr="_T_name"),
        output("rho_m_rate", Scalar, "Mobile dislocation density rate"),
        parameter("k1", Scalar, "Dislocation Storage coefficient"),
        option("thermally_activated_recovery", bool, "Whether to include thermal activation for dynamic recovery coefficient", default=True, attr="thermally_activated_recovery"),
        parameter("k2", Scalar, "Temperature-independent dynamic recovery coefficient", default=0.0),
        parameter("k2_0", Scalar, "Recovery pre-exponential factor", default=0.0),
        parameter("Q_d", Scalar, "Dynamic recovery activation energy", default=0.0),
        buffer("k_B", Scalar, "Boltzmann constant", default=0.0)
    )

    _flow_rate_name: str
    _L_name: str
    _rho_m_name: str
    _T_name: str | None
    k1: Scalar
    thermally_activated_recovery: bool
    k2: Scalar
    k2_0: Scalar
    Q_d: Scalar
    k_B: Scalar

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.thermally_activated_recovery:
            required_deps = ["k2_0", "Q_d", "k_B"]
            missing = unsupplied(kwargs, required_deps)
            if missing:
                raise ValueError(
                    f"{type(self).__name__}: include_solid_solution=True requires the "
                    f"following parmeters/buffers to be defined in the input file: {missing}"
                )
        else:
            if "k2" not in kwargs or float(kwargs["k2"]) == 0.0:
                raise ValueError(
                    f"{type(self).__name__}: include_solid_solution=False requires the "
                    f"dynamic recovery coefficient 'k2' to be explicitly defined."
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

        p_dot = bound[self._flow_rate_name]
        L = bound[self._L_name]
        rho_m = bound[self._rho_m_name]
        T = bound.get(self._T_name) if self._T_name is not None else None

        k1 = self._get_param("k1", promoted_params, Scalar)

        if self.thermally_activated_recovery:
            if T is None:
                raise ValueError(
                    f"{type(self).__name__}: thermally_activated_recovery=True requires 'T' as an input."
                )
            k2_0 = self._get_param("k2_0", promoted_params, Scalar)
            Q_d = self._get_param("Q_d", promoted_params, Scalar)

            k2 = k2_0 * exp(-Q_d / (self.k_B * T))
        else:
            k2 = self._get_param("k2", promoted_params, Scalar)

        rho_m_dot = (k1/L - k2 * rho_m) * p_dot

        if v is None:
            return rho_m_dot

        actions: dict[str, ChainRuleAction] = {}

        drho_m_dot_dp_dot = k1/L - k2 * rho_m
        actions["flow_rate"] = lambda V, c=drho_m_dot_dp_dot: c * V

        drho_m_dot_dL = -(k1 * p_dot) / pow(L, 2.0)
        actions["L"] = lambda V, c=drho_m_dot_dL: c * V

        drho_m_dot_drho_m = -k2 * p_dot
        actions["rho_m"] = lambda V, c=drho_m_dot_drho_m: c * V

        if self.thermally_activated_recovery:
            if T is None:
                raise ValueError(
                    f"{type(self).__name__}: thermally_activated_recovery=True requires 'T' as an input."
                )
            assert self.k_B is not None

            k2_0 = self._get_param("k2_0", promoted_params, Scalar)
            Q_d = self._get_param("Q_d", promoted_params, Scalar)

            drho_m_dot_dT = - (k2_0 * Q_d) / (self.k_B * pow(T, 2.0)) * exp(-Q_d / (self.k_B * T)) * rho_m * p_dot
            actions["T"] = lambda V, c=drho_m_dot_dT: c * V

        return rho_m_dot, self.apply_chain_rule(v, "rho_m_rate", actions, output=rho_m_dot)
