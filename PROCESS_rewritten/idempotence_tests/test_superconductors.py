"""Numerical equivalence tests for ``rewritten_models/superconductors.py``.

Methodology: see `idempotence_tests/_harness.py`. Applied here:

- **Random sweep**, 300 samples, seed fixed per test, over
  `JcritRebco`'s validity range (4.2-72 K, 0-15 T) plus a margin outside it
  so the out-of-range logging path is exercised by the sweep too, not just
  by a hand-picked case.
- **Branch coverage** (`jcrit_rebco` has three independent conditionals):
  `temp_conductor < temp_c0max_rebco` vs. not; `b_conductor < birr` (normal)
  vs. not (field-too-high); and the validity-range check. Each has an
  explicit hand-picked case landing on both sides.
- **Two-layer check for the `ImplicitFunction`** (`CurrentSharingTemperatureRebco`),
  per the harness's rationale for why one check alone isn't enough:
  1. `assert_residual_matches_explicit` — the residual formula itself,
     `jcrit_rebco(u, b_conductor) - j_conductor`, checked pointwise against
     an independent reference expression at random (non-root) points. This
     catches a wrong residual even if it happens to still converge near the
     right answer.
  2. `assert_roots_match_via_solver` — the residual actually solved with
     the same `scipy.optimize.newton` call the original wraps internally,
     confirming the *converged root* matches the original's
     `current_sharing_rebco` output, not just the formula.
"""

from __future__ import annotations

from idempotence_tests._harness import (
    assert_explicit_equivalent,
    assert_residual_matches_explicit,
    assert_roots_match_via_solver,
    random_samples,
    require_process,
)
from rewritten_models.superconductors import CurrentSharingTemperatureRebco, JcritRebco

require_process()

from process.models import superconductors as orig  # noqa: E402

# Validity range per jcrit_rebco's docstring, plus ~20% margin on both
# sides so the sweep also exercises the out-of-range logging path, not
# just the interior.
_JCRIT_RANGES = {"temp_conductor": (0.0, 85.0), "b_conductor": (0.0, 18.0)}


def test_jcrit_rebco_random_sweep():
    samples = random_samples(_JCRIT_RANGES, n=300, seed=40)
    assert_explicit_equivalent(orig.jcrit_rebco, JcritRebco(), samples)


def test_jcrit_rebco_branch_coverage():
    """Hand-picked cases for jcrit_rebco's three conditionals, each on
    both sides: temp_conductor vs temp_c0max_rebco (90 K); b_conductor vs
    birr (field-dependent, not a fixed constant — picked empirically
    below); and the 4.2-72K / field validity range."""
    cases = [
        dict(temp_conductor=20.0, b_conductor=5.0),  # normal, in range
        dict(temp_conductor=95.0, b_conductor=5.0),  # temp > temp_c0max_rebco (90K)
        dict(temp_conductor=85.0, b_conductor=20.0),  # b_conductor > birr (field too high)
        dict(temp_conductor=2.0, b_conductor=5.0),  # below validity range (temp < 4.2K)
        dict(temp_conductor=68.0, b_conductor=13.0),  # above 65K threshold, still valid
    ]
    for kwargs in cases:
        orig_out = orig.jcrit_rebco(**kwargs)
        new_out = JcritRebco()(**kwargs)
        assert orig_out == new_out, (kwargs, orig_out, new_out)


def _reference_residual(temp_current_sharing_rebco: float, b_conductor: float, j_conductor: float) -> float:
    """Independent reference expression for the residual, written directly
    from jcrit_rebco's definition rather than by calling the rewritten
    JcritRebco — so this check can't pass merely because both sides call
    the same (possibly wrong) function."""
    j_crit_rebco, _valid, _b_c20max, _temp_c0max = orig.jcrit_rebco(
        temp_current_sharing_rebco, b_conductor
    )
    return j_crit_rebco - j_conductor


def test_current_sharing_residual_matches_reference_pointwise():
    samples = random_samples(
        {
            "temp_current_sharing_rebco": (4.2, 72.0),
            "b_conductor": (0.0, 15.0),
            "j_conductor": (1.0e6, 5.0e8),
        },
        n=300,
        seed=50,
    )
    assert_residual_matches_explicit(
        CurrentSharingTemperatureRebco().residual, _reference_residual, samples
    )


def test_current_sharing_root_matches_original_solve():
    samples = random_samples(
        {"b_conductor": (0.5, 14.0), "j_conductor": (1.0e7, 3.0e8)}, n=50, seed=60
    )

    def solve_original(b_conductor, j_conductor):
        return orig.current_sharing_rebco(b_conductor, j_conductor)

    assert_roots_match_via_solver(
        solve_original,
        CurrentSharingTemperatureRebco().residual,
        "temp_current_sharing_rebco",
        samples,
        x0=10.0,
        x1=20.0,
    )
