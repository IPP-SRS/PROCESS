"""Isolated global-namespace registry for the functional rewrite experiment.

``rewritten_models`` must stay completely isolated from PROCESS — it never
imports ``process.data_structure`` and never touches a central data object.
But its whole point is point-to-point data flow using *the same variable
names* PROCESS already uses, so some registry has to say, outside of
PROCESS's own dataclasses, "this name means this physical quantity, and this
model is the one that produces it." That is what this module is: a
hand-maintained mirror/extension of the ``process/data_structure`` namespace,
not a runtime dependency of any model (models never import this module
except to self-register, and no ``ExplicitFunction``/``ImplicitFunction``
reads from it to get a value).

Two things it buys us, cheaply:

1. A single place to look up "does this name already mean something, and
   what, before I use it for a new model" — the answer to "reuse existing
   data_structure namespace as much as possible" when dozens of models are
   being rewritten in parallel by different agents that can't see each
   other's work in progress.
2. An automatic clash check: every rewritten model calls :func:`declare` at
   import time for each of its outputs (and any input it originates rather
   than merely consumes). Importing two models that declare the same name
   with a different meaning raises immediately instead of silently
   colliding.

This is deliberately lightweight — a name/description/unit/origin ledger,
not a type system. It does not validate units dimensionally, does not know
about the ``ImplicitModel`` naming rule (no ``r_`` prefix), and is not meant
to survive contact with a "real" namespace-management tool if this
experiment grows past its current scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Origin = Literal["existing", "new"]


@dataclass(frozen=True)
class NamespaceEntry:
    """One entry in the shared functional-rewrite namespace.

    Attributes
    ----------
    name:
        The flat global variable name, exactly as it appears in model
        signatures (e.g. ``"p_plasma_separatrix_mw"``).
    description:
        Short human-readable meaning, used both for documentation and to
        detect same-name-different-meaning clashes.
    unit:
        Physical unit, or ``""`` for dimensionless/non-physical values
        (switches, counts, booleans).
    origin:
        ``"existing"`` if this name already exists as an attribute on one of
        the ``*Data`` dataclasses in ``process/data_structure`` (PROCESS's
        own central data structure) — the common case, since instructions
        are to reuse that namespace wherever possible. ``"new"`` if this
        experiment is introducing the name because no PROCESS-side attribute
        currently carries this exact quantity as a distinct value (e.g. a
        quantity that PROCESS only ever computes as an unnamed local/inline
        expression).
    source:
        For ``origin="existing"``, the ``module.ClassName.attribute`` this
        mirrors in ``process/data_structure`` (informational only — this
        registry does not import or check against it). ``None`` for
        ``origin="new"``.
    defining_model:
        Name of the rewritten model (its ``ExplicitFunction``/
        ``ImplicitFunction`` class name) that produces this name as an
        ``Output()``. ``None`` for names that are only ever consumed as
        inputs within this experiment so far.
    notes:
        Free text — e.g. why a name was renamed from what PROCESS calls the
        same call-site parameter, or why a new name was introduced.
    """

    name: str
    description: str
    unit: str
    origin: Origin
    source: str | None
    defining_model: str | None
    notes: str = ""


NAMESPACE: dict[str, NamespaceEntry] = {}


def declare(
    name: str,
    *,
    description: str,
    unit: str = "",
    origin: Origin,
    defining_model: str | None = None,
    source: str | None = None,
    notes: str = "",
) -> str:
    """Register *name* in the shared namespace, or validate a re-declaration.

    Returns *name* unchanged (so this can be called inline while building an
    ``Output()`` line or a signature default, if convenient). Raises
    ``ValueError`` if *name* is already registered with a different
    ``description`` — the signal that this name means something different
    here than where it was first declared, and must instead be suffixed
    with the owning model's name (e.g. ``p_loss_mw_myModel``) per the
    clash-avoidance rule in the rewrite instructions.

    Re-declaring the same name with the same description (e.g. a second
    model that also *consumes* an existing output as an input) is a no-op,
    not a clash — the shared namespace is exactly meant to be read by many
    models.
    """
    existing = NAMESPACE.get(name)
    if existing is None:
        NAMESPACE[name] = NamespaceEntry(
            name=name,
            description=description,
            unit=unit,
            origin=origin,
            source=source,
            defining_model=defining_model,
            notes=notes,
        )
        return name

    if existing.description != description:
        raise ValueError(
            f"Namespace clash on {name!r}: already declared as "
            f"{existing.description!r} (by {existing.defining_model or 'unknown'}), "
            f"now redeclared as {description!r}. Suffix the new name with the "
            f"owning model's class name instead of reusing {name!r}."
        )

    if existing.defining_model is None and defining_model is not None:
        # An input-only mention is now confirmed as the producing model.
        NAMESPACE[name] = NamespaceEntry(
            name=name,
            description=description,
            unit=unit or existing.unit,
            origin=existing.origin,
            source=existing.source or source,
            defining_model=defining_model,
            notes=existing.notes or notes,
        )

    return name
