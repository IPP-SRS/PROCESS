"""Numerical equivalence tests for the stellarator geometry-scaling slice
of ``rewritten_models/stellarator/stellarator.py``.

Methodology: see `idempotence_tests/_harness.py`. Applied here with one
addition the earlier test files didn't need: the originals under test
(`st_new_config`, `st_geom`, `st_strc`) are instance methods reading/writing
`self.data.*` groups, not plain functions — so `_make_stellarator()` below
builds a bare `Stellarator` instance (via `__new__`, bypassing `__init__`,
which needs 12 other injected models none of these three methods touch)
with a fresh `process.core.model.DataStructure()` attached, exactly the
inputs each method needs set, nothing else.

- **Random sweep**, 300 samples, seed fixed per test. Ranges bracket
  plausible stellarator-scale geometry (rmajor ~3-30 m — stellarators run
  larger than tokamaks, e.g. Helias 5-B ~22 m).
- `st_new_config`'s own file-I/O call (`load_stellarator_config`) is
  monkeypatched to a no-op — it belongs to a different, not-yet-rewritten
  dependency-analysis node (PLAN.md module docstring for this file), and
  this test is only checking the geometry-scaling arithmetic *after* config
  loading, exactly matching what the rewrite itself assumes as input.
- **Branch coverage**: `StNewConfig`'s `is_aspect_iteration_variable`
  branch is covered both ways explicitly (the random sweep alone would
  need to also vary a boolean, which `random_samples`, built for
  continuous ranges, doesn't do — so this is driven directly rather than
  through the harness).
- `StStrc`'s `msupstr`/`m_struc` (PLAN.md §11 item 4) has no `self.data`
  attribute to read back — in the original it's a plain local, never
  assigned to the data structure, only printed. Checked against the
  original's `aintmass`/`clgsmass`/`coldmass` (which *are* real attributes)
  via a live call, and against a reference expression transcribed directly
  from the source for the `msupstr` piece specifically (same approach as
  `test_superconductors.py`'s `_reference_residual`).
"""

from __future__ import annotations

from unittest.mock import patch

from idempotence_tests._harness import random_samples, require_process
from rewritten_models.stellarator.stellarator import StGeom, StNewConfig, StStrc

require_process()

from process.core.model import DataStructure  # noqa: E402
from process.models.stellarator.stellarator import Stellarator  # noqa: E402


def _make_stellarator() -> Stellarator:
    """A bare Stellarator instance with a fresh DataStructure attached,
    bypassing __init__ (which needs 12 injected models none of
    st_new_config/st_geom/st_strc touch)."""
    s = Stellarator.__new__(Stellarator)
    s.data = DataStructure()
    s.outfile = 6
    return s


_ST_NEW_CONFIG_RANGES = {
    "rmajor": (3.0, 30.0),
    "b_plasma_toroidal_on_axis": (1.0, 15.0),
    "stella_config_aspect_ref": (5.0, 15.0),
    "stella_config_bt_ref": (1.0, 15.0),
    "stella_config_rmajor_ref": (3.0, 30.0),
    "stella_config_rminor_ref": (0.5, 5.0),
    "stella_config_coil_rmajor": (3.0, 30.0),
    "stella_config_coil_rminor": (0.5, 5.0),
    "stella_config_min_plasma_coil_distance": (0.0, 3.0),
    "f_st_coil_aspect": (0.5, 2.0),
    "aspect_iterated_value": (3.0, 15.0),
    "stella_config_coilspermodule": (1, 10),
    "stella_config_symmetry": (1, 20),
}


def _run_original_st_new_config(sample: dict, *, is_aspect_iteration_variable: bool) -> DataStructure:
    s = _make_stellarator()
    d = s.data
    d.physics.rmajor = sample["rmajor"]
    d.physics.b_plasma_toroidal_on_axis = sample["b_plasma_toroidal_on_axis"]
    d.physics.aspect = sample["aspect_iterated_value"]
    d.numerics.ixc = [1] if is_aspect_iteration_variable else [2, 3]
    d.stellarator_config.stella_config_aspect_ref = sample["stella_config_aspect_ref"]
    d.stellarator_config.stella_config_bt_ref = sample["stella_config_bt_ref"]
    d.stellarator_config.stella_config_rmajor_ref = sample["stella_config_rmajor_ref"]
    d.stellarator_config.stella_config_rminor_ref = sample["stella_config_rminor_ref"]
    d.stellarator_config.stella_config_coil_rmajor = sample["stella_config_coil_rmajor"]
    d.stellarator_config.stella_config_coil_rminor = sample["stella_config_coil_rminor"]
    d.stellarator_config.stella_config_min_plasma_coil_distance = sample[
        "stella_config_min_plasma_coil_distance"
    ]
    d.stellarator_config.stella_config_coilspermodule = int(sample["stella_config_coilspermodule"])
    d.stellarator_config.stella_config_symmetry = int(sample["stella_config_symmetry"])
    d.stellarator.f_st_coil_aspect = sample["f_st_coil_aspect"]

    with patch("process.models.stellarator.stellarator.load_stellarator_config"):
        s.st_new_config()
    return d


