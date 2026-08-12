"""Functional rewrite of a slice of ``process/models/stellarator/stellarator.py``.

Original: ``Stellarator(Model)``, dependency-analysis node ``Stellarator``
(class model, entry method ``run``, `models/stellarator/stellarator.py`,
stellarator-only — not in the tokamak graph). This is a large node (2585
lines, 8 methods) and this stage only covers 3 of them — the ones that are
both self-contained (call no other model's methods, unlike
``blanket_neutronics``/``st_fwbs`` which call into ``CCFE_HCPB``, not yet
rewritten) and proof-of-principle scale:

- ``st_new_config`` (~85 lines): initial config-driven geometry scaling.
- ``st_geom`` (~44 lines): plasma volume/surface area from the scale factors.
- ``st_strc`` (~102 lines, computational part only — its ``output`` block
  is excluded per PLAN.md §5, same as every other model's `output()`).

Granularity (PLAN.md §4 decision 5, revised): **one rewritten model per
original method, no further splitting** — this file has exactly 3 classes,
``StNewConfig``, ``StGeom``, ``StStrc``, each with every output its
corresponding original method has, reproduced as written. This is
different from an earlier version of this file (10 classes, one per
independently-traceable output) — see PLAN.md §11 item 8 for why that
approach was superseded; whether any of these 3 should be split further is
deferred, PLAN.md §13.

Deliberately **not** covered here, and why (PLAN.md §7 "known gaps" pattern):

- ``run()`` / ``output()``: almost entirely a call sequence into other
  models (``self.costs.run()``, ``st_heat(...)``, ``self.st_phys(...)``,
  ``self.power.tfpwr(...)``, ...) plus the outer double-call-to-st_phys
  convergence pattern the original's own comment says "should be
  integrated to avoid this double call" — i.e. this is composition-layer
  work, out of scope per PLAN.md §5 decision 2, exactly like `Caller`.
- ``st_fwbs`` (~1196 lines), ``st_phys`` (~566 lines),
  ``sc_tf_coil_nuclear_heating_iter90`` (~203 lines): each individually
  larger than any tokamak-side POC model, and `blanket_neutronics`/`st_fwbs`
  call into `CCFE_HCPB` (a separate, not-yet-rewritten node). Stage-5 scale
  work, not proof-of-principle scale — deferred.

One thing intentionally not reproduced, PLAN.md §5-scoped:

- ``load_stellarator_config(...)`` (the file-I/O call at the top of the
  original ``st_new_config``) belongs to a *different* dependency-analysis
  node (``stellarator.preset_config_functions``, not yet rewritten). Its
  outputs — the ``stella_config_*`` reference constants — are taken here as
  plain inputs, already loaded, per naming rule 4 (config becomes input
  arguments, not a parametrized sub-object).

``msupstr``/``m_struc`` in the original ``st_strc`` — an explicitly
"not really trusted" alternative scaling law, computed unconditionally but
only ever *printed* (next to ``aintmass``, for comparison) inside the
excluded ``if output:`` block — **is** reproduced, as ``StStrc``'s
``msupstr`` output. Scope rule, corrected (PLAN.md §5): excluding
``output()`` means excluding the literal print calls, not a real computed
quantity that happens to currently feed only those calls. ``m_struc``
itself stays an undecorated local (naming rule 6): it's consumed exactly
once, to compute ``msupstr``, nowhere else in the original.

One finding, not a bug fix (PLAN.md §5): ``f_st_n_coils`` is defined as
``n_tf_coils / (stella_config_coilspermodule * stella_config_symmetry)``,
but two lines earlier in the *same* original method, ``n_tf_coils`` is
itself assigned exactly ``stella_config_coilspermodule *
stella_config_symmetry`` — so `f_st_n_coils` is provably always `1.0`
within one call to this function. Reproduced faithfully below (as a
function of its stated inputs, not hardcoded to `1.0`) since nothing
guarantees `n_tf_coils` couldn't diverge from that formula before this
function runs (e.g. if a future caller passes in a `n_tf_coils` set by some
other route) — see PLAN.md §10 findings log.
"""

from __future__ import annotations

import numpy as np

