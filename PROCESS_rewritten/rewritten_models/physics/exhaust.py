"""Functional rewrite of ``process/models/physics/exhaust.py``.

Original: ``PlasmaExhaust(Model)``, dependency-analysis node ``PlasmaExhaust``
(class model, entry method ``calculate_separatrix_power``,
`models/physics/exhaust.py`). Only the four computational static methods are
in scope — ``output()`` (report-writing to the .out file) is deliberately
excluded, see ``rewritten_models/PLAN.md`` §5.

All four original methods were already effectively pure functions with
kwargs matching the global namespace, so this is close to a direct
translation. The one deviation: ``calculate_radiation_fraction``'s original
parameter ``p_plasma_heating_mw`` is renamed to ``p_plasma_heating_total_mw``
— every call site actually feeds it ``physics.p_plasma_heating_total_mw``,
and that name (not ``p_plasma_heating_mw``) is the one that exists in
``process/data_structure/physics_variables.py``. See PLAN.md §9.
"""

from __future__ import annotations

from rewritten_models._framework import ExplicitFunction, Output
from rewritten_models._namespace import declare

# --- shared namespace declarations for this model's outputs -----------------

declare(
    "p_plasma_separatrix_mw",
    description="Power crossing the plasma separatrix",
    unit="MW",
    origin="existing",
    source="physics_variables.PhysicsData.p_plasma_separatrix_mw",
    defining_model="PlasmaSeparatrixPower",
)
declare(
    "p_plasma_separatrix_rmajor_mw",
    description="Power crossing the separatrix, per unit major radius",
    unit="MW/m",
    origin="existing",
    source="physics_variables.PhysicsData.p_plasma_separatrix_rmajor_mw",
    defining_model="PsepOverRMetric",
)
declare(
    "p_div_bt_q_aspect_rmajor_mw",
    description=(
        "EU-DEMO divertor protection re-attachment metric, "
        "Psep * Bt / (q95 * aspect * rmajor)"
    ),
    unit="MW T/m",
    origin="existing",
    source="physics_variables.PhysicsData.p_div_bt_q_aspect_rmajor_mw",
    defining_model="EuDemoReattachmentMetric",
)
declare(
    "f_p_plasma_separatrix_rad",
    description="Radiation fraction of the plasma (radiated / total heating power)",
    unit="",
    origin="existing",
    source="physics_variables.PhysicsData.f_p_plasma_separatrix_rad",
    defining_model="RadiationFraction",
)


class PlasmaSeparatrixPower(ExplicitFunction):
    """Power crossing the plasma separatrix (P_sep).

    Original: ``PlasmaExhaust.calculate_separatrix_power`` (static method).
    """

    p_plasma_separatrix_mw = Output()

    def __call__(
        self,
        f_p_alpha_plasma_deposited: float,
        p_alpha_total_mw: float,
        p_non_alpha_charged_mw: float,
        p_hcd_injected_total_mw: float,
        p_plasma_ohmic_mw: float,
        p_plasma_rad_mw: float,
    ) -> float:
        """
        Parameters
        ----------
        f_p_alpha_plasma_deposited : float
            Fraction of alpha power deposited in plasma.
        p_alpha_total_mw : float
            Total alpha power produced (MW).
        p_non_alpha_charged_mw : float
            Power from non-alpha charged particles (MW).
        p_hcd_injected_total_mw : float
            Total power injected by heating and current drive (MW). Note:
            at the original call site in ``Physics.run`` this is 0 rather
            than the raw global value when the plasma is ignited — that
            branch belongs to whichever model computes the ignition state
            (`Physics`), not to this one; this function just takes whatever
            value it's given.
        p_plasma_ohmic_mw : float
            Ohmic heating power (MW).
        p_plasma_rad_mw : float
            Radiated power from plasma (MW).
        """
        return (
            f_p_alpha_plasma_deposited * p_alpha_total_mw
            + p_non_alpha_charged_mw
            + p_hcd_injected_total_mw
            + p_plasma_ohmic_mw
            - p_plasma_rad_mw
        )


class PsepOverRMetric(ExplicitFunction):
    """Power crossing the separatrix, normalised by major radius (Psep / R0).

    Original: ``PlasmaExhaust.calculate_psep_over_r_metric`` (static method).
    """

    p_plasma_separatrix_rmajor_mw = Output()

    def __call__(self, p_plasma_separatrix_mw: float, rmajor: float) -> float:
        """
        Parameters
        ----------
        p_plasma_separatrix_mw : float
            Power crossing the separatrix (MW).
        rmajor : float
            Plasma major radius (m).
        """
        return p_plasma_separatrix_mw / rmajor


class EuDemoReattachmentMetric(ExplicitFunction):
    """EU-DEMO divertor protection re-attachment metric (Psep*Bt / q95*A*R0).

    Original: ``PlasmaExhaust.calculate_eu_demo_re_attachment_metric``
    (static method).

    References
    ----------
    [1] M. Siccinio, G. Federici, R. Kembleton, H. Lux, F. Maviglia, and
    J. Morris, "Figure of merit for divertor protection in the preliminary
    design of the EU-DEMO reactor," Nuclear Fusion, vol. 59, no. 10,
    pp. 106026-106026, Jul. 2019, doi: https://doi.org/10.1088/1741-4326/ab3153.

    [2] H. Zohm et al., "A stepladder approach to a tokamak fusion power
    plant," Nuclear Fusion, vol. 57, no. 8, pp. 086002-086002, May 2017,
    doi: https://doi.org/10.1088/1741-4326/aa739e.
    """

    p_div_bt_q_aspect_rmajor_mw = Output()

    def __call__(
        self,
        p_plasma_separatrix_mw: float,
        b_plasma_toroidal_on_axis: float,
        q95: float,
        aspect: float,
        rmajor: float,
    ) -> float:
        """
        Parameters
        ----------
        p_plasma_separatrix_mw : float
            Power crossing the separatrix (MW).
        b_plasma_toroidal_on_axis : float
            Toroidal magnetic field on axis (T).
        q95 : float
            Safety factor at 95% flux surface.
        aspect : float
            Aspect ratio of the plasma.
        rmajor : float
            Plasma major radius (m).
        """
        return (p_plasma_separatrix_mw * b_plasma_toroidal_on_axis) / (
            q95 * aspect * rmajor
        )


class RadiationFraction(ExplicitFunction):
    """Radiation fraction of the plasma (radiated power / total heating power).

    Original: ``PlasmaExhaust.calculate_radiation_fraction`` (static method).

    Deviation from the original: the second parameter is named
    ``p_plasma_heating_total_mw`` here, not the original's
    ``p_plasma_heating_mw`` — see module docstring and PLAN.md §9. Original
    behaviour (return 0 with a warning if heating power is zero, rather than
    raising a ZeroDivisionError) is preserved.
    """

    f_p_plasma_separatrix_rad = Output()

    def __call__(self, p_plasma_rad_mw: float, p_plasma_heating_total_mw: float) -> float:
        """
        Parameters
        ----------
        p_plasma_rad_mw : float
            Radiated power from plasma (MW).
        p_plasma_heating_total_mw : float
            Total plasma heating power (MW).
        """
        if p_plasma_heating_total_mw == 0:
            return 0.0

        return p_plasma_rad_mw / p_plasma_heating_total_mw