def test_st_new_config_random_sweep_both_iteration_branches():
    for is_aspect_iteration_variable in (False, True):
        samples = random_samples(
            _ST_NEW_CONFIG_RANGES,
            n=150,
            seed=72 if is_aspect_iteration_variable else 73,
        )
        for sample in samples:
            d = _run_original_st_new_config(
                sample, is_aspect_iteration_variable=is_aspect_iteration_variable
            )
            result = StNewConfig()(
                rmajor=sample["rmajor"],
                is_aspect_iteration_variable=is_aspect_iteration_variable,
                aspect_iterated_value=sample["aspect_iterated_value"],
                stella_config_aspect_ref=sample["stella_config_aspect_ref"],
                b_plasma_toroidal_on_axis=sample["b_plasma_toroidal_on_axis"],
                stella_config_bt_ref=sample["stella_config_bt_ref"],
                f_st_coil_aspect=sample["f_st_coil_aspect"],
                stella_config_coilspermodule=int(sample["stella_config_coilspermodule"]),
                stella_config_symmetry=int(sample["stella_config_symmetry"]),
                stella_config_rmajor_ref=sample["stella_config_rmajor_ref"],
                stella_config_rminor_ref=sample["stella_config_rminor_ref"],
                stella_config_coil_rmajor=sample["stella_config_coil_rmajor"],
                stella_config_coil_rminor=sample["stella_config_coil_rminor"],
                stella_config_min_plasma_coil_distance=sample[
                    "stella_config_min_plasma_coil_distance"
                ],
            )
            (
                aspect, rminor, eps, n_tf_coils, f_st_rmajor, f_st_rminor, f_st_aspect,
                f_st_n_coils, f_st_b, r_coil_major, r_coil_minor, f_coil_shape,
            ) = result

            expected = dict(
                aspect=d.physics.aspect, rminor=d.physics.rminor, eps=d.physics.eps,
                n_tf_coils=d.tfcoil.n_tf_coils, f_st_rmajor=d.stellarator.f_st_rmajor,
                f_st_rminor=d.stellarator.f_st_rminor, f_st_aspect=d.stellarator.f_st_aspect,
                f_st_n_coils=d.stellarator.f_st_n_coils, f_st_b=d.stellarator.f_st_b,
                r_coil_major=d.stellarator.r_coil_major, r_coil_minor=d.stellarator.r_coil_minor,
                f_coil_shape=d.stellarator.f_coil_shape,
            )
            actual = dict(
                aspect=aspect, rminor=rminor, eps=eps, n_tf_coils=n_tf_coils,
                f_st_rmajor=f_st_rmajor, f_st_rminor=f_st_rminor, f_st_aspect=f_st_aspect,
                f_st_n_coils=f_st_n_coils, f_st_b=f_st_b, r_coil_major=r_coil_major,
                r_coil_minor=r_coil_minor, f_coil_shape=f_coil_shape,
            )
            assert expected == actual, (is_aspect_iteration_variable, sample, expected, actual)


def test_st_geom_random_sweep():
    samples = random_samples(
        {
            "rminor": (0.5, 5.0),
            "f_st_rmajor": (0.5, 1.5),
            "f_st_rminor": (0.5, 1.5),
            "stella_config_vol_plasma": (100.0, 3000.0),
            "stella_config_plasma_surface": (200.0, 4000.0),
        },
        n=300,
        seed=74,
    )
    for sample in samples:
        s = _make_stellarator()
        d = s.data
        d.stellarator.f_st_rmajor = sample["f_st_rmajor"]
        d.stellarator.f_st_rminor = sample["f_st_rminor"]
        d.stellarator_config.stella_config_vol_plasma = sample["stella_config_vol_plasma"]
        d.stellarator_config.stella_config_plasma_surface = sample["stella_config_plasma_surface"]
        d.physics.rminor = sample["rminor"]

        s.st_geom()

        vol_plasma, a_plasma_surface, a_plasma_poloidal, a_plasma_surface_outboard = StGeom()(
            f_st_rmajor=sample["f_st_rmajor"],
            f_st_rminor=sample["f_st_rminor"],
            stella_config_vol_plasma=sample["stella_config_vol_plasma"],
            stella_config_plasma_surface=sample["stella_config_plasma_surface"],
            rminor=sample["rminor"],
        )
        assert vol_plasma == d.physics.vol_plasma
        assert a_plasma_surface == d.physics.a_plasma_surface
        assert a_plasma_poloidal == d.physics.a_plasma_poloidal
        assert a_plasma_surface_outboard == d.physics.a_plasma_surface_outboard


