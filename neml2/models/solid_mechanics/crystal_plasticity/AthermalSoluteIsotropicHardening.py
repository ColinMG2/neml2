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

from ._validation import unsupplied


@register_neml2_object("AthermalSoluteIsotropicHardening")
class AthermalSoluteIsotropicHardening(Model):
    r"""The isotropic resistance combines an athermal microstructural term $\sigma_a$ and a solute
    term $\sigma_{ss}$,
    written as:
    $$
    \sigma_0=\sigma_a+\sigma_{ss}
    $$

    $\sigma_a$ is an Orowan-type obstacle strengthening from a population with
    mean free path $L$ calculated as:
    $$
    \sigma_a=\frac{\alpha G b}{\bar{m} L}
    $$

    Every resistance this model returns lives in **equivalent-stress space**, because
    that is what the consumers expect: the mobility law resolves it onto the slip
    system itself via $\tau_0 = \bar{m}\sigma_0$, and the yield surface uses it as an
    isotropic hardening term. The Taylor expression $\alpha G b / L$ is a *resolved
    shear* resistance, so it carries an explicit $1/\bar{m}$ here -- exactly as the
    solute term below carries one. Dropping either $1/\bar{m}$ resolves the resistance
    onto the slip system twice and makes the athermal barrier a factor $\bar{m}$ too
    small.

    When ``include_solid_solution`` is set to ``true``, a thermally-activated solute-drag
    term $\sigma_{ss}$ describes the interaction between mobile dislocations and
    diffusing solute atoms. This term should be set to ``false`` for polycrystal
    materials (e.g., tungsten) and should be set to ``true`` for RAFM steel to
    capture the dynamic strain-aging regime, including
    flow stress plateau and suppressed strain-rate sensitivity observed at
    intermediate temperatures. The expression is based on
    the ratio of the dislocation waiting time
    $t_w = L / v_{disl} = L\bar{m} \rho_m b / \dot{p}$ and an Arrhenius solute-interaction
    time $t_a = t_{a,0} \exp(Q_a / (k_B T))$:
    $$
    \tau_{ss} = \tau_{s,0} \exp\!\left[-\left(\frac{t_w}{t_a}\right)^{p_{ss}}\right],
    \qquad
    \sigma_{ss} = \frac{\tau_{ss}}{\bar{m}}
    $$
    and the total resistance is $\sigma_0 = \sigma_a + \sigma_{ss}$
    (otherwise $\sigma_0 = \sigma_a$).

    Note: unlike the original C++ implementation, ``temperature`` and
    ``v_disl`` are declared as *optional* inputs (only entering the model's
    dependency graph when actually supplied in the input file), but
    ``t_a0``, ``Q_a``, ``k_B``, ``tau_s0``, and ``p_ss`` are declared
    as *required* parameters here for simplicity -- you must still supply
    them in the input file even when ``include_solid_solution = False``.
    ``m`` is required unconditionally, since $\sigma_a$ needs it too.
    """

    hit = HitSchema(
        input("L", Scalar, "Mean Free Path", attr="_L_name"),
        input("T", Scalar, "Temperature", default=None, attr="_T_name"),
        input("rho_m", Scalar, "Mobile dislocation density", default=None, attr="_rho_m_name"),
        input(
            "flow_rate",
            Scalar,
            "Equivalent plastic strain rate",
            default=None,
            attr="_flow_rate_name",
        ),
        output("athermal_solute_resistance", Scalar, "Athermal solute resistance"),
        option("flow_rate_min", float, "Add numerical guard for NR solver for flow rate",
                default=1e-6, attr="flow_rate_min"),
        parameter("G", Scalar, "Shear Modulus"),
        parameter("alpha", Scalar, "Taylor interaction constant"),
        buffer("b", Scalar, "Burger's vector magnitude"),
        option(
            "include_solid_solution",
            bool,
            "Whether to include the Arrhenius-type solute resistance.",
            default=True,
            attr="include_solid_solution",
        ),
        parameter("t_a0", Scalar, "Solute-interaction time prefactor", default=0.0),
        parameter("Q_a", Scalar, "Solute-interaction activation energy", default=0.0),
        buffer("k_B", Scalar, "Boltzmann constant", default=0.0),
        buffer("m", Scalar, "Schmid factor"),
        parameter("tau_s0", Scalar, "Saturation solute resistance", default=0.0),
        parameter(
            "p_ss",
            Scalar,
            "Solute-drag exponent (controls the transition towards saturation)",
            default=0.0,
        ),
    )

    _L_name: str
    _T_name: str | None
    _rho_m_name: str | None
    _flow_rate_name: str | None
    flow_rate_min: float
    G: Scalar
    alpha: Scalar
    b: Scalar
    include_solid_solution: bool
    t_a0: Scalar
    Q_a: Scalar
    k_B: Scalar
    m: Scalar
    tau_s0: Scalar
    p_ss: Scalar

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.include_solid_solution:
            required_deps = ["t_a0", "Q_a", "k_B", "tau_s0", "p_ss"]
            missing = unsupplied(kwargs, required_deps)
            if missing:
                raise ValueError(
                    f"{type(self).__name__}: include_solid_solution=True requires the "
                    f"following parmeters/buffers to be defined in the input file: {missing}"
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

        L = bound[self._L_name]
        T = bound.get(self._T_name) if self._T_name is not None else None
        rho_m = bound.get(self._rho_m_name) if self._rho_m_name is not None else None
        p_dot = bound.get(self._flow_rate_name) if self._flow_rate_name is not None else None

        G = self._get_param("G", promoted_params, Scalar)
        alpha = self._get_param("alpha", promoted_params, Scalar)
        b = self.b

        # alpha*G*b/L is the Taylor *resolved shear* resistance; divide by the Schmid
        # factor so the returned sigma_0 is in equivalent-stress space, which is what
        # the mobility law (tau_0 = m*sigma_0) and the yield surface both assume.
        sigma_a = alpha * G * b / (L * self.m)
        sigma_0 = sigma_a

        if self.include_solid_solution:
            if T is None or rho_m is None or p_dot is None:
                raise ValueError(
                    f"{type(self).__name__}: include_solid_solution=True requires both "
                    "'temperature', 'rho_m', and 'flow_rate' to be supplied as inputs."
                )
            assert self.m is not None
            assert self.k_B is not None
            T0 = T
            rho_m0 = rho_m
            p_dot0 = p_dot

            p_dot_eff = clamp(p_dot0, self.flow_rate_min)

            t_w = (L * self.m * rho_m0 * b) / p_dot_eff

            t_a0 = self._get_param("t_a0", promoted_params, Scalar)
            Q_a = self._get_param("Q_a", promoted_params, Scalar)
            t_a = t_a0 * exp(Q_a / (self.k_B * T0))

            tau_s0 = self._get_param("tau_s0", promoted_params, Scalar)
            p_ss = self._get_param("p_ss", promoted_params, Scalar)
            x = t_w / t_a
            y = pow(x, p_ss)
            y_safe = clamp(y, None, 30.0)
            tau_ss = tau_s0 * exp(-y_safe)

            sigma_ss = tau_ss / self.m

            sigma_0 = sigma_a + sigma_ss

        if v is None:
            return sigma_0

        dsigma_0_dL = -sigma_a / L
        actions: dict[str, ChainRuleAction] = {}

        if self.include_solid_solution:
            if T is None or rho_m is None or p_dot is None:
                raise ValueError(
                    f"{type(self).__name__}: include_solid_solution=True requires both "
                    "'temperature', 'rho_m', and 'flow_rate' to be supplied as inputs."
                )
            assert self.m is not None
            assert self.k_B is not None

            T0 = T
            rho_m0 = rho_m
            p_dot0 = p_dot
            p_dot_eff = clamp(p_dot0, self.flow_rate_min)
            t_w = (L * self.m * rho_m * b) / p_dot_eff

            t_a0 = self._get_param("t_a0", promoted_params, Scalar)
            Q_a = self._get_param("Q_a", promoted_params, Scalar)
            tau_s0 = self._get_param("tau_s0", promoted_params, Scalar)
            p_ss = self._get_param("p_ss", promoted_params, Scalar)
            t_a = t_a0 * exp(Q_a / (self.k_B * T0))
            x = t_w / t_a
            y = pow(x, p_ss)
            y_safe = clamp(y, None, 30.0)
            tau_ss = tau_s0 * exp(-y_safe)

            common = (tau_s0 * p_ss) / self.m * pow(x, p_ss - 1.0) * exp(-y_safe)

            dsigma_ss_dL = -(common * self.m * rho_m0 * b) / (t_a * p_dot_eff)
            dsigma_0_dL = dsigma_0_dL + dsigma_ss_dL

            dsigma_0_dT = -common * (t_w * t_a * Q_a) / (self.k_B * pow(t_a, 2.0) * pow(T, 2.0))
            actions["T"] = lambda V, c=dsigma_0_dT: c * V

            dsigma_0_drho_m = -(common * self.m * L * b) / (t_a * p_dot_eff)
            actions["rho_m"] = lambda V, c=dsigma_0_drho_m: c * V

            # p_dot_eff = clamp(p_dot0, self.flow_rate_min) is locally constant
            # where the floor binds, so the true derivative w.r.t. flow_rate is
            # zero there -- gate it the same way MeanFreePath.rho_min /
            # ScalarExponential.exponent_max gate their own clamped inputs.
            # (L, T, rho_m don't enter this clamp, so their actions need no gate.)
            p_dot_live = heaviside(p_dot0 - self.flow_rate_min)
            dsigma_0_dflow_rate = common * L * self.m * rho_m0 * b / (t_a * pow(p_dot_eff, 2.0))
            actions["flow_rate"] = lambda V, c=dsigma_0_dflow_rate * p_dot_live: c * V

        actions["L"] = lambda V, c=dsigma_0_dL: c * V

        return sigma_0, self.apply_chain_rule(
            v, "athermal_solute_resistance", actions, output=sigma_0
        )
