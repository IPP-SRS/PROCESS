"""Functional rewrite of ``process/models/physics/density_limit.py``.

Original: ``PlasmaDensityLimit(Model)``, dependency-analysis node
``PlasmaDensityLimit`` (class model, entry method ``run``,
`models/physics/density_limit.py`). ``output()`` is out of scope, see
``rewritten_models/PLAN.md`` §5.

Granularity (PLAN.md §4 decision 5, revised): **one rewritten model per
original method, no further splitting** — this file has one class per
method the original class defines (11, excluding ``output()``): the 8
``calculate_*_density_limit`` static methods, ``get_density_limit_value``,
``calculate_density_limit``, and ``run`` itself. Where one original method
calls another (``run`` calls ``calculate_density_limit`` and
``get_density_limit_value``; ``calculate_density_limit`` calls each of the
8 correlations), the rewritten class does the same, just calling the
corresponding rewritten class instead of ``self.method(...)``. Naming
convention: a rewritten class is named after its original method in
PascalCase (`calculate_density_limit` -> `CalculateDensityLimit`), except
the entry method (`run`), which takes the original *class*'s name
(`PlasmaDensityLimit`) since "run" alone is true of every `Model` subclass
and carries no information. Whether any of these 11 should be split further
is deferred — see PLAN.md §13.

One behavioural note, not a bug, worth being explicit about: the original
``calculate_density_limit`` computes the switch-enforced value *twice* —
once as its own (unused-by-``run()``) second return value, and again via
``get_density_limit_value`` on the array. Only the second computation is
ever read; ``CalculateDensityLimit`` below only declares the array as its
output, not the unused second value. This is not a decomposition choice
(it doesn't split anything into an extra class) — it's the same "don't
reproduce provably-dead computation" rule as everywhere else in this
project, and is separately logged as a PROCESS bug, see PLAN.md §10.

``nd_plasma_electron_max_array`` is reproduced as a real output of
``CalculateDensityLimit`` even though, in the original, nothing besides
``run``'s own two single-element reads and the excluded ``output()`` report
uses the whole array. Scope rule, corrected (PLAN.md §5): excluding
``output()`` means excluding the literal print/format calls, not any real
computed quantity that happens to currently feed only those calls.

Three parameter renames versus the original static methods, all cases of
the same pattern as ``exhaust.py``: the *call site* (``run()``) already
uses the true global name, but the static method's own parameter used a
shorter local alias. Renamed here per naming rule 1 (PLAN.md §6), each
noted below:

- ``qcyl`` -> ``qstar`` (``qcyl`` is not a `process/data_structure` attribute
  anywhere; ``run()`` always feeds it ``self.data.physics.qstar``).
- ``c_plasma`` -> ``plasma_current`` (same situation; ``run()`` always feeds
  it ``self.data.physics.plasma_current``).
- ``zeff`` -> ``n_charge_plasma_effective_vol_avg`` (same situation; missed
  in the first pass of this rewrite, caught on a later review — ``run()``
  feeds ``calculate_density_limit``'s ``zeff`` parameter
  ``self.data.physics.n_charge_plasma_effective_vol_avg``, and ``zeff``
  itself is not a `process/data_structure` attribute).
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np

from rewritten_models._framework import ExplicitFunction, Output
from rewritten_models._namespace import declare

# --- switch domain ------------------------------------------------------
# Self-contained copy of process.models.physics.density_limit.DensityLimitModel
# (not imported, to keep this package isolated from PROCESS — see PLAN.md §1).
# The original's `full_name` property is dropped: it exists only to label the
# excluded `output()` report and isn't read by any in-scope computation.


class DensityLimitModel(IntEnum):
    """Which of the 8 density-limit correlations `i_density_limit` selects."""

    ASDEX = 1
    BORRASS_ITER_I = 2
    BORRASS_ITER_II = 3
    JET_EDGE_RADIATION = 4
    JET_SIMPLE = 5
    HUGILL_MURAKAMI = 6
    GREENWALD = 7
    ASDEX_NEW = 8


# --- shared namespace declarations --------------------------------------
# i_density_limit, prn1, qstar, plasma_current, rmajor, rminor,
# b_plasma_toroidal_on_axis, p_plasma_separatrix_mw, a_plasma_surface,
# n_charge_plasma_effective_vol_avg, nd_plasma_electrons_max,
# nd_plasma_electron_line, f_nd_plasma_greenwald,
# nd_plasma_electron_max_array already exist in process/data_structure and
# are used verbatim. The 8 individual correlation values have no existing
# per-value attribute — PROCESS only names the aggregate array — so these
# are minted here (origin="new").

declare(
    "nd_plasma_electron_max_asdex",
    description="ASDEX density limit correlation value (array index 0 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="AsdexDensityLimit",
)
declare(
    "nd_plasma_electron_max_borrass_iter_i",
    description="Borrass ITER I density limit correlation value (array index 1 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="BorrassIterIDensityLimit",
)
declare(
    "nd_plasma_electron_max_borrass_iter_ii",
    description="Borrass ITER II density limit correlation value (array index 2 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="BorrassIterIiDensityLimit",
)
declare(
    "nd_plasma_electron_max_jet_edge_radiation",
    description="JET edge radiation density limit correlation value (array index 3 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="JetEdgeRadiationDensityLimit",
)
declare(
    "nd_plasma_electron_max_jet_simple",
    description="JET simple density limit correlation value (array index 4 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="JetSimpleDensityLimit",
)
declare(
    "nd_plasma_electron_max_hugill_murakami",
    description="Hugill-Murakami density limit correlation value (array index 5 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="HugillMurakamiDensityLimit",
)
declare(
    "nd_plasma_electron_max_greenwald",
    description="Greenwald density limit correlation value (array index 6 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="GreenwaldDensityLimit",
)
declare(
    "nd_plasma_electron_max_asdex_new",
    description="ASDEX Upgrade new density limit correlation value (array index 7 in PROCESS)",
    unit="m^-3",
    origin="new",
    defining_model="AsdexNewDensityLimit",
)
declare(
    "nd_plasma_electron_max_array",
    description="All 8 density-limit correlation values, bundled into one array",
    unit="m^-3",
    origin="existing",
    source="physics_variables.PhysicsData.nd_plasma_electron_max_array",
    defining_model="CalculateDensityLimit",
)
declare(
    "nd_plasma_electrons_max",
    description="Switch-enforced plasma electron density upper limit",
    unit="m^-3",
    origin="existing",
    source="physics_variables.PhysicsData.nd_plasma_electrons_max",
    defining_model="GetDensityLimitValue",
)
declare(
    "f_nd_plasma_greenwald",
    description="Line-averaged electron density as a fraction of the Greenwald limit",
    unit="",
    origin="existing",
    source="physics_variables.PhysicsData.f_nd_plasma_greenwald",
    defining_model="PlasmaDensityLimit",
)


class AsdexDensityLimit(ExplicitFunction):
    """ASDEX density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_asdex_density_limit``
    (static method).

    References
    ----------
    T.C.Hender et.al., 'Physics Assessment of the European Reactor Study',
    AEA FUS 172, 1992
    """

    nd_plasma_electron_max_asdex = Output()

    def __call__(
        self,
        p_perp: float,
        b_plasma_toroidal_on_axis: float,
        q95: float,
        rmajor: float,
        prn1: float,
    ) -> float:
        """
        Parameters
        ----------
        p_perp : float
            Perpendicular power density (MW/m^2).
        b_plasma_toroidal_on_axis : float
            Toroidal field on axis (T).
        q95 : float
            Safety factor at 95% of the plasma poloidal flux.
        rmajor : float
            Plasma major radius (m).
        prn1 : float
            Edge density / average plasma density.
        """
        return (
            1.54e20
            * p_perp**0.43
            * b_plasma_toroidal_on_axis**0.31
            / (q95 * rmajor) ** 0.45
        ) / prn1


class BorrassIterIDensityLimit(ExplicitFunction):
    """Borrass ITER I density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_borrass_iter_i_density_limit``
    (static method).

    References
    ----------
    T.C.Hender et.al., 'Physics Assessment of the European Reactor Study',
    AEA FUS 172, 1992
    """

    nd_plasma_electron_max_borrass_iter_i = Output()

    def __call__(
        self,
        p_perp: float,
        b_plasma_toroidal_on_axis: float,
        q95: float,
        rmajor: float,
        prn1: float,
    ) -> float:
        """
        Parameters
        ----------
        p_perp : float
            Perpendicular power density (MW/m^2).
        b_plasma_toroidal_on_axis : float
            Toroidal field on axis (T).
        q95 : float
            Safety factor at 95% of the plasma poloidal flux.
        rmajor : float
            Plasma major radius (m).
        prn1 : float
            Edge density / average plasma density.
        """
        return (
            1.8e20
            * p_perp**0.53
            * b_plasma_toroidal_on_axis**0.31
            / (q95 * rmajor) ** 0.22
        ) / prn1


class BorrassIterIiDensityLimit(ExplicitFunction):
    """Borrass ITER II density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_borrass_iter_ii_density_limit``
    (static method).

    References
    ----------
    T.C.Hender et.al., 'Physics Assessment of the European Reactor Study',
    AEA FUS 172, 1992
    """

    nd_plasma_electron_max_borrass_iter_ii = Output()

    def __call__(
        self,
        p_perp: float,
        b_plasma_toroidal_on_axis: float,
        q95: float,
        rmajor: float,
        prn1: float,
    ) -> float:
        """
        Parameters
        ----------
        p_perp : float
            Perpendicular power density (MW/m^2).
        b_plasma_toroidal_on_axis : float
            Toroidal field on axis (T).
        q95 : float
            Safety factor at 95% of the plasma poloidal flux.
        rmajor : float
            Plasma major radius (m).
        prn1 : float
            Edge density / average plasma density.
        """
        return (
            0.5e20
            * p_perp**0.57
            * b_plasma_toroidal_on_axis**0.31
            / (q95 * rmajor) ** 0.09
        ) / prn1


class JetEdgeRadiationDensityLimit(ExplicitFunction):
    """JET edge radiation density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_jet_edge_radiation_density_limit``
    (static method).

    References
    ----------
    T.C.Hender et.al., 'Physics Assessment of the European Reactor Study',
    AEA FUS 172, 1992
    """

    nd_plasma_electron_max_jet_edge_radiation = Output()

    def __call__(
        self,
        n_charge_plasma_effective_vol_avg: float,
        p_hcd_injected_total_mw: float,
        prn1: float,
        qstar: float,
    ) -> float:
        """
        Parameters
        ----------
        n_charge_plasma_effective_vol_avg : float
            Effective charge (Z_eff), volume-averaged. Renamed from the
            original's local parameter name ``zeff`` — see module
            docstring.
        p_hcd_injected_total_mw : float
            Power injected into the plasma (MW).
        prn1 : float
            Edge density / average plasma density.
        qstar : float
            Equivalent cylindrical safety factor. Renamed from the
            original's local parameter name ``qcyl`` — see module
            docstring.
        """
        denom = (n_charge_plasma_effective_vol_avg - 1.0) * (1.0 - 4.0 / (3.0 * qstar))
        if denom <= 0.0:
            return 0.0
        return (1.0e20 * np.sqrt(p_hcd_injected_total_mw / denom)) / prn1


class JetSimpleDensityLimit(ExplicitFunction):
    """JET simple density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_jet_simple_density_limit``
    (static method).

    References
    ----------
    T.C.Hender et.al., 'Physics Assessment of the European Reactor Study',
    AEA FUS 172, 1992
    """

    nd_plasma_electron_max_jet_simple = Output()

    def __call__(
        self,
        b_plasma_toroidal_on_axis: float,
        p_plasma_separatrix_mw: float,
        rmajor: float,
        prn1: float,
    ) -> float:
        """
        Parameters
        ----------
        b_plasma_toroidal_on_axis : float
            Toroidal field on axis (T).
        p_plasma_separatrix_mw : float
            Power crossing the separatrix (MW).
        rmajor : float
            Plasma major radius (m).
        prn1 : float
            Edge density / average plasma density.
        """
        return (
            0.237e20 * b_plasma_toroidal_on_axis * np.sqrt(p_plasma_separatrix_mw) / rmajor
        ) / prn1


class HugillMurakamiDensityLimit(ExplicitFunction):
    """Hugill-Murakami density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_hugill_murakami_density_limit``
    (static method).

    References
    ----------
    N.A. Uckan and ITER Physics Group, 'ITER Physics Design Guidelines: 1989'
    """

    nd_plasma_electron_max_hugill_murakami = Output()

    def __call__(
        self, b_plasma_toroidal_on_axis: float, rmajor: float, qstar: float
    ) -> float:
        """
        Parameters
        ----------
        b_plasma_toroidal_on_axis : float
            Toroidal field on axis (T).
        rmajor : float
            Plasma major radius (m).
        qstar : float
            Equivalent cylindrical safety factor. Renamed from the
            original's local parameter name ``qcyl`` — see module
            docstring.
        """
        return 3.0e20 * b_plasma_toroidal_on_axis / (rmajor * qstar)


class GreenwaldDensityLimit(ExplicitFunction):
    """Greenwald density limit correlation (n_GW).

    Original: ``PlasmaDensityLimit.calculate_greenwald_density_limit``
    (static method). Typically applied to the line-averaged electron density.

    References
    ----------
    M. Greenwald et al., "A new look at density limits in tokamaks,"
    Nuclear Fusion, vol. 28, no. 12, pp. 2199-2207, Dec. 1988,
    doi: https://doi.org/10.1088/0029-5515/28/12/009.

    M. Greenwald, "Density limits in toroidal plasmas," Plasma Physics and
    Controlled Fusion, vol. 44, no. 8, pp. R27-R53, Jul. 2002,
    doi: https://doi.org/10.1088/0741-3335/44/8/201.
    """

    nd_plasma_electron_max_greenwald = Output()

    def __call__(self, plasma_current: float, rminor: float) -> float:
        """
        Parameters
        ----------
        plasma_current : float
            Plasma current (A). Renamed from the original's local
            parameter name ``c_plasma`` — see module docstring.
        rminor : float
            Plasma minor radius (m).
        """
        return 1.0e14 * plasma_current / (np.pi * rminor**2)


class AsdexNewDensityLimit(ExplicitFunction):
    """ASDEX Upgrade new density limit correlation.

    Original: ``PlasmaDensityLimit.calculate_asdex_new_density_limit``
    (static method). For the separatrix density, scaled by ``prn1`` to a
    volume average.

    References
    ----------
    J. W. Berkery et al., "Density limits as disruption forecasters for
    spherical tokamaks," Plasma Physics and Controlled Fusion, vol. 65,
    no. 9, pp. 095003-095003, Jul. 2023,
    doi: https://doi.org/10.1088/1361-6587/ace476.

    M. Bernert et al., "The H-mode density limit in the full tungsten
    ASDEX Upgrade tokamak," vol. 57, no. 1, pp. 014038-014038, Nov. 2014,
    doi: https://doi.org/10.1088/0741-3335/57/1/014038.
    """

    nd_plasma_electron_max_asdex_new = Output()

    def __call__(
        self,
        p_hcd_injected_total_mw: float,
        plasma_current: float,
        q95: float,
        prn1: float,
    ) -> float:
        """
        Parameters
        ----------
        p_hcd_injected_total_mw : float
            Power injected into the plasma (MW).
        plasma_current : float
            Plasma current (A). Renamed from the original's local
            parameter name ``c_plasma`` — see module docstring.
        q95 : float
            Safety factor at 95% surface.
        prn1 : float
            Edge density / average plasma density.
        """
        return (
            1.0e20
            * 0.506
            * (p_hcd_injected_total_mw**0.396 * (plasma_current / 1.0e6) ** 0.265)
            / (q95**0.323)
        ) / prn1


class CalculateDensityLimit(ExplicitFunction):
    """Compute all 8 density-limit correlations, bundled into one array.

    Original: ``PlasmaDensityLimit.calculate_density_limit``. Calls each of
    the 8 correlation classes above exactly where the original calls the
    corresponding ``self.calculate_*`` method; ``p_perp`` is computed inline
    since it's inline in the original method, not its own method. The
    switch validation is reproduced faithfully even though ``run`` (below)
    also validates the same value before this is ever called — that
    duplication exists in the original too (see PLAN.md §11 item 3 for the
    difference between this, real-but-redundant validation, and the
    genuinely dead second-return-value the original also has here, which
    is *not* reproduced).

    Deviation: raises the built-in ``ValueError`` on an illegal switch value,
    not PROCESS's ``ProcessValueError`` — importing ``process.core.exceptions``
    would break this package's isolation from PROCESS.
    """

    nd_plasma_electron_max_array = Output()

    def __call__(
        self,
        b_plasma_toroidal_on_axis: float,
        i_density_limit: int,
        p_plasma_separatrix_mw: float,
        p_hcd_injected_total_mw: float,
        plasma_current: float,
        prn1: float,
        qstar: float,
        q95: float,
        rmajor: float,
        rminor: float,
        a_plasma_surface: float,
        n_charge_plasma_effective_vol_avg: float,
    ) -> list[float]:
        """
        Parameters
        ----------
        b_plasma_toroidal_on_axis : float
            Toroidal field on axis (T).
        i_density_limit : int
            Switch denoting which correlation is (elsewhere) enforced (1-8)
            — used here only to validate, matching the original.
        p_plasma_separatrix_mw : float
            Power flowing to the edge plasma via charged particles (MW).
        p_hcd_injected_total_mw : float
            Power injected into the plasma (MW).
        plasma_current : float
            Plasma current (A).
        prn1 : float
            Edge density / average plasma density.
        qstar : float
            Equivalent cylindrical safety factor. Renamed from the
            original's local parameter name ``qcyl`` — see module
            docstring.
        q95 : float
            Safety factor at 95% surface.
        rmajor : float
            Plasma major radius (m).
        rminor : float
            Plasma minor radius (m).
        a_plasma_surface : float
            Plasma surface area (m^2).
        n_charge_plasma_effective_vol_avg : float
            Effective charge (Z_eff), volume-averaged. Renamed from the
            original's local parameter name ``zeff`` — see module
            docstring.
        """
        try:
            DensityLimitModel(i_density_limit)
        except ValueError:
            raise ValueError(
                f"Illegal value of i_density_limit: {i_density_limit!r} (must be 1-8)"
            ) from None

        p_perp = p_plasma_separatrix_mw / a_plasma_surface

        return [
            AsdexDensityLimit()(
                p_perp=p_perp,
                b_plasma_toroidal_on_axis=b_plasma_toroidal_on_axis,
                q95=q95, rmajor=rmajor, prn1=prn1,
            ),
            BorrassIterIDensityLimit()(
                p_perp=p_perp,
                b_plasma_toroidal_on_axis=b_plasma_toroidal_on_axis,
                q95=q95, rmajor=rmajor, prn1=prn1,
            ),
            BorrassIterIiDensityLimit()(
                p_perp=p_perp,
                b_plasma_toroidal_on_axis=b_plasma_toroidal_on_axis,
                q95=q95, rmajor=rmajor, prn1=prn1,
            ),
            JetEdgeRadiationDensityLimit()(
                n_charge_plasma_effective_vol_avg=n_charge_plasma_effective_vol_avg,
                p_hcd_injected_total_mw=p_hcd_injected_total_mw,
                prn1=prn1, qstar=qstar,
            ),
            JetSimpleDensityLimit()(
                b_plasma_toroidal_on_axis=b_plasma_toroidal_on_axis,
                p_plasma_separatrix_mw=p_plasma_separatrix_mw,
                rmajor=rmajor, prn1=prn1,
            ),
            HugillMurakamiDensityLimit()(
                b_plasma_toroidal_on_axis=b_plasma_toroidal_on_axis,
                rmajor=rmajor, qstar=qstar,
            ),
            GreenwaldDensityLimit()(plasma_current=plasma_current, rminor=rminor),
            AsdexNewDensityLimit()(
                p_hcd_injected_total_mw=p_hcd_injected_total_mw,
                plasma_current=plasma_current, q95=q95, prn1=prn1,
            ),
        ]


class GetDensityLimitValue(ExplicitFunction):
    """Select the density-limit correlation value PROCESS actually enforces.

    Original: ``PlasmaDensityLimit.get_density_limit_value``. The original
    takes an already-validated ``DensityLimitModel`` enum member (its
    caller, ``run``, does the ``int`` -> enum conversion and validation
    beforehand); this rewrite takes the raw ``i_density_limit`` int
    (the global-namespace name) and does that conversion internally instead
    — the closest equivalent that still fits a plain-parameter interface,
    since ``DensityLimitModel`` isn't itself a global-namespace name. An
    invalid value still raises (``ValueError`` from the enum constructor),
    matching the original's behaviour of assuming its caller already
    validated.
    """

    nd_plasma_electrons_max = Output()

    def __call__(self, i_density_limit: int, nd_plasma_electron_max_array: list[float]) -> float:
        """
        Parameters
        ----------
        i_density_limit : int
            Switch denoting which correlation to enforce (1-8).
        nd_plasma_electron_max_array : list[float]
            The 8 correlation values, from `CalculateDensityLimit` above.
        """
        model = DensityLimitModel(i_density_limit)
        model_map = {
            DensityLimitModel.ASDEX: nd_plasma_electron_max_array[0],
            DensityLimitModel.BORRASS_ITER_I: nd_plasma_electron_max_array[1],
            DensityLimitModel.BORRASS_ITER_II: nd_plasma_electron_max_array[2],
            DensityLimitModel.JET_EDGE_RADIATION: nd_plasma_electron_max_array[3],
            DensityLimitModel.JET_SIMPLE: nd_plasma_electron_max_array[4],
            DensityLimitModel.HUGILL_MURAKAMI: nd_plasma_electron_max_array[5],
            DensityLimitModel.GREENWALD: nd_plasma_electron_max_array[6],
            DensityLimitModel.ASDEX_NEW: nd_plasma_electron_max_array[7],
        }
        return model_map[model]


class PlasmaDensityLimit(ExplicitFunction):
    """Calculate plasma density limits and the Greenwald fraction.

    Original: ``PlasmaDensityLimit.run`` — the dependency-analysis node's
    own entry method, so this class takes the node's own name rather than
    ``Run`` (every `Model` subclass has a `run`; only this class's own name
    says what it actually does). Calls `CalculateDensityLimit` and
    `GetDensityLimitValue` exactly where the original calls
    ``self.calculate_density_limit``/``self.get_density_limit_value``; the
    Greenwald-fraction line is inlined since it's inline in the original
    method too.

    Deviation: raises the built-in ``ValueError`` on an illegal switch
    value, not PROCESS's ``ProcessValueError`` — same reason as
    `CalculateDensityLimit`/`GetDensityLimitValue` above.
    """

    nd_plasma_electron_max_array = Output()
    nd_plasma_electrons_max = Output()
    f_nd_plasma_greenwald = Output()

    def __call__(
        self,
        b_plasma_toroidal_on_axis: float,
        i_density_limit: int,
        p_plasma_separatrix_mw: float,
        p_hcd_injected_total_mw: float,
        plasma_current: float,
        prn1: float,
        qstar: float,
        q95: float,
        rmajor: float,
        rminor: float,
        a_plasma_surface: float,
        n_charge_plasma_effective_vol_avg: float,
        nd_plasma_electron_line: float,
    ) -> tuple[list[float], float, float]:
        """
        Parameters
        ----------
        b_plasma_toroidal_on_axis, p_plasma_separatrix_mw,
        p_hcd_injected_total_mw, plasma_current, prn1, qstar, q95, rmajor,
        rminor, a_plasma_surface, n_charge_plasma_effective_vol_avg :
            See `CalculateDensityLimit` above — passed straight through.
        i_density_limit : int
            Switch denoting which correlation to enforce (1-8).
        nd_plasma_electron_line : float
            Line-averaged electron density (m^-3).
        """
        nd_plasma_electron_max_array = CalculateDensityLimit()(
            b_plasma_toroidal_on_axis=b_plasma_toroidal_on_axis,
            i_density_limit=i_density_limit,
            p_plasma_separatrix_mw=p_plasma_separatrix_mw,
            p_hcd_injected_total_mw=p_hcd_injected_total_mw,
            plasma_current=plasma_current,
            prn1=prn1,
            qstar=qstar,
            q95=q95,
            rmajor=rmajor,
            rminor=rminor,
            a_plasma_surface=a_plasma_surface,
            n_charge_plasma_effective_vol_avg=n_charge_plasma_effective_vol_avg,
        )

        try:
            nd_plasma_electrons_max = GetDensityLimitValue()(
                i_density_limit=i_density_limit,
                nd_plasma_electron_max_array=nd_plasma_electron_max_array,
            )
        except ValueError:
            raise ValueError(
                f"Illegal value of i_density_limit: {i_density_limit!r} (must be 1-8)"
            ) from None

        f_nd_plasma_greenwald = nd_plasma_electron_line / nd_plasma_electron_max_array[6]

        return nd_plasma_electron_max_array, nd_plasma_electrons_max, f_nd_plasma_greenwald