def _reference_msupstr(e_tf_magnetic_stored_total_gj: float) -> float:
    """Transcribed directly from Stellarator.st_strc's source (m_struc/msupstr
    are plain locals there, never assigned to self.data — nothing to read
    back from a live call, see module docstring)."""
    m_struc = 1.3483e0 * (1000.0e0 * e_tf_magnetic_stored_total_gj) ** 0.7821e0
    return 1000.0e0 * m_struc


def test_st_strc_random_sweep():
    samples = random_samples(
        {
            "e_tf_magnetic_stored_total_gj": (1.0, 300.0),
            "stella_config_coilsurface": (500.0, 6000.0),
            "f_st_rmajor": (0.5, 1.5),
            "r_coil_minor": (0.5, 5.0),
            "stella_config_coil_rminor": (0.5, 5.0),
            "dx_tf_inboard_out_toroidal": (0.1, 2.0),
            "len_tf_coil": (100.0, 2000.0),
            "n_tf_coils": (10.0, 60.0),
            "b_plasma_toroidal_on_axis": (1.0, 15.0),
            "den_steel": (7000.0, 8200.0),
            "m_tf_coils_total": (1.0e5, 1.0e7),
            "dewmkg": (0.0, 3.0e7),
        },
        n=300,
        seed=75,
    )
    for sample in samples:
        s = _make_stellarator()
        d = s.data
        d.tfcoil.e_tf_magnetic_stored_total_gj = sample["e_tf_magnetic_stored_total_gj"]
        d.stellarator_config.stella_config_coilsurface = sample["stella_config_coilsurface"]
        d.stellarator.f_st_rmajor = sample["f_st_rmajor"]
        d.stellarator.r_coil_minor = sample["r_coil_minor"]
        d.stellarator_config.stella_config_coil_rminor = sample["stella_config_coil_rminor"]
        d.tfcoil.dx_tf_inboard_out_toroidal = sample["dx_tf_inboard_out_toroidal"]
        d.tfcoil.len_tf_coil = sample["len_tf_coil"]
        d.tfcoil.n_tf_coils = sample["n_tf_coils"]
        d.physics.b_plasma_toroidal_on_axis = sample["b_plasma_toroidal_on_axis"]
        d.fwbs.den_steel = sample["den_steel"]
        d.tfcoil.m_tf_coils_total = sample["m_tf_coils_total"]
        d.fwbs.dewmkg = sample["dewmkg"]

        s.st_strc(False)

        fncmass, gsmass, msupstr, aintmass, clgsmass, coldmass = StStrc()(
            e_tf_magnetic_stored_total_gj=sample["e_tf_magnetic_stored_total_gj"],
            stella_config_coilsurface=sample["stella_config_coilsurface"],
            f_st_rmajor=sample["f_st_rmajor"],
            r_coil_minor=sample["r_coil_minor"],
            stella_config_coil_rminor=sample["stella_config_coil_rminor"],
            dx_tf_inboard_out_toroidal=sample["dx_tf_inboard_out_toroidal"],
            len_tf_coil=sample["len_tf_coil"],
            n_tf_coils=sample["n_tf_coils"],
            b_plasma_toroidal_on_axis=sample["b_plasma_toroidal_on_axis"],
            den_steel=sample["den_steel"],
            m_tf_coils_total=sample["m_tf_coils_total"],
            dewmkg=sample["dewmkg"],
        )

        assert fncmass == d.structure.fncmass == 0.0
        assert gsmass == d.structure.gsmass == 0.0
        assert aintmass == d.structure.aintmass
        assert clgsmass == d.structure.clgsmass
        assert coldmass == d.structure.coldmass
        assert msupstr == _reference_msupstr(sample["e_tf_magnetic_stored_total_gj"])