from rewritten_models._framework import ExplicitFunction, Output
from rewritten_models._namespace import declare

# --- shared namespace declarations --------------------------------------
# aspect, rminor, eps, n_tf_coils, f_st_rmajor, f_st_rminor, f_st_aspect,
# f_st_n_coils, f_st_b, r_coil_major, r_coil_minor, f_coil_shape,
# vol_plasma, a_plasma_surface, a_plasma_poloidal, a_plasma_surface_outboard,
# fncmass, gsmass, aintmass, clgsmass, coldmass already exist in
# process/data_structure and are used verbatim. Three genuinely new names:

declare(
    "aspect_iterated_value",
    description=(
        "The plasma aspect ratio value already present before stellarator "
        "config-driven geometry scaling runs — used only when the optimiser "
        "is actively iterating it (see is_aspect_iteration_variable)"
    ),
    unit="",
    origin="new",
    defining_model=None,
    notes=(
        "Original: self.data.physics.aspect, read (not written) inside "
        "st_new_config's `if 1 not in ixc` branch. Named distinctly from "
        "the `aspect` Output below — same physical quantity, but here it's "
        "an upstream-supplied value being conditionally kept, not what this "
        "model computes; using the same name for both an Output and a "
        "same-model Input would be confusing outside the ImplicitFunction "
        "case where that's the whole point (PLAN.md §6)."
    ),
)
declare(
    "is_aspect_iteration_variable",
    description=(
        "Whether plasma aspect ratio is currently one of the optimiser's active "
        "iteration variables (original: `1 in self.data.numerics.ixc`, "
        "aspect ratio being PROCESS iteration-variable #1)"
    ),
    unit="",
    origin="new",
    defining_model=None,
    notes=(
        "Solver/optimiser bookkeeping, evaluated upstream by the "
        "not-yet-modelled composition layer (PLAN.md §5 decision 2) — this "
        "model just takes the already-evaluated boolean, not PROCESS's "
        "`ixc` array or its iteration-variable-numbering convention "
        "(keeping that convention out of this isolated namespace)."
    ),
)
declare(
    "msupstr",
    description=(
        "Intercoil support structure mass, from an older/alternative "
        "scaling law kept only as a reference point against aintmass"
    ),
    unit="kg",
    origin="new",
    defining_model="StStrc",
    notes=(
        "Not a process/data_structure attribute — in the original this is a "
        "plain local (`msupstr`), never assigned to self.data, whose only "
        "use is a comparison print inside the excluded output() block. "
        "Reproduced anyway per the corrected scope rule (module docstring, "
        "PLAN.md §5/§11 item 4)."
    ),
)


