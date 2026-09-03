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

"""Generic scalar exponential map."""

from __future__ import annotations

from ...factory import register_neml2_object
from ...schema import HitSchema, input, option, output, parameter
from ...types import Scalar, clamp, exp, heaviside
from ..chain_rule import ChainRuleAction, ChainRuleDict, SecondOrderChainRuleDict
from ..model import Model


@register_neml2_object("ScalarExponential")
class ScalarExponential(Model):
    r"""Exponential map between two Scalar variables,

    $$
    y = A \exp(s x)
    $$

    where $A$ is ``scaling`` and $s$ is ``rate``.

    The derivatives reuse the primal, $\partial y / \partial x = s y$ and
    $\partial^2 y / \partial x^2 = s^2 y$, so they cost nothing extra and cannot
    disagree with the forward value.

    The principal use is reparameterizing a strictly positive internal variable.
    Solving for $x = \ln \rho$ rather than $\rho$ makes positivity structural
    (no floor or clamp can be violated by a Newton iterate) and compresses a
    quantity spanning many orders of magnitude onto a scale comparable with the
    other unknowns, which matters when a norm-based convergence test is shared
    across the whole residual vector.
    """

    # d2y/dx2 = s^2 y, and the cross term with a promoted ``scaling`` is
    # exp(s x) * s, both expressible as primal-shape bilinears.
    SUPPORTS_SECOND_ORDER = True

    hit = HitSchema(
        input("from", Scalar, "Scalar variable to exponentiate", attr="_from"),
        output("to", Scalar, "The exponential map of the input", attr="_to"),
        parameter(
            "scaling",
            Scalar,
            "Multiplicative prefactor A in A*exp(s*x)",
            default="1",
            attr="scaling",
            allow_promotion=True,
        ),
        parameter(
            "rate",
            Scalar,
            "Exponent coefficient s in A*exp(s*x)",
            default="1",
            attr="rate",
            allow_promotion=True,
        ),
        option(
            "exponent_max",
            float,
            "Overflow guard. The exponent s*x is clamped to [-exponent_max, "
            "exponent_max] before exp; float64 exp overflows above about 709, and "
            "an overflow poisons the whole solve with NaN rather than failing "
            "cleanly. Only a nonphysical iterate can reach the bound, and the "
            "derivative branch is zeroed where it binds so residual and Jacobian "
            "stay consistent. Raise it only if the primal genuinely needs a wider "
            "range than float64 exp supports.",
            default=700.0,
            attr="exponent_max",
        ),
    )

    _from: str
    _to: str
    scaling: Scalar
    rate: Scalar
    exponent_max: float

    def forward(  # type: ignore[override]
        self,
        *args: Scalar,
        v: ChainRuleDict | None = None,
        v2: SecondOrderChainRuleDict | None = None,
        vh: ChainRuleDict | None = None,
    ):
        # One structural input, followed by the promoted-parameter pack holding
        # any mode-3/4 promoted parameters (scaling and/or rate as runtime
        # inputs).
        x, promoted_params = args[0], args[1:]
        A = self._get_param("scaling", promoted_params, Scalar)
        s = self._get_param("rate", promoted_params, Scalar)

        z_raw = s * x
        z = clamp(z_raw, -self.exponent_max, self.exponent_max)
        y = A * exp(z)

        if v is None:
            return y

        # Where the overflow clamp binds, y no longer depends on x or s, so those
        # branches are zeroed. ``live`` is 1 strictly inside the bound, 0 outside.
        live = heaviside(self.exponent_max - z_raw) * heaviside(z_raw + self.exponent_max)

        # dy/dx = s*y. Reusing the primal keeps value and Jacobian consistent by
        # construction and avoids a second exp evaluation.
        actions: dict[str, ChainRuleAction] = {self._from: lambda V, c=s * y * live: c * V}

        # dy/dA = y/A = exp(z) -- unaffected by the clamp, which only bounds the
        # exponent. dy/ds = x*y, which the clamp does gate.
        exp_z = exp(z)
        nlp_A = self._promoted_params.get("scaling")
        if nlp_A is not None:
            actions[nlp_A.input_name] = lambda V, c=exp_z: c * V
        nlp_s = self._promoted_params.get("rate")
        if nlp_s is not None:
            actions[nlp_s.input_name] = lambda V, c=x * y * live: c * V

        if v2 is None and vh is None:
            return y, *self.propagate_tangents(v, self._to, actions, output=y)

        # Second order. Each action receives primal-shape Scalar tangents and
        # returns a primal-shape Scalar bilinear.
        # Every branch that differentiates the exponent is gated by ``live`` for
        # the same reason as first order.
        actions_2: dict = {}
        actions_2[(self._from, self._from)] = lambda Va, Vb, c=s * s * y * live: c * Va * Vb

        if nlp_A is not None:
            A_name = nlp_A.input_name
            # d2y/dA2 = 0; d2y/dA dx = s*exp(z).
            cross_A = s * exp_z * live
            actions_2[(A_name, self._from)] = lambda Va, Vb, c=cross_A: c * Va * Vb
            actions_2[(self._from, A_name)] = lambda Va, Vb, c=cross_A: c * Va * Vb
        if nlp_s is not None:
            s_name = nlp_s.input_name
            # d2y/ds2 = x^2 y; d2y/ds dx = y + s*x*y.
            actions_2[(s_name, s_name)] = lambda Va, Vb, c=x * x * y * live: c * Va * Vb
            cross_s = (y + s * x * y) * live
            actions_2[(s_name, self._from)] = lambda Va, Vb, c=cross_s: c * Va * Vb
            actions_2[(self._from, s_name)] = lambda Va, Vb, c=cross_s: c * Va * Vb
        if nlp_A is not None and nlp_s is not None:
            # d2y/dA ds = x*exp(z).
            A_name, s_name = nlp_A.input_name, nlp_s.input_name
            cross_As = x * exp_z * live
            actions_2[(A_name, s_name)] = lambda Va, Vb, c=cross_As: c * Va * Vb
            actions_2[(s_name, A_name)] = lambda Va, Vb, c=cross_As: c * Va * Vb

        return y, *self.propagate_tangents(
            v, self._to, actions, output=y, v2=v2, actions_2=actions_2, vh=vh
        )


__all__ = ["ScalarExponential"]
