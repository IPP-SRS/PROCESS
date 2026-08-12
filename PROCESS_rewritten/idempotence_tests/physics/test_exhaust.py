"""Numerical equivalence tests for ``rewritten_models/physics/exhaust.py``.

Methodology: see `idempotence_tests/_harness.py` module docstring for the
general approach (random sweep + explicit branch coverage, exact equality).
Applied here:

- **Random sweep**, 300 samples per class, seed 0. Ranges are chosen to
  bracket realistic tokamak operating points by roughly 2x on either side
  of a typical value (e.g. Psep ~ 50-500 MW, not 1e-30 to 1e30) — wide
  enough to actually stress the arithmetic, not so wide the physics
  correlations are meaningless.
- **Branch coverage**: `RadiationFraction` has exactly one branch — the
  `p_plasma_heating_total_mw == 0` guard — covered explicitly below, since
  a random float sweep will essentially never draw exactly 0.0.
"""

from __future__ import annotations

from idempotence_tests._harness import (
    assert_explicit_equivalent,
    random_samples,
    require_process,
)
from rewritten_models.physics.exhaust import (
    EuDemoReattachmentMetric,
    PlasmaSeparatrixPower,
    PsepOverRMetric,
    RadiationFraction,
)

require_process()

from process.models.physics.exhaust import PlasmaExhaust  # noqa: E402


def test_plasma_separatrix_power():
    samples = random_samples(
        {
            "f_p_alpha_plasma_deposited": (0.5, 1.0),
            "p_alpha_total_mw": (10.0, 800.0),
            "p_non_alpha_charged_mw": (0.0, 100.0),
            "p_hcd_injected_total_mw": (0.0, 200.0),
            "p_plasma_ohmic_mw": (0.0, 5.0),
            "p_plasma_rad_mw": (0.0, 400.0),
        },
        n=300,
        seed=0,
    )
    assert_explicit_equivalent(
        PlasmaExhaust.calculate_separatrix_power, PlasmaSeparatrixPower(), samples
    )


def test_psep_over_r_metric():
    samples = random_samples(
        {"p_plasma_separatrix_mw": (1.0, 500.0), "rmajor": (3.0, 15.0)},
        n=300,
        seed=1,
    )
    assert_explicit_equivalent(
        PlasmaExhaust.calculate_psep_over_r_metric, PsepOverRMetric(), samples
    )


def test_eu_demo_reattachment_metric():
    samples = random_samples(
        {
            "p_plasma_separatrix_mw": (1.0, 500.0),
            "b_plasma_toroidal_on_axis": (1.0, 15.0),
            "q95": (1.5, 8.0),
            "aspect": (1.5, 5.0),
            "rmajor": (3.0, 15.0),
        },
        n=300,
        seed=2,
    )
    assert_explicit_equivalent(
        PlasmaExhaust.calculate_eu_demo_re_attachment_metric,
        EuDemoReattachmentMetric(),
        samples,
    )


def test_radiation_fraction_random_sweep():
    samples = random_samples(
        {"p_plasma_rad_mw": (0.0, 400.0), "p_plasma_heating_total_mw": (1.0, 900.0)},
        n=300,
        seed=3,
    )
    assert_explicit_equivalent(
        PlasmaExhaust.calculate_radiation_fraction,
        RadiationFraction(),
        samples,
        # original's parameter is p_plasma_heating_mw; rewritten's is
        # p_plasma_heating_total_mw (PLAN.md §9 rename) — map back for the
        # original-side call.
        map_inputs=lambda s: {
            "p_plasma_rad_mw": s["p_plasma_rad_mw"],
            "p_plasma_heating_mw": s["p_plasma_heating_total_mw"],
        },
    )


def test_radiation_fraction_zero_heating_power_branch():
    """Covers the p_plasma_heating_total_mw == 0 guard (returns 0.0, not
    ZeroDivisionError) — a random sweep won't hit this on its own."""
    samples = [{"p_plasma_rad_mw": v, "p_plasma_heating_total_mw": 0.0} for v in (0.0, 1.0, 250.0)]
    assert_explicit_equivalent(
        PlasmaExhaust.calculate_radiation_fraction,
        RadiationFraction(),
        samples,
        map_inputs=lambda s: {
            "p_plasma_rad_mw": s["p_plasma_rad_mw"],
            "p_plasma_heating_mw": s["p_plasma_heating_total_mw"],
        },
    )
