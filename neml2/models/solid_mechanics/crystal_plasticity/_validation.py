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
