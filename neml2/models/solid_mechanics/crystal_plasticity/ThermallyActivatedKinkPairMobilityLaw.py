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

import math

from neml2.factory import register_neml2_object
from neml2.models.chain_rule import ChainRuleAction, ChainRuleDict
from neml2.models.model import Model
from neml2.schema import HitSchema, buffer, input, option, output, parameter
from neml2.types import Scalar, clamp, exp, heaviside, log, macaulay, pow


@register_neml2_object("ThermallyActivatedKinkPairMobilityLaw")
class ThermallyActivatedKinkPairMobilityLaw(Model):
    r"""Screw-dislocation glide velocity set by thermally activated kink-pair nucleation
    over the Peierls barrier -- the rate-limiting mechanism for BCC metals below the
    athermal transition temperature $T_0$.

    Both stress inputs arrive in **equivalent-stress space** and are resolved onto the
    slip system here with the Schmid factor $\bar{m}$, so the driving stress is
    $$
    \tau^* = \left\langle \bar{m}\sigma_{\mathrm{eff}} - \bar{m}\sigma_0 \right\rangle,
    $$
    where $\sigma_{\mathrm{eff}}$ is the von Mises effective stress and $\sigma_0$ the
    isotropic (athermal + solute) resistance. A resistance expressed as a *resolved
    shear* stress -- the Taylor form $\alpha G b/L$, for instance -- must therefore be
    divided by $\bar{m}$ before it is handed in; see
    :class:`AthermalSoluteIsotropicHardening`, which does exactly that.

    The normalized driving stress $\hat\tau = \tau^*/\tau_p$ sets the activation
    enthalpy, which is Macaulay-clamped so it vanishes once thermal energy alone can
    carry the kink pair over the barrier:
    $$
    \Delta G = H_0 \left[ \left(1 - \hat\tau^{\,p}\right)^{q} - \frac{T}{T_0} \right],
    \qquad
    v_{\mathrm{disl}} = \frac{2 h b}{w B_k}\, \tau^*
        \exp\!\left(-\frac{\langle \Delta G \rangle}{2 k_B T}\right).
    $$
    The factor of two in the exponent is intentional: the barrier is traversed by a
    *pair* of kinks. The kink geometry is fixed to the lattice constant $a$ as
    $b = \tfrac{\sqrt{3}}{2}a$ (Burgers vector), $h = \sqrt{2/3}\,a$ (kink height) and
    $w = 25a$ (kink-pair separation), and $T_0$ is conventionally $0.9\,T_m$.

    Above roughly $0.35\,T_0$ the zero-stress factor
    $\exp(-H_0 (1 - T/T_0) / 2 k_B T)$ is large enough that the imposed strain rate
    is carried by $\tau^* \ll 1$ MPa, so the implicit solution sits on the corner of
    the Macaulay bracket: the plastic Jacobian jumps from zero (elastic side) to
    $\bar{m}^2 K \exp(\cdot)$ (plastic side) and Newton cycles between the two
    branches. Setting ``smoothing_width`` $= s > 0$ replaces the bracket with the
    softplus $\tau^* = s \ln(1 + e^{x/s})$, $x = \bar{m}(\sigma_{\mathrm{eff}} -
    \sigma_0)$, whose derivative is the logistic $1/(1 + e^{-x/s})$. The shift in
    flow stress is $O(s)$; $s \approx 0.1$ MPa is enough to remove the corner.
    """

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
        parameter("H_0", Scalar, "Reference activation enthalpy"),
        option(
            "tau_hat_min",
            float,
            "Derivative-only floor on the normalized driving stress tau*/tau_p. With "
            "p < 1 the barrier derivative carries tau_hat**(p-1), which diverges at "
            "incipient yield (tau* -> 0) and poisons the Jacobian with NaN. The "
            "residual itself is untouched.",
            default=1.0e-6,
            attr="tau_hat_min",
        ),
        option(
            "smoothing_width",
            float,
            "Resolved-stress width (stress units) of the softplus that replaces the "
            "Macaulay bracket <m*sigma_eff - m*sigma_0>. 0 keeps the exact bracket; a "
            "small positive value (~0.1 MPa) removes the yield corner that stalls "
            "Newton near the athermal plateau.",
            default=0.0,
            attr="smoothing_width",
        ),
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
    tau_hat_min: float
    smoothing_width: float

    def _driving_stress(self, x: Scalar) -> tuple[Scalar, Scalar]:
        """Driving stress $\\tau^*(x)$ and its slope $d\\tau^*/dx$."""
        s = self.smoothing_width
        if s <= 0.0:
            return macaulay(x), heaviside(x)
        # Overflow-safe softplus: <x> + s*ln(1 + exp(-|x|/s)).
        abs_x = macaulay(x) + macaulay(-x)
        return macaulay(x) + s * log(1.0 + exp(-abs_x / s)), 1.0 / (1.0 + exp(-x / s))

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
        h = math.sqrt(2 / 3) * self.a
        w = 25 * self.a

        K = (2 * h * b) / (w * B_k)
        tau_eff = self.m * sigma_eff
        tau_0 = self.m * sigma_0
        tau_1, dtau_1_dx = self._driving_stress(tau_eff - tau_0)
        tau_tilda = tau_1 / tau_p
        tau_ratio = clamp(tau_tilda, 0.0, 1.0 - 1.0e-6)
        dg = H_0 * (pow(1.0 - pow(tau_ratio, p), q) - T / T_0)
        dg1 = macaulay(dg)
        exp_core = -dg1 / (2.0 * self.k_B * T)
        exp_clamp = clamp(exp_core, -100.0, 50.0)
        exp_val = exp(exp_clamp)
        v_disl = K * tau_1 * exp_val

        if v is None:
            return v_disl

        actions: dict[str, ChainRuleAction] = {}

        # Derivative-only floor (the residual keeps the unfloored tau_ratio): p < 1
        # makes tau_ratio**(p-1) singular as tau* -> 0, i.e. at every elastic step.
        tau_ratio_d = clamp(tau_ratio, self.tau_hat_min, 1.0 - 1.0e-6)

        dtau_1_dsigma_eff = dtau_1_dx * self.m
        dtau_tilda_dtau_eff = 1.0 / tau_p * dtau_1_dsigma_eff
        ddg_dtau_eff = (
            heaviside(dg)
            * q
            * pow(1 - pow(tau_ratio, p), q - 1.0)
            * -p
            * pow(tau_ratio_d, p - 1.0)
            * dtau_tilda_dtau_eff
        )
        dv_disl_dtau_eff = (
            K * dtau_1_dsigma_eff * exp_val
            - K * tau_1 * H_0 / (2 * self.k_B * T) * ddg_dtau_eff * exp_val
        )
        actions["sigma_eff"] = lambda V, c=dv_disl_dtau_eff: c * V

        dtau_1_dsigma_0 = -dtau_1_dx * self.m
        dtau_tilda_dtau_0 = 1.0 / tau_p * dtau_1_dsigma_0
        ddg_dtau_0 = (
            heaviside(dg)
            * q
            * pow(1.0 - pow(tau_ratio, p), q - 1.0)
            * -p
            * pow(tau_ratio_d, p - 1.0)
            * dtau_tilda_dtau_0
        )
        dv_disl_dtau_0 = (
            K * dtau_1_dsigma_0 * exp_val
            - K * tau_1 * H_0 / (2.0 * self.k_B * T) * ddg_dtau_0 * exp_val
        )
        actions["sigma_0"] = lambda V, c=dv_disl_dtau_0: c * V

        dexp_core_dT = (H_0 * heaviside(dg)) / (2.0 * self.k_B * T * T_0) + dg1 / (
            2.0 * self.k_B * pow(T, 2.0)
        )
        dv_disl_dT = K * tau_1 * dexp_core_dT * exp_val
        actions["T"] = lambda V, c=dv_disl_dT: c * V

        return v_disl, self.apply_chain_rule(v, "v_disl", actions, output=v_disl)
