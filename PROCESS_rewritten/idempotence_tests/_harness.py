"""Shared methodology for numerically verifying a rewritten model.

These are equivalence tests, not idempotence tests in the strict sense (the
folder name follows the terminology you asked for) — each one checks that a
rewritten ``ExplicitFunction``/``ImplicitFunction`` produces *exactly* the
same numbers as the original PROCESS class/function it replaces. "Full
confidence" here means: don't just spot-check a few values by hand (that's
what stage 1 did the first time, before this harness existed, and it's not
enough to catch a translation error that only shows up for some inputs).
Every rewritten model's test must instead combine two things:

1. **A wide, reproducible random sweep.** For every input, draw ``n``
   samples (default 300) uniformly from a range covering the quantity's
   realistic physical span — wide enough to be a real stress test, not so
   wide it only ever hits domain errors. Every sample is fed to *both* the
   original and the rewritten callable and the two outputs are compared.
   The seed is fixed (pass one explicitly; don't rely on the default) so a
   failure is reproducible, not a flake.

   Comparison is **exact equality**, not `np.isclose`. These rewrites are
   meant to be line-for-line translations of the original arithmetic — if
   the two disagree by even 1 ULP, that's a real translation bug (a
   reordered operation, `np.sqrt` silently swapped for `math.sqrt`, a
   dropped term), not acceptable floating-point noise. Every rewrite in
   stage 1 achieved exact equality across its whole sweep; treat anything
   less as a finding to investigate, not a tolerance to raise.

2. **Explicit branch/edge-case coverage.** A random sweep only proves
   equivalence *on the inputs it happened to draw* — it will not reliably
   hit an `if` branch that's only taken on a knife-edge condition (a
   `denom <= 0` guard, a switch value at the boundary of its domain, an
   illegal input that should raise). Read the original source, list every
   branch by hand, and add one hand-picked case landing in each — including
   the ones the random sweep is unlikely to ever hit on its own. A test
   file's docstring should say, concretely, which branches its edge cases
   cover, not just "edge cases tested."

Every idempotence test needs the real `process` package, so it only runs
under the `PROCESS_env` conda environment your other PROCESS work uses
(`conda run -n PROCESS_env python -m pytest PROCESS_rewritten/idempotence_tests/`).
Running under a plain interpreter skips with a clear reason instead of an
opaque `ModuleNotFoundError` — see `require_process()` below.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Iterable, Mapping

import numpy as np
import pytest


def require_process() -> None:
    """Skip the calling test with a clear reason if `process` isn't importable.

    Call this first in any test module that imports from `process.models...`
    — without it, running this suite outside `PROCESS_env` fails with a
    confusing `ModuleNotFoundError` deep in an import instead of a skip that
    says why.
    """
    if importlib.util.find_spec("process") is None:
        pytest.skip(
            "requires the real `process` package — run under "
            "`conda run -n PROCESS_env python -m pytest ...`"
        )


def random_samples(
    ranges: Mapping[str, tuple[float, float]], n: int, seed: int
) -> list[dict[str, float]]:
    """``n`` reproducible uniform-random samples over ``ranges``.

    ``ranges`` maps each input name to an inclusive ``(low, high)`` span
    covering its realistic physical range — document the physical
    reasoning for each range at the call site (a plausible major radius,
    a plausible switch domain, etc.), not just the numbers.

    Returns a list of ``n`` dicts, each a full kwargs set for one call to
    both the original and the rewritten callable. Same ``seed`` -> same
    samples, always — that's the whole point of fixing it explicitly.
    """
    rng = np.random.default_rng(seed)
    names = list(ranges)
    lows = np.array([ranges[name][0] for name in names])
    highs = np.array([ranges[name][1] for name in names])
    draws = rng.uniform(lows, highs, size=(n, len(names)))
    return [dict(zip(names, row, strict=True)) for row in draws]


def assert_explicit_equivalent(
    original: Callable[..., object],
    rewritten: Callable[..., object],
    samples: Iterable[Mapping[str, float]],
    *,
    map_inputs: Callable[[dict], dict] | None = None,
    unwrap_original: Callable[[object], object] | None = None,
) -> None:
    """Assert ``original(**s) == rewritten(**s)`` for every sample ``s``.

    Collects *every* mismatching sample before failing, rather than
    stopping at the first one — a translation bug that only shows up for
    some inputs is exactly what this is meant to catch, and seeing all the
    failing cases at once (not just one) is what makes the failure
    actionable.

    Parameters
    ----------
    original, rewritten :
        The two callables under comparison — typically a `staticmethod`
        from the original PROCESS class and an instance of the rewritten
        ``ExplicitFunction``. Both are called as ``fn(**sample)``.
    samples :
        Kwargs dicts, e.g. from `random_samples` plus hand-picked edge
        cases appended on.
    map_inputs :
        If the original and rewritten callables don't share parameter
        names (a renamed parameter, see PLAN.md §6 naming rule 1), a
        function ``sample -> kwargs`` producing the *original*'s kwargs
        from the same sample dict used for the rewritten call. Leave unset
        when both share the same names.
    unwrap_original :
        If the original returns something the rewritten output must be
        compared against only in part (e.g. the original returns a 4-tuple
        but this rewritten class only covers one element of it), a
        function extracting the comparable piece from the original's
        return value.
    """
    failures = []
    n_checked = 0
    for sample in samples:
        n_checked += 1
        original_kwargs = map_inputs(sample) if map_inputs else sample
        original_out = original(**original_kwargs)
        if unwrap_original is not None:
            original_out = unwrap_original(original_out)
        rewritten_out = rewritten(**sample)
        if original_out != rewritten_out:
            failures.append((sample, original_out, rewritten_out))

    if failures:
        lines = [f"{len(failures)}/{n_checked} samples mismatched:"]
        for sample, orig, new in failures[:10]:
            lines.append(f"  input={sample!r}\n    original={orig!r}\n    rewritten={new!r}")
        if len(failures) > 10:
            lines.append(f"  ... and {len(failures) - 10} more")
        raise AssertionError("\n".join(lines))


def assert_residual_matches_explicit(
    residual: Callable[..., float],
    reference: Callable[..., float],
    samples: Iterable[Mapping[str, float]],
) -> None:
    """Assert an ``ImplicitFunction.residual`` matches a reference formula
    at arbitrary (not necessarily root) points.

    Solving both the original and the rewritten residual with the same
    solver and comparing the converged root (see
    `assert_roots_match_via_solver`) only proves the two *agree at the
    root* — two different residual formulas can still converge to the same
    root while disagreeing everywhere else, especially if the solver is
    forgiving. This checks the residual formula itself, pointwise, against
    an independently-written reference expression (not the solver-found
    root), so a wrong residual can't hide behind a lucky convergence.
    """
    assert_explicit_equivalent(reference, residual, samples)


def assert_roots_match_via_solver(
    solve_original: Callable[..., float],
    residual: Callable[..., float],
    unknown_name: str,
    samples: Iterable[Mapping[str, float]],
    *,
    x0: float,
    x1: float,
    tol: float = 1e-6,
    atol: float = 1e-6,
) -> None:
    """Assert the original's own solve and the rewritten residual (solved
    with the same ``scipy.optimize.newton`` call) converge to the same root.

    This is the composition-level check: it doesn't just confirm the
    residual formula is right (see `assert_residual_matches_explicit`), it
    confirms that wiring an actual solver around the rewritten residual —
    the thing a future composition layer will do — reproduces the
    original's answer, not just an equally-valid alternate root.

    Parameters
    ----------
    unknown_name :
        The residual's parameter name for the unknown being solved for
        (e.g. ``"temp_current_sharing_rebco"``) — bound explicitly here
        rather than guessed, since it differs per model.
    x0, x1 :
        The two starting points ``scipy.optimize.newton`` (secant method)
        needs — use the same ones the original passes internally.
    """
    from scipy import optimize

    failures = []
    n_checked = 0
    for sample in samples:
        n_checked += 1
        original_root = solve_original(**sample)

        def wrapped(u, _sample=sample):
            return residual(**{**_sample, unknown_name: u})

        new_root, _ = optimize.newton(
            wrapped, x0, x1=x1, tol=tol, rtol=tol, maxiter=50, full_output=True, disp=True
        )
        if abs(original_root - new_root) > atol:
            failures.append((sample, original_root, new_root))

    if failures:
        lines = [f"{len(failures)}/{n_checked} root mismatches:"]
        for sample, orig, new in failures[:10]:
            lines.append(f"  input={sample!r} original_root={orig!r} rewritten_root={new!r}")
        raise AssertionError("\n".join(lines))
