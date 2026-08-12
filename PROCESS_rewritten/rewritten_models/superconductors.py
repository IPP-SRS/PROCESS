"""Functional rewrite of two functions from ``process/models/superconductors.py``.

Original dependency-analysis node: ``superconductors_functions`` (file
model, `models/superconductors.py`) — a bucket of ~10 independent
superconductor critical-surface correlations (`itersc`, `gl_nbti`, `bi2212`,
`jcrit_rebco`, `hijc_rebco`, `western_superconducting_nb3sn`, ...) plus
`current_sharing_rebco`, which solves one of them for a temperature. This
proof-of-principle stage rewrites only the REBCO pair
(`jcrit_rebco` / `current_sharing_rebco`) — chosen specifically because
`current_sharing_rebco` is the cleanest embedded root-find in the physics
models (PLAN.md §7), and is the only thing in this stage exercising
``ImplicitFunction``. The rest of this file's correlations are left for
stage 4 (PLAN.md §8); see the naming note below for why that matters now.

Naming note (PLAN.md §6, rule 3): none of `jcrit_rebco`'s outputs exist in
`process/data_structure` — PROCESS never promotes a single material's
critical current density/field/temperature to a central-data attribute,
because ~10 different correlations in this same file each produce an
analogous-but-different value (Nb3Sn's critical field is not REBCO's).
Naming them generically (`j_critical`, `b_c20max`, `temp_c0max` — the
original's own local parameter/return names) would silently clash the
moment `itersc` or another sibling correlation is rewritten in stage 4 and
also wants to call its "critical field" `b_c20max`. So these are minted
*already* suffixed with `_rebco`, pre-empting that clash rather than fixing
it up later.
"""

from __future__ import annotations

import logging

from rewritten_models._framework import ExplicitFunction, ImplicitFunction, Output
from rewritten_models._namespace import declare

logger = logging.getLogger(__name__)

# --- shared namespace declarations --------------------------------------

declare(
    "b_conductor",
    description="Magnetic field at the superconductor",
    unit="T",
    origin="new",
    defining_model=None,
    notes=(
        "Generic input shared by every superconductor correlation in this file "
        "(not itself an output of any of them, so no clash risk from reuse)."
    ),
)
declare(
    "j_conductor",
    description="Operating (actual) current density in the superconductor, "
    "to be compared against a material's critical current density",
    unit="A/m^2",
    origin="new",
    defining_model=None,
    notes="Generic input, reused across every material's current-sharing-temperature model.",
)
declare(
    "j_crit_rebco",
    description="Critical current density of a REBCO 2nd-generation HTS superconductor",
    unit="A/m^2",
    origin="new",
    defining_model="JcritRebco",
)
declare(
    "is_valid_rebco",
    description="Whether temp_conductor/b_conductor are within jcrit_rebco's validity range",
    unit="",
    origin="new",
    defining_model="JcritRebco",
)
declare(
    "b_c20max_rebco",
    description="REBCO upper critical field at zero temperature and strain (material constant)",
    unit="T",
    origin="new",
    defining_model="JcritRebco",
)
declare(
    "temp_c0max_rebco",
    description="REBCO critical temperature at zero field and strain (material constant)",
    unit="K",
    origin="new",
    defining_model="JcritRebco",
)
declare(
    "temp_current_sharing_rebco",
    description="Temperature at which REBCO's critical current density equals j_conductor",
    unit="K",
    origin="new",
    defining_model="CurrentSharingTemperatureRebco",
)


class JcritRebco(ExplicitFunction):
    """Critical current density of a REBCO 2nd-generation HTS superconductor.

    Original: ``jcrit_rebco`` (module-level function).

    Notes
    -----
    Validity range: 4.2 K <= temp_conductor <= 72.0 K; 0.0 T <= b_conductor
    <= 15.0 T for temp_conductor < 65 K, else 0.0 T <= b_conductor <= 11.5 T.
    ``is_valid_rebco`` is False, and an error logged, outside this range —
    the original still returns a (deliberately unphysical, e.g. negative)
    value rather than raising, and this preserves that.
    """

    j_crit_rebco = Output()
    is_valid_rebco = Output()
    b_c20max_rebco = Output()
    temp_c0max_rebco = Output()

    def __call__(
        self, temp_conductor: float, b_conductor: float
    ) -> tuple[float, bool, float, float]:
        """
        Parameters
        ----------
        temp_conductor : float
            Superconductor temperature (K).
        b_conductor : float
            Magnetic field at the superconductor (T).
        """
        temp_c0max_rebco = 90.0
        b_c20max_rebco = 132.5

        C = 1.82962e8  # scaling constant
        p = 0.5875
        q = 1.7
        alpha = 1.54121
        beta = 1.96679
        oneoveralpha = 1 / alpha

        is_valid_rebco = True
        if (temp_conductor < 4.2) or (temp_conductor > 72.0):
            is_valid_rebco = False
        if temp_conductor < 65:
            if (b_conductor < 0.0) or (b_conductor > 15.0):
                is_valid_rebco = False
        elif (b_conductor < 0.0) or (b_conductor > 11.5):
            is_valid_rebco = False

        if not is_valid_rebco:
            logger.error(
                "jcrit_rebco: input out of range\ntemperature: %s\nField: %s",
                temp_conductor,
                b_conductor,
            )

        if temp_conductor < temp_c0max_rebco:
            birr = b_c20max_rebco * (1 - temp_conductor / temp_c0max_rebco) ** alpha
        else:
            # temp above critical temp: ensure result is real but negative.
            birr = b_c20max_rebco * (1 - temp_conductor / temp_c0max_rebco)

        if b_conductor < birr:
            factor = (b_conductor / birr) ** p * (1 - b_conductor / birr) ** q
            j_crit_rebco = (C / b_conductor) * (birr**beta) * factor
        else:
            # Field too high: ensure result is real but negative, varying with temperature.
            temp_critical_at_b = temp_c0max_rebco * (
                1 - (b_conductor / b_c20max_rebco) ** oneoveralpha
            )
            j_crit_rebco = -(temp_conductor - temp_critical_at_b)

        return j_crit_rebco, is_valid_rebco, b_c20max_rebco, temp_c0max_rebco


class CurrentSharingTemperatureRebco(ImplicitFunction):
    """Current sharing temperature for a REBCO 2nd-generation HTS superconductor.

    Original: ``current_sharing_rebco`` (module-level function), which wraps
    this exact root-find in a call to ``scipy.optimize.newton`` — the
    solver call itself is composition-layer work (PLAN.md §5), out of scope
    here; this class only fixes the interface being solved: find
    ``temp_current_sharing_rebco`` such that REBCO's critical current
    density at that temperature equals the operating current density
    ``j_conductor``.
    """

    temp_current_sharing_rebco = Output()

    def residual(
        self, temp_current_sharing_rebco: float, b_conductor: float, j_conductor: float
    ) -> float:
        """
        Parameters
        ----------
        temp_current_sharing_rebco : float
            Candidate current sharing temperature (K) — the unknown.
        b_conductor : float
            Magnetic field at the superconductor (T).
        j_conductor : float
            Operating current density in the superconductor (A/m^2).
        """
        j_crit_rebco, _is_valid_rebco, _b_c20max_rebco, _temp_c0max_rebco = JcritRebco()(
            temp_conductor=temp_current_sharing_rebco, b_conductor=b_conductor
        )
        return j_crit_rebco - j_conductor
