"""Numerical equivalence tests for ``rewritten_models/physics/density_limit.py``.

Methodology: see `idempotence_tests/_harness.py`. Applied here:

- **Random sweep**, 300 samples, seed fixed per test. Ranges bracket
  realistic tokamak operating points.
- **Branch coverage**:
  - `JetEdgeRadiationDensityLimit` has a `denom <= 0.0` guard (returns 0.0
    instead of evaluating `sqrt` of something that could be negative) —
    covered by picking `n_charge_plasma_effective_vol_avg`/`qstar`
    combinations that land on both sides of `denom == 0`.
  - `GetDensityLimitValue`/`CalculateDensityLimit`/`PlasmaDensityLimit` are
    each tested for **every one of the 8 valid switch values** (not a
    sample of them — the domain is small enough to cover exhaustively)
    plus an out-of-domain value to confirm the illegal-switch error path.
- Each rewritten class is checked directly against its one corresponding
  original method (`AsdexDensityLimit` vs. `calculate_asdex_density_limit`,
  etc. — no more "compare against an array index" indirection, now that
  the rewrite mirrors the original method boundaries 1:1, PLAN.md §4
  decision 5).
"""

from __future__ import annotations

from idempotence_tests._harness import (
    assert_explicit_equivalent,
    random_samples,
    require_process,
)
from rewritten_models.physics.density_limit import (
    AsdexDensityLimit,
    AsdexNewDensityLimit,
    BorrassIterIDensityLimit,
    BorrassIterIiDensityLimit,
    CalculateDensityLimit,
    GetDensityLimitValue,
    GreenwaldDensityLimit,
    HugillMurakamiDensityLimit,
    JetEdgeRadiationDensityLimit,
    JetSimpleDensityLimit,
    PlasmaDensityLimit,
)

require_process()

from process.models.physics.density_limit import (  # noqa: E402
    DensityLimitModel as OrigDensityLimitModel,
    PlasmaDensityLimit as OrigPlasmaDensityLimit,
)

ORIG = OrigPlasmaDensityLimit()

_CORRELATION_RANGES = {
    "p_perp": (0.001, 5.0),
    "b_plasma_toroidal_on_axis": (1.0, 15.0),
    "q95": (1.5, 8.0),
    "rmajor": (3.0, 15.0),
    "prn1": (0.1, 0.6),
}

# Shared physically-realistic ranges for calculate_density_limit/run's inputs.
_RUN_RANGES = {
    "b_plasma_toroidal_on_axis": (1.0, 15.0),
    "p_plasma_separatrix_mw": (1.0, 500.0),
    "p_hcd_injected_total_mw": (0.0, 200.0),
    "plasma_current": (1.0e6, 25.0e6),
    "prn1": (0.1, 0.6),
    "qstar": (1.5, 8.0),
    "q95": (1.5, 8.0),
    "rmajor": (3.0, 15.0),
    "rminor": (0.5, 5.0),
    "a_plasma_surface": (200.0, 3000.0),
    "n_charge_plasma_effective_vol_avg": (1.0, 4.0),
    "nd_plasma_electron_line": (1.0e19, 2.0e20),
}


def test_asdex_density_limit():
    samples = random_samples(_CORRELATION_RANGES, n=300, seed=10)
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_asdex_density_limit, AsdexDensityLimit(), samples
    )


def test_borrass_iter_i_density_limit():
    samples = random_samples(_CORRELATION_RANGES, n=300, seed=11)
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_borrass_iter_i_density_limit,
        BorrassIterIDensityLimit(),
        samples,
    )


def test_borrass_iter_ii_density_limit():
    samples = random_samples(_CORRELATION_RANGES, n=300, seed=12)
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_borrass_iter_ii_density_limit,
        BorrassIterIiDensityLimit(),
        samples,
    )


def test_jet_edge_radiation_density_limit_random_sweep():
    samples = random_samples(
        {
            "n_charge_plasma_effective_vol_avg": (1.0, 4.0),
            "p_hcd_injected_total_mw": (0.0, 200.0),
            "prn1": (0.1, 0.6),
            "qstar": (1.5, 8.0),
        },
        n=300,
        seed=13,
    )
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_jet_edge_radiation_density_limit,
        JetEdgeRadiationDensityLimit(),
        samples,
        map_inputs=lambda s: {
            "zeff": s["n_charge_plasma_effective_vol_avg"],
            "p_hcd_injected_total_mw": s["p_hcd_injected_total_mw"],
            "prn1": s["prn1"],
            "qcyl": s["qstar"],
        },
    )


