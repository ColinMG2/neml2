# Copyright 2024, UChicago Argonne, LLC
# All Rights Reserved
# Software Name: NEML2 -- the New Engineering material Model Library, version 2
# By: Argonne National Laboratory
# OPEN SOURCE LICENSE (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import annotations

from neml2.factory import register_neml2_object
from neml2.models.chain_rule import ChainRuleAction, ChainRuleDict
from neml2.models.model import Model
from neml2.schema import HitSchema, buffer, input, option, output, parameter
from neml2.types import Scalar, clamp, exp, heaviside, pow

@register_neml2_object("SoluteDislocationInteractionRate")
class SoluteDislocationInteractionRate(Model):

    hit = HitSchema(
        input("L", Scalar, "Mean Free Path", attr="_L_name"),
        input("T", Scalar, "Temperature", attr="_T_name"),
        input("rho_m", Scalar, "Mobile dislocation density", attr="_rho_m_name"),
        input("flow_rate", Scalar, "Equivalent plastic strain rate", attr="_flow_rate_name"),
        input("tau_ss", Scalar, "Solute dislocation interaction resistance", attr="_tau_ss_name"),
        output("tau_ss_rate", Scalar, "Rate of solute dislocaiton interaction resistanc"),
        option("flow_rate_min", float, "Add numerical guard for NR solver for flow rate",
                        default=1e-6, attr="flow_rate_min"),
        parameter("t_a0", Scalar, "Solute-interaction time prefactor"),
        parameter("Q_a", Scalar, "Solute-interaction activation energy"),
        buffer("k_B", Scalar, "Boltzmann constant"),
        buffer("m", Scalar, "Schmid factor"),
        buffer("b", Scalar, "Burger's vector magnitude"),
        parameter("tau_s0", Scalar, "Saturation solute resistance"),
        parameter(
            "p_ss",
            Scalar,
            "Solute-drag exponent (controls the transition towards saturation)",
        ),
    )

    _L_name: str
    _T_name: str
    _rho_m_name: str
    _flow_rate_name: str
    _tau_ss_name: str
    flow_rate_min: float
    t_a0: Scalar
    Q_a: Scalar
    k_B: Scalar
    b: Scalar
    m: Scalar
    tau_s0: Scalar
    p_ss: Scalar

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

        L = bound[self._L_name]
        T = bound[self._T_name]
        rho_m = bound[self._rho_m_name]
        p_dot = bound[self._flow_rate_name]

        p_dot0 = clamp(p_dot, self.flow_rate_min)

        t_w = (L * self.m * rho_m * self.b) / p_dot0

        t_a0 = self._get_param("t_a0", promoted_params, Scalar)
        Q_a = self._get_param("Q_a", promoted_params, Scalar)

        t_a = t_a0 * exp(Q_a / (self.k_B * T))

        tau_s0 = self._get_param("tau_s0", promoted_params, Scalar)
        p_ss = self._get_param("p_ss", promoted_params, Scalar)
        x = t_w / t_a
        y = pow(x, p_ss)
        y_safe = clamp(y, None, 30.0)
        tau_ss_a = tau_s0 * exp(-y_safe)

        tau_ss = bound[self._tau_ss_name]

        tau_ss_rate = (tau_ss_a - tau_ss) / t_a

        if v is None:
            return tau_ss_rate

        actions: dict[str, ChainRuleAction] = {}

        common = tau_s0 * p_ss * pow(x, p_ss - 1.0) * exp(-y_safe)

        dtau_ss_dL = -(common * self.m * rho_m * self.b) / (t_a * p_dot0)
        dtau_ss_rate_dL = dtau_ss_dL / t_a
        actions["L"] = lambda V, c=dtau_ss_rate_dL: c*V

        dtau_ss_dT = -common * (t_w * t_a * Q_a) / (self.k_B * pow(t_a, 2.0) * pow(T, 2.0))
        dt_a_dT = -t_a0 * Q_a / (self.k_B * pow(T, 2.0)) * exp(Q_a / (self.k_B * T))
        dtau_ss_rate_dT = (dtau_ss_dT * t_a - (tau_ss_a - tau_ss) * dt_a_dT) / pow(t_a, 2.0)
        actions["T"] = lambda V, c=dtau_ss_rate_dT: c*V

        dtau_ss_drho_m = -(common * self.m * L * self.b) / (t_a * p_dot0)
        dtau_ss_rate_drho_m = dtau_ss_drho_m/t_a
        actions["rho_m"] = lambda V, c=dtau_ss_rate_drho_m: c*V

        p_dot_live = heaviside(p_dot - self.flow_rate_min)
        dtau_ss_dflow_rate = (common * L * self.m * rho_m * self.b * p_dot_live) / (t_a * pow(p_dot0, 2.0))
        dtau_ss_rate_dflow_rate = dtau_ss_dflow_rate/t_a
        actions["flow_rate"] = lambda V, c=dtau_ss_rate_dflow_rate : c*V

        dtau_ss_rate_dtau_ss = -1/t_a
        actions["tau_ss"] = lambda V, c=dtau_ss_rate_dtau_ss: c*V

        return tau_ss_rate, self.apply_chain_rule(
            v, "tau_ss_rate", actions, output=tau_ss_rate
        )
