"""Minimal scaffolding for the functional rewrite experiment.

This module defines the ``Output`` marker and the ``ExplicitFunction`` /
``ImplicitFunction`` base classes used by every model under ``rewritten_models``.
No such framework exists elsewhere in this codebase or in the user's sibling
projects (checked: PROCESS_code_analysis, ESL-MBSE-MDAO, ESL_utils,
DESC-openMDAO) — it was designed from scratch for this experiment, closely
following the two examples given in the task brief. Treat it as part of what
the ``exhaust.py`` test is meant to validate, not as settled prior art.

Design intent
--------------
- ``Output()`` is a *declaration*, not a value holder. It exists so a model's
  class body documents, at a glance, which global-namespace variables it
  produces, in the same spirit as a dataclass field. It carries no state and
  performs no computation.
- ``ExplicitFunction`` subclasses are pure: ``__call__(self, *inputs) ->
  <one value per Output, in declaration order>``. The output count on return
  must equal the number of declared ``Output()`` attributes: a single value
  for one output, a tuple for more than one.
- ``ImplicitFunction`` subclasses model a residual ``R(u; other inputs) = 0``.
  The declared ``Output()`` names double as the unknowns being solved for;
  ``residual(self, u, ...)`` returns the residual value(s) that should vanish
  at the solution, matching the declared outputs 1:1. This experiment does
  not include a solver — ``ImplicitFunction`` only fixes the *interface*
  shape (what residual, in terms of what unknowns and inputs); wiring an
  actual root-finder around it is composition-layer work, out of scope here.
- Neither base class touches ``process.data_structure`` or any central data
  object. All inputs/outputs are plain function parameters and return
  values, named after the shared namespace catalogued in ``_namespace.py``.
"""

from __future__ import annotations

import abc
from typing import Any


class Output:
    """Marks a class attribute as a declared output of a model.

    Purely declarative: carries no value and does no work. ``__set_name__``
    records the attribute name so tooling (and humans) can introspect a
    model's declared outputs via ``ExplicitFunction.output_names`` /
    ``ImplicitFunction.output_names`` without re-parsing the call signature.
    """

    name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"Output({self.name!r})"


class _DeclaresOutputs:
    """Shared introspection helper for the two function kinds."""

    @classmethod
    def output_names(cls) -> tuple[str, ...]:
        """Names of this model's declared outputs, in class-body order."""
        return tuple(
            name
            for name, value in vars(cls).items()
            if isinstance(value, Output)
        )


class ExplicitFunction(_DeclaresOutputs, abc.ABC):
    """Base class for explicit models: ``outputs = f(inputs)``.

    Subclasses declare one ``Output()`` class attribute per output and
    implement ``__call__`` with one plain parameter per input, named after
    the shared global namespace. Return a single value if there is one
    declared output, or a tuple of values (in declaration order) if there
    are several.
    """

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> Any:
        """Compute and return this model's declared output(s)."""


class ImplicitFunction(_DeclaresOutputs, abc.ABC):
    """Base class for implicit models: unknowns ``u`` s.t. ``R(u, ...) = 0``.

    Subclasses declare one ``Output()`` per unknown being solved for and
    implement ``residual`` with the unknown(s) as leading parameter(s) and
    the remaining data as plain keyword/positional parameters, named after
    the shared global namespace. Never name a parameter or local starting
    with ``r_`` — reserved to avoid confusion with the residual return
    value(s).
    """

    @abc.abstractmethod
    def residual(self, *args, **kwargs) -> Any:
        """Return the residual(s), zero at the solution.

        See ``ExplicitFunction.__call__`` for why this is ``Any``, not
        ``None``.
        """