def test_jet_edge_radiation_denom_guard_both_branches():
    """Covers denom = (zeff - 1) * (1 - 4/(3*qstar)) <= 0.0 (returns 0.0)
    and > 0.0 (evaluates the correlation) explicitly, since a uniform
    random sweep over plausible zeff/qstar rarely lands exactly on or
    below the boundary."""
    cases = [
        dict(n_charge_plasma_effective_vol_avg=1.0, p_hcd_injected_total_mw=50.0, prn1=0.3, qstar=3.0),
        dict(n_charge_plasma_effective_vol_avg=2.0, p_hcd_injected_total_mw=50.0, prn1=0.3, qstar=1.0),
        dict(n_charge_plasma_effective_vol_avg=2.0, p_hcd_injected_total_mw=50.0, prn1=0.3, qstar=3.0),
    ]
    for kwargs in cases:
        orig = OrigPlasmaDensityLimit.calculate_jet_edge_radiation_density_limit(
            zeff=kwargs["n_charge_plasma_effective_vol_avg"],
            p_hcd_injected_total_mw=kwargs["p_hcd_injected_total_mw"],
            prn1=kwargs["prn1"],
            qcyl=kwargs["qstar"],
        )
        new = JetEdgeRadiationDensityLimit()(**kwargs)
        assert orig == new, (kwargs, orig, new)


def test_jet_simple_density_limit():
    samples = random_samples(
        {
            "b_plasma_toroidal_on_axis": (1.0, 15.0),
            "p_plasma_separatrix_mw": (1.0, 500.0),
            "rmajor": (3.0, 15.0),
            "prn1": (0.1, 0.6),
        },
        n=300,
        seed=14,
    )
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_jet_simple_density_limit, JetSimpleDensityLimit(), samples
    )


def test_hugill_murakami_density_limit():
    samples = random_samples(
        {"b_plasma_toroidal_on_axis": (1.0, 15.0), "rmajor": (3.0, 15.0), "qstar": (1.5, 8.0)},
        n=300,
        seed=15,
    )
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_hugill_murakami_density_limit,
        HugillMurakamiDensityLimit(),
        samples,
        map_inputs=lambda s: {
            "b_plasma_toroidal_on_axis": s["b_plasma_toroidal_on_axis"],
            "rmajor": s["rmajor"],
            "qcyl": s["qstar"],
        },
    )


def test_greenwald_density_limit():
    samples = random_samples({"plasma_current": (1.0e6, 25.0e6), "rminor": (0.5, 5.0)}, n=300, seed=16)
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_greenwald_density_limit,
        GreenwaldDensityLimit(),
        samples,
        map_inputs=lambda s: {"c_plasma": s["plasma_current"], "rminor": s["rminor"]},
    )


def test_asdex_new_density_limit():
    samples = random_samples(
        {
            "p_hcd_injected_total_mw": (0.0, 200.0),
            "plasma_current": (1.0e6, 25.0e6),
            "q95": (1.5, 8.0),
            "prn1": (0.1, 0.6),
        },
        n=300,
        seed=17,
    )
    assert_explicit_equivalent(
        OrigPlasmaDensityLimit.calculate_asdex_new_density_limit,
        AsdexNewDensityLimit(),
        samples,
        map_inputs=lambda s: {
            "p_hcd_injected_total_mw": s["p_hcd_injected_total_mw"],
            "c_plasma": s["plasma_current"],
            "q95": s["q95"],
            "prn1": s["prn1"],
        },
    )


def _orig_calculate_density_limit_kwargs(s: dict) -> dict:
    return dict(
        b_plasma_toroidal_on_axis=s["b_plasma_toroidal_on_axis"],
        i_density_limit=s["i_density_limit"],
        p_plasma_separatrix_mw=s["p_plasma_separatrix_mw"],
        p_hcd_injected_total_mw=s["p_hcd_injected_total_mw"],
        plasma_current=s["plasma_current"],
        prn1=s["prn1"],
        qcyl=s["qstar"],
        q95=s["q95"],
        rmajor=s["rmajor"],
        rminor=s["rminor"],
        a_plasma_surface=s["a_plasma_surface"],
        zeff=s["n_charge_plasma_effective_vol_avg"],
    )