class StNewConfig(ExplicitFunction):
    """Initialise stellarator geometry scale factors and coil radii.

    Original: ``Stellarator.st_new_config``. All 12 of the original
    method's outputs, reproduced together — the original itself never
    hands any of these to another method individually until later methods
    (``st_geom``, ``st_strc``), so nothing here is split out (PLAN.md §4
    decision 5, revised).
    """

    aspect = Output()
    rminor = Output()
    eps = Output()
    n_tf_coils = Output()
    f_st_rmajor = Output()
    f_st_rminor = Output()
    f_st_aspect = Output()
    f_st_n_coils = Output()
    f_st_b = Output()
    r_coil_major = Output()
    r_coil_minor = Output()
    f_coil_shape = Output()

    def __call__(
        self,
        rmajor: float,
        is_aspect_iteration_variable: bool,
        aspect_iterated_value: float,
        stella_config_aspect_ref: float,
        b_plasma_toroidal_on_axis: float,
        stella_config_bt_ref: float,
        f_st_coil_aspect: float,
        stella_config_coilspermodule: int,
        stella_config_symmetry: int,
        stella_config_rmajor_ref: float,
        stella_config_rminor_ref: float,
        stella_config_coil_rmajor: float,
        stella_config_coil_rminor: float,
        stella_config_min_plasma_coil_distance: float,
    ) -> tuple[
        float, float, float, float, float, float, float, float, float, float, float, float
    ]:
        """
        Parameters
        ----------
        rmajor : float
            Plasma major radius (m).
        is_aspect_iteration_variable : bool
            Whether aspect ratio is an active optimiser iteration variable
            (see namespace declaration above).
        aspect_iterated_value : float
            Aspect ratio value already present when
            ``is_aspect_iteration_variable`` is True (see namespace
            declaration above).
        stella_config_aspect_ref, stella_config_bt_ref,
        stella_config_rmajor_ref, stella_config_rminor_ref,
        stella_config_coil_rmajor, stella_config_coil_rminor,
        stella_config_min_plasma_coil_distance :
            Reference-configuration geometry constants.
        b_plasma_toroidal_on_axis : float
            Toroidal magnetic field on axis (T).
        f_st_coil_aspect : float
            Coil aspect ratio scaling factor (external input, not computed
            by this or any other model).
        stella_config_coilspermodule, stella_config_symmetry : int
            Number of TF coils per module / number of modules, from the
            stellarator configuration.
        """
        aspect = (
            aspect_iterated_value if is_aspect_iteration_variable else stella_config_aspect_ref
        )

        rminor = rmajor / aspect
        eps = 1.0 / aspect

        # This overwrites n_tf_coils from the input file.
        n_tf_coils = stella_config_coilspermodule * stella_config_symmetry

        f_st_rmajor = rmajor / stella_config_rmajor_ref
        f_st_rminor = rminor / stella_config_rminor_ref
        f_st_aspect = aspect / stella_config_aspect_ref
        # See module docstring: provably always 1.0, reproduced as a
        # function of its stated inputs anyway (PLAN.md §10).
        f_st_n_coils = n_tf_coils / (stella_config_coilspermodule * stella_config_symmetry)
        f_st_b = b_plasma_toroidal_on_axis / stella_config_bt_ref

        r_coil_major = stella_config_coil_rmajor * f_st_rmajor
        r_coil_minor = stella_config_coil_rminor * f_st_rmajor / f_st_coil_aspect

        f_coil_shape = (
            stella_config_min_plasma_coil_distance + stella_config_rminor_ref
        ) / stella_config_coil_rminor

        return (
            aspect, rminor, eps, n_tf_coils, f_st_rmajor, f_st_rminor, f_st_aspect,
            f_st_n_coils, f_st_b, r_coil_major, r_coil_minor, f_coil_shape,
        )


class StGeom(ExplicitFunction):
    """Plasma volume and surface area for a stellarator.

    Original: ``Stellarator.st_geom`` — simple scaling based on a Fourier
    representation, per Geiger's documentation. All 4 of the original
    method's outputs, reproduced together (PLAN.md §4 decision 5, revised).

    References
    ----------
    J. Geiger, IPP Greifswald internal document: 'Darstellung von
    ineinandergeschachtelten toroidal geschlossenen Flaechen mit
    Fourierkoeffizienten' ('Representation of nested, closed surfaces with
    Fourier coefficients')
    """

    vol_plasma = Output()
    a_plasma_surface = Output()
    a_plasma_poloidal = Output()
    a_plasma_surface_outboard = Output()

    def __call__(
        self,
        f_st_rmajor: float,
        f_st_rminor: float,
        stella_config_vol_plasma: float,
        stella_config_plasma_surface: float,
        rminor: float,
    ) -> tuple[float, float, float, float]:
        """
        Parameters
        ----------
        f_st_rmajor, f_st_rminor : float
            Major/minor radius scale factors — from `StNewConfig` above.
        stella_config_vol_plasma, stella_config_plasma_surface : float
            Reference-configuration plasma volume (m^3) / surface area (m^2).
        rminor : float
            Plasma minor radius (m) — from `StNewConfig` above.
        """
        vol_plasma = f_st_rmajor * f_st_rminor**2 * stella_config_vol_plasma

        # Plasma surface scaled from effective parameter:
        a_plasma_surface = f_st_rmajor * f_st_rminor * stella_config_plasma_surface

        # Plasma cross section area. Approximated (average, could be
        # calculated for every toroidal angle if desired).
        a_plasma_poloidal = np.pi * rminor * rminor

        # a_plasma_surface_outboard is retained only for obsolescent fispact
        # calculation... Cross-sectional area, averaged over toroidal angle.
        # Used only in the divertor model; approximate as for tokamaks.
        a_plasma_surface_outboard = 0.5 * a_plasma_surface

        return vol_plasma, a_plasma_surface, a_plasma_poloidal, a_plasma_surface_outboard


