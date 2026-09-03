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

__all__ = ["unsupplied"]


def unsupplied(kwargs: dict[str, object], names: list[str]) -> list[str]:
    """Return the subset of ``names`` the user did not supply in the input file.

    A HIT option may arrive as a plain number, or as a string naming a
    ``[Tensors]`` entry (or an already-resolved typed object). Only the numeric
    form can be inspected here -- ``__init__`` runs before HIT resolution -- and
    a reference is by definition supplied, so anything non-numeric passes.
    """
    missing = []
    for name in names:
        value = kwargs.get(name)
        if value is None:
            missing.append(name)
            continue
        if isinstance(value, str):
            # a [Tensors] reference: supplied by definition
            continue
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            # an already-typed object: supplied by definition
            continue
        if math.isnan(number):
            missing.append(name)
    return missing
