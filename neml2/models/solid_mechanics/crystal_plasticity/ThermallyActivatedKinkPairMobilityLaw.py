from __future__ import annotations

from neml2.factory import register_neml2_object
from neml2.models.chain_rule import ChainRuleDict, ChainRuleAction
from neml2.models.model import Model
from neml2.schema import HitSchema, buffer, input, output, parameter
from neml2.types import Scalar, exp, pow, macaulay, clamp, heaviside
import math

@register_neml2_object("ThermallyActivatedKinkPairMobilityLaw")
class ThermallyActivatedKinkPairMobilityLaw(Model):

    hit = HitSchema(
        input("sigma_eff", Scalar, "Effective stress (von mises)", attr="_sigma_eff_name"),
        input("sigma_0", Scalar, "Athermal-solute resistance", attr="_sigma_0_name"),
        input("T", Scalar, "Temperature", attr="_T_name"),
        output("v_disl", Scalar, "BCC screw mobile dislocation velocity"),
        buffer("a", Scalar, "Lattice constant"),
        buffer("k_B", Scalar, "Boltzmann constant"),
        buffer("m", Scalar, "Schmid factor"),
        parameter("B_k", Scalar, "Kink drag coefficient"),
        parameter("tau_p", Scalar, "Peierl's stress"),
        parameter("T_0", Scalar, "Athermal transition temperature"),
        parameter("p", Scalar, "Mobility fitting exponent p"),
        parameter("q", Scalar, "Mobility fitting exponent q"),
        parameter("H_0", Scalar, "Reference activation enthalpy")
    )

    _sigma_eff_name: str
    _sigma_0_name: str
    _T_name: str
    a: Scalar
    k_B: Scalar
    m: Scalar
    B_k: Scalar
    tau_p: Scalar
    T_0: Scalar
    p: Scalar
    q: Scalar
    H_0: Scalar

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

        sigma_eff = bound[self._sigma_eff_name]
        sigma_0 = bound[self._sigma_0_name]
        T = bound[self._T_name]
        B_k = self._get_param("B_k", promoted_params, Scalar)
        tau_p = self._get_param("tau_p", promoted_params, Scalar)
        T_0 = self._get_param("T_0", promoted_params, Scalar)
        p = self._get_param("p", promoted_params, Scalar)
        q = self._get_param("q", promoted_params, Scalar)
        H_0 = self._get_param("H_0", promoted_params, Scalar)

        b = math.sqrt(3) / 2 * self.a
        h = math.sqrt(2/3) * self.a
        w = 25 * self.a

        K = (2 * h * b) / (w * B_k)
        tau_eff = self.m * sigma_eff
        tau_0 = self.m * sigma_0
        tau_1 = macaulay(tau_eff - tau_0)
        tau_tilda = tau_1 / tau_p
        tau_ratio = clamp(tau_tilda, 0.0, 1.0 - 1.0e-6)
        dg = pow(1.0 - pow(tau_ratio, p), q) - T / T_0
        dg1 = macaulay(dg)
        exp_core = -H_0 * dg1 / (2.0 * self.k_B * T)
        exp_val = exp(exp_core)
        v_disl = K * tau_1 * exp_val

        if v is None:
            return v_disl

        actions: dict[str, ChainRuleAction] = {}

        dtau_1_dsigma_eff = heaviside(tau_eff - tau_0) * self.m
        dtau_tilda_dtau_eff = 1.0 / tau_p * dtau_1_dsigma_eff
        ddg_dtau_eff = heaviside(dg) * q * pow(1 - pow(tau_ratio, p), q - 1.0) * -p * pow(tau_ratio, p - 1.0) * dtau_tilda_dtau_eff
        dv_disl_dtau_eff = K * dtau_1_dsigma_eff * exp_val - K * tau_1 * H_0 / (2 * self.k_B * T) * ddg_dtau_eff * exp_val
        actions["sigma_eff"] = lambda V, c=dv_disl_dtau_eff: c * V

        dtau_1_dsigma_0 = -heaviside(tau_eff - tau_0) * self.m
        dtau_tilda_dtau_0 = 1.0 / tau_p * dtau_1_dsigma_0
        ddg_dtau_0 = heaviside(dg) * q * pow(1.0 - pow(tau_ratio, p), q - 1.0) * -p * pow(tau_ratio, p - 1.0) * dtau_tilda_dtau_0
        dv_disl_dtau_0 = K * dtau_1_dsigma_0 * exp_val - K * tau_1 * H_0 / (2.0 * self.k_B * T) * ddg_dtau_0 * exp_val
        actions["sigma_0"] = lambda V, c=dv_disl_dtau_0: c * V

        dexp_core_dT = H_0 / (2 * self.k_B * pow(T, 2.0)) * dg1 + H_0 / (2 * self.k_B * T * T_0) * heaviside(dg)
        dv_disl_dT = K * tau_1 * dexp_core_dT * exp_val
        actions["T"] = lambda V, c=dv_disl_dT: c * V

        return v_disl, self.apply_chain_rule(v, "v_disl", actions, output=v_disl)