class StStrc(ExplicitFunction):
    """Structural masses for a stellarator.

    Original: ``Stellarator.st_strc``, computational part only — its
    ``if output:`` block is excluded per PLAN.md §5, same as every other
    model's `output()`. "In practice, many of the masses are simply set to
    zero to avoid double-counting of structural components that are
    specified differently for tokamaks." All 6 of the original method's
    outputs, reproduced together (PLAN.md §4 decision 5, revised);
    ``m_struc`` stays an undecorated local, see module docstring.
    """

    fncmass = Output()
    gsmass = Output()
    msupstr = Output()
    aintmass = Output()
    clgsmass = Output()
    coldmass = Output()

    def __call__(
        self,
        e_tf_magnetic_stored_total_gj: float,
        stella_config_coilsurface: float,
        f_st_rmajor: float,
        r_coil_minor: float,
        stella_config_coil_rminor: float,
        dx_tf_inboard_out_toroidal: float,
        len_tf_coil: float,
        n_tf_coils: float,
        b_plasma_toroidal_on_axis: float,
        den_steel: float,
        m_tf_coils_total: float,
        dewmkg: float,
    ) -> tuple[float, float, float, float, float, float]:
        """
        Parameters
        ----------
        e_tf_magnetic_stored_total_gj : float
            Total magnetic energy stored in the TF coils (GJ).
        stella_config_coilsurface : float
            Reference-configuration coil surface area (m^2).
        f_st_rmajor : float
            Major radius scale factor — from `StNewConfig`.
        r_coil_minor : float
            Coil minor radius (m) — from `StNewConfig`.
        stella_config_coil_rminor : float
            Reference-configuration coil minor radius (m).
        dx_tf_inboard_out_toroidal : float
            TF coil inboard leg toroidal thickness (m).
        len_tf_coil : float
            TF coil length (m).
        n_tf_coils : float
            Number of TF coils — from `StNewConfig`.
        b_plasma_toroidal_on_axis : float
            Toroidal magnetic field on axis (T).
        den_steel : float
            Steel density (kg/m^3).
        m_tf_coils_total : float
            Total TF coil mass (kg) — from the (not yet rewritten) TF coil model.
        dewmkg : float
            Cryostat mass (kg) — from the (not yet rewritten) blanket/shield model.
        """
        fncmass = 0.0  # Reactor core gravity support mass excluded for stellarators.
        gsmass = 0.0  # ? Not sure about this (original's own comment).

        # Previous scaling law for intercoil structure, kept as a reference
        # to the new model below, not really trusted (original's own
        # comment). F.C. Moon, J. Appl. Phys. 53(12) (1982) 9112.
        # Regression coefficients from Greifswald, March 2014.
        m_struc = 1.3483 * (1000.0 * e_tf_magnetic_stored_total_gj) ** 0.7821
        msupstr = 1000.0 * m_struc

        # Intercoil bolted-plates structure from the coil surface.
        intercoil_surface = (
            stella_config_coilsurface
            * f_st_rmajor
            * (r_coil_minor / stella_config_coil_rminor)
            - dx_tf_inboard_out_toroidal * len_tf_coil * n_tf_coils
        )

        # 0.18 m effective thickness, scaled with empirical 1.5 law; 5.6 T
        # reference point of Helias. From Schauer & Bykov, Helias 5-B
        # design (Nucl. Fus. 2013).
        aintmass = (
            0.18
            * (b_plasma_toroidal_on_axis / 5.6) ** 2
            * intercoil_surface
            * den_steel
        )

        # Very simple approximation for the gravity support, fits the
        # Helias 5b reactor design point.
        clgsmass = 0.2 * aintmass

        coldmass = m_tf_coils_total + aintmass + dewmkg

        return fncmass, gsmass, msupstr, aintmass, clgsmass, coldmass
