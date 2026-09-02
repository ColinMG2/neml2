from __future__ import annotations

from neml2.factory import register_neml2_object
from neml2.models.chain_rule import ChainRuleDict, ChainRuleAction
from neml2.models.model import Model
from neml2.schema import HitSchema, buffer, input, output
from neml2.types import Scalar

@register_neml2_object("OrowanPlasticShearRate")
class OrowanPlasticShearRate(Model):

    hit = HitSchema(
        input("rho_m", Scalar, "Mobile dislocation density", attr="_rho_m_name"),
        input("v_disl", Scalar, "BCC screw dislocation velocity", attr="_v_disl_name"),
        output("gamma_dot", Scalar, "Plastic shear flow rate"),
        buffer("b", Scalar, "Burger's vector magnitude")
    )

    _rho_m_name: str
    _v_disl_name: str
    b: Scalar

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
        v_disl = bound[self._v_disl_name]

        gamma_dot = rho_m * self.b * v_disl

        if v is None:
            return gamma_dot

        actions: dict[str, ChainRuleAction] = {}

        dgamma_dot_drho_m = self.b * v_disl
        actions["rho_m"] = lambda V, c=dgamma_dot_drho_m: c * V

        dgamma_dot_dv_disl = rho_m * self.b
        actions["v_disl"] = lambda V, c=dgamma_dot_dv_disl: c * V

        return gamma_dot, self.apply_chain_rule(v, "gamma_dot", actions, output=gamma_dot)