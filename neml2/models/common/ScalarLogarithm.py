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

"""Generic scalar natural-logarithm map with a floor guard."""

from __future__ import annotations

from ...factory import register_neml2_object
from ...schema import HitSchema, input, option, output
from ...types import Scalar, clamp, heaviside, log
from ..chain_rule import ChainRuleAction, ChainRuleDict
from ..model import Model


@register_neml2_object("ScalarLogarithm")
class ScalarLogarithm(Model):
    r"""Natural-logarithm map between two Scalar variables,

    $$
    y = \ln\!\big(\max(x, x_{\min})\big)
    $$

    ``floor`` ($x_{\min}$) guards ``log`` -- and its derivative -- against a
    non-positive or vanishingly small ``x``. Where the floor binds, $y$ no
    longer depends on $x$, so the derivative is zeroed there via a heaviside
    gate: the same clamp-derivative convention used by ``MeanFreePath``'s
    ``rho_min`` and ``ScalarExponential``'s ``exponent_max``.

    The principal use is pairing with :class:`~neml2.models.common.ScalarExponential`
    to write a residual entirely in log-space -- e.g. comparing a
    reparameterized Newton unknown ``log_x`` against ``log(clamp(x_target,
    floor))`` -- so the residual has a genuine, well-conditioned finite root
    even when the physical target sits at or below the floor. An
    ``exp``-only reparameterization has no such root there: it can only
    approach the floor asymptotically as the unknown marches to
    $-\infty$.
    """

    hit = HitSchema(
        input("from", Scalar, "Scalar variable to take the logarithm of", attr="_from"),
        output("to", Scalar, "The natural logarithm of the (floored) input", attr="_to"),
        option(
            "floor",
            float,
            "Lower floor applied to the input before taking the logarithm. Guards "
            "log() against a non-positive or vanishingly small argument. Match "
            "this to any floor already applied to the same physical quantity "
            "elsewhere in the model (e.g. a paired reciprocal-division guard) so "
            "both stay numerically consistent.",
            default=1e-30,
            attr="floor",
        ),
    )

    _from: str
    _to: str
    floor: float

    def forward(
        self,
        *args: Scalar,
        v: ChainRuleDict | None = None,
        **_: object,
    ) -> Scalar | tuple[Scalar, ChainRuleDict]:
        x = args[0]
        x_eff = clamp(x, self.floor)
        y = log(x_eff)

        if v is None:
            return y

        # live == 0 where the floor binds -- y is locally constant in x there.
        live = heaviside(x - self.floor)
        dy_dx = live / x_eff
        actions: dict[str, ChainRuleAction] = {self._from: lambda V, c=dy_dx: c * V}

        return y, self.apply_chain_rule(v, self._to, actions, output=y)


__all__ = ["ScalarLogarithm"]
