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


"""Quadratic polynomial model $y = a x^2 + b x + c$."""

from __future__ import annotations

from ...factory import register_neml2_object
from ...schema import BLOCK_NAME, HitSchema, input, output, parameter
from ...types import Scalar
from ..chain_rule import ChainRuleDict, SecondOrderChainRuleDict
from ..model import Model


@register_neml2_object("ScalarQuadraticInterpolation")
class ScalarQuadraticInterpolation(Model):
    r"""Quadratic function of the argument, $y = a x^2 + b x + c$."""

    # Smooth in x: dy/dx = 2 a x + b, d2y/dx2 = 2 a.
    SUPPORTS_SECOND_ORDER = True

    hit = HitSchema(
        input("argument", Scalar, "Argument for quadratic interpolation", attr="_argument"),
        output(
            "output",
            Scalar,
            "Output from quadratic interpolation",
            default=BLOCK_NAME,
            attr="_output",
        ),
        parameter("a", Scalar, "Constant multiplied to quadratic argument"),
        parameter("b", Scalar, "Constant multiplied to linear argument"),
        parameter("c", Scalar, "Constant added to output"),
    )

    _argument: str
    _output: str
    a: Scalar
    b: Scalar
    c: Scalar

    def forward(  # type: ignore[override]
        self,
        *inputs: Scalar,
        v: ChainRuleDict | None = None,
        v2: SecondOrderChainRuleDict | None = None,
        vh: ChainRuleDict | None = None,
    ):
        if len(inputs) != 1:
            raise ValueError(f"ScalarQuadraticInterpolation expected 1 input, got {len(inputs)}")
        x_arg = inputs[0]

        a = self._get_param("a", inputs[1:], Scalar)
        b = self._get_param("b", inputs[1:], Scalar)
        c = self._get_param("c", inputs[1:], Scalar)

        out = a * x_arg * x_arg + b * x_arg + c
        if v is None:
            return out

        # First-order pushforward: dy/dx = 2 a x + b.
        def argument_action(V: Scalar) -> Scalar:
            return (2.0 * a * x_arg + b) * V

        actions_1 = {self._argument: argument_action}

        if v2 is None and vh is None:
            return out, self.apply_chain_rule(v, self._output, actions_1, output=out)

        # Second-order pushforward: d2y/dx2 = 2 a, contracted with both seeds.
        def argument_argument_action(Va: Scalar, Vb: Scalar) -> Scalar:
            return 2.0 * a * Va * Vb

        actions_2 = {(self._argument, self._argument): argument_argument_action}

        return out, *self.propagate_tangents(
            v, self._output, actions_1, output=out, v2=v2, actions_2=actions_2, vh=vh
        )


__all__ = ["ScalarQuadraticInterpolation"]