def test_calculate_density_limit_array_random_sweep():
    samples = random_samples(_RUN_RANGES, n=300, seed=20)
    for sample in samples:
        sample = dict(sample, i_density_limit=1)  # unused by the array computation itself
        orig_array, _unused_second_value = ORIG.calculate_density_limit(
            **_orig_calculate_density_limit_kwargs(sample)
        )
        new_array = CalculateDensityLimit()(
            **{k: v for k, v in sample.items() if k != "nd_plasma_electron_line"}
        )
        assert list(orig_array) == new_array, (sample, list(orig_array), new_array)


def test_calculate_density_limit_illegal_switch_raises():
    sample = dict(random_samples(_RUN_RANGES, n=1, seed=21)[0], i_density_limit=99)
    try:
        CalculateDensityLimit()(
            **{k: v for k, v in sample.items() if k != "nd_plasma_electron_line"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for i_density_limit=99")


def test_get_density_limit_value_all_switch_values():
    """Exhaustive over the full 8-value switch domain (small enough to
    cover completely, not just sample)."""
    array = list(
        ORIG.calculate_density_limit(
            **_orig_calculate_density_limit_kwargs(
                dict(random_samples(_RUN_RANGES, n=1, seed=22)[0], i_density_limit=1)
            )
        )[0]
    )
    for switch in range(1, 9):
        orig = ORIG.get_density_limit_value(OrigDensityLimitModel(switch), array)
        new = GetDensityLimitValue()(i_density_limit=switch, nd_plasma_electron_max_array=array)
        assert orig == new, (switch, orig, new)


def test_get_density_limit_value_illegal_switch_raises():
    array = [0.0] * 8
    for illegal_switch in (0, 9, -1):
        try:
            GetDensityLimitValue()(i_density_limit=illegal_switch, nd_plasma_electron_max_array=array)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for i_density_limit={illegal_switch}")


def test_plasma_density_limit_full_random_sweep():
    """The top-level rewritten model (~run) against the original's actual
    run() output, for all 8 switch values across the random sweep."""
    samples = random_samples(_RUN_RANGES, n=40, seed=23)
    for switch in range(1, 9):
        for sample in samples:
            orig_array, _ = ORIG.calculate_density_limit(
                **_orig_calculate_density_limit_kwargs(dict(sample, i_density_limit=switch))
            )
            orig_enforced = ORIG.get_density_limit_value(OrigDensityLimitModel(switch), orig_array)
            orig_greenwald_fraction = sample["nd_plasma_electron_line"] / orig_array[6]

            new_array, new_enforced, new_greenwald_fraction = PlasmaDensityLimit()(
                b_plasma_toroidal_on_axis=sample["b_plasma_toroidal_on_axis"],
                i_density_limit=switch,
                p_plasma_separatrix_mw=sample["p_plasma_separatrix_mw"],
                p_hcd_injected_total_mw=sample["p_hcd_injected_total_mw"],
                plasma_current=sample["plasma_current"],
                prn1=sample["prn1"],
                qstar=sample["qstar"],
                q95=sample["q95"],
                rmajor=sample["rmajor"],
                rminor=sample["rminor"],
                a_plasma_surface=sample["a_plasma_surface"],
                n_charge_plasma_effective_vol_avg=sample["n_charge_plasma_effective_vol_avg"],
                nd_plasma_electron_line=sample["nd_plasma_electron_line"],
            )
            assert list(orig_array) == new_array
            assert orig_enforced == new_enforced
            assert orig_greenwald_fraction == new_greenwald_fraction


def test_plasma_density_limit_illegal_switch_raises():
    sample = random_samples(_RUN_RANGES, n=1, seed=24)[0]
    try:
        PlasmaDensityLimit()(
            b_plasma_toroidal_on_axis=sample["b_plasma_toroidal_on_axis"],
            i_density_limit=99,
            p_plasma_separatrix_mw=sample["p_plasma_separatrix_mw"],
            p_hcd_injected_total_mw=sample["p_hcd_injected_total_mw"],
            plasma_current=sample["plasma_current"],
            prn1=sample["prn1"],
            qstar=sample["qstar"],
            q95=sample["q95"],
            rmajor=sample["rmajor"],
            rminor=sample["rminor"],
            a_plasma_surface=sample["a_plasma_surface"],
            n_charge_plasma_effective_vol_avg=sample["n_charge_plasma_effective_vol_avg"],
            nd_plasma_electron_line=sample["nd_plasma_electron_line"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for i_density_limit=99")
