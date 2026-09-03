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
from neml2.schema import HitSchema, buffer, input, output
from neml2.types import Scalar


@register_neml2_object("OrowanPlasticShearRate")
class OrowanPlasticShearRate(Model):
    hit = HitSchema(
        input("rho_m", Scalar, "Mobile dislocation density", attr="_rho_m_name"),
        input("v_disl", Scalar, "BCC screw dislocation velocity", attr="_v_disl_name"),
        output("gamma_dot", Scalar, "Plastic shear flow rate"),
        buffer("b", Scalar, "Burger's vector magnitude"),
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
        inputs = args[:n_in]
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
