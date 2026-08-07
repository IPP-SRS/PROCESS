"""Track A IDF performance probe instrumentation.

Entirely inert unless the environment variable ``PROCESS_IDF_PROBE`` is set to
one of the modes below. With it unset, every hook in this module is a no-op and
PROCESS behaves byte-for-byte as baseline.

Modes
-----
off (default)
    No instrumentation at all.
baseline
    Unmodified control flow; records sweeps-per-``call_models`` and the calling
    phase (function evaluation vs FD gradient).
single_sweep
    ``Caller.call_models`` performs exactly ONE model sweep -- the idempotence
    loop is removed. This is the IDF-like evaluation.
single_sweep_debug
    As ``single_sweep``, but performs a second sweep afterwards purely to
    measure per-constraint lag drift. The FIRST sweep's values are returned, so
    the optimiser still sees true single-sweep behaviour. Timing from this mode
    is meaningless by construction.

Records are appended as JSON lines to ``PROCESS_IDF_PROBE_LOG`` if set.
"""

from __future__ import annotations

import json
import os
import time

MODE = os.environ.get("PROCESS_IDF_PROBE", "off").strip().lower()
if MODE in ("", "0", "off", "none", "false"):
    MODE = ""

_LOG_PATH = os.environ.get("PROCESS_IDF_PROBE_LOG") or ""

# Current evaluator phase: "func" (fcnvmc1), "grad" (fcnvmc2), or "other".
PHASE = "other"

# Counters
N_CALL_MODELS = 0
N_SWEEPS = 0
N_RETRIES = 0
_SWEEPS_THIS_CALL = 0

_records: list[dict] = []


def _emit(record: dict) -> None:
    _records.append(record)
    if _LOG_PATH:
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")


_CENSUS_CALLER = None
_CENSUS_S1: dict | None = None


def note_sweep() -> None:
    """Called once per ``_call_models_once`` executed inside ``call_models``."""
    global N_SWEEPS, _SWEEPS_THIS_CALL, _CENSUS_S1
    N_SWEEPS += 1
    _SWEEPS_THIS_CALL += 1
    if _CENSUS_CALLER is not None:
        # Snapshot after sweep 1 and after sweep 2; the diff is the lag that a
        # single-sweep (IDF) evaluation would carry.
        if _SWEEPS_THIS_CALL == 1:
            _CENSUS_S1 = _snapshot(_CENSUS_CALLER.data)
        elif _SWEEPS_THIS_CALL == 2 and _CENSUS_S1 is not None:
            _census_diff(_CENSUS_S1, _snapshot(_CENSUS_CALLER.data))
            _CENSUS_S1 = None


def note_retry(epsfcn: float) -> None:
    """Called when SolverHandler retries with an enlarged epsfcn (C6)."""
    global N_RETRIES
    N_RETRIES += 1
    if MODE:
        _emit({"kind": "retry", "n": N_RETRIES, "epsfcn": float(epsfcn)})


def _finish_call(objf, conf, wall: float, sweeps: int) -> None:
    global N_CALL_MODELS
    N_CALL_MODELS += 1
    _emit({
        "kind": "call",
        "i": N_CALL_MODELS,
        "phase": PHASE,
        "sweeps": sweeps,
        "wall": wall,
        "objf": float(objf),
    })


_SKIP_MODULES = {"numerics", "globals", "scan"}
_SKIP_FIELDS = {"ncalls", "nviter", "norm_objf"}

# path -> max relative change observed between sweep 1 and sweep 2
CENSUS: dict[str, dict] = {}


def _snapshot(data) -> dict:
    """Flatten DataStructure scalars (and array norms) to {path: float}."""
    import dataclasses

    import numpy as np

    out: dict[str, float] = {}
    for f in dataclasses.fields(data):
        if f.name in _SKIP_MODULES:
            continue
        mod = getattr(data, f.name, None)
        if mod is None or not dataclasses.is_dataclass(mod):
            continue
        for g in dataclasses.fields(mod):
            if g.name in _SKIP_FIELDS:
                continue
            try:
                v = getattr(mod, g.name)
            except Exception:
                continue
            key = f"{f.name}.{g.name}"
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[key] = float(v)
            elif isinstance(v, np.ndarray) and v.size and v.dtype.kind == "f":
                try:
                    out[key] = float(np.linalg.norm(np.nan_to_num(v)))
                except Exception:
                    pass
    return out


def _census_diff(before: dict, after: dict) -> None:
    for k, a in before.items():
        b = after.get(k)
        if b is None:
            continue
        denom = abs(a) if abs(a) > 1e-30 else 1.0
        rel = abs(b - a) / denom
        if rel == 0.0:
            continue
        sym = abs(b - a) / (abs(a) + abs(b) + 1e-300)
        e = CENSUS.setdefault(
            k, {"max_rel": 0.0, "max_sym": 0.0, "n_changed": 0, "example": None})
        e["n_changed"] += 1
        if sym > e["max_sym"]:
            e["max_sym"] = sym
        if rel > e["max_rel"]:
            e["max_rel"] = rel
            e["example"] = {"sweep1": a, "sweep2": b}


def call_models(caller, xc, m):
    """Replacement body for ``Caller.call_models`` when a probe mode is active.

    Returns ``(objf, conf)`` exactly like the original.
    """
    global _SWEEPS_THIS_CALL

    # Imported lazily: process.core.caller imports this module at import time,
    # so top-level imports of solver machinery would be circular.
    from process.core.solver import constraints  # noqa: PLC0415
    from process.core.solver.objectives import objective_function  # noqa: PLC0415

    _SWEEPS_THIS_CALL = 0
    t0 = time.perf_counter()

    if MODE in ("baseline", "census"):
        # Delegate to the real implementation; note_sweep() inside it counts.
        # In census mode note_sweep() also snapshots sweeps 1 and 2 and diffs
        # them, so the trajectory stays exactly the baseline one.
        global _CENSUS_CALLER
        _CENSUS_CALLER = caller if (MODE == "census" and PHASE == "func") else None
        objf, conf = caller._call_models_original(xc, m)
        _CENSUS_CALLER = None
        _finish_call(objf, conf, time.perf_counter() - t0, _SWEEPS_THIS_CALL)
        return objf, conf

    # ---- single sweep -------------------------------------------------
    caller._call_models_once(xc)
    note_sweep()
    objf = objective_function(caller.data.numerics.minmax, caller.data)
    conf, _, _, _, _ = constraints.constraint_eqns(m, -1, caller.data)

    if MODE == "single_sweep_debug":
        # One extra sweep purely to quantify lag drift. Return the FIRST values.
        caller._call_models_once(xc)
        note_sweep()
        objf2 = objective_function(caller.data.numerics.minmax, caller.data)
        conf2, _, _, _, _ = constraints.constraint_eqns(m, -1, caller.data)
        drift = []
        for j in range(len(conf)):
            a, b = float(conf[j]), float(conf2[j])
            denom = abs(a) if abs(a) > 1e-30 else 1.0
            drift.append({"j": j, "c1": a, "c2": b, "rel": abs(b - a) / denom})
        _emit({
            "kind": "drift",
            "i": N_CALL_MODELS + 1,
            "phase": PHASE,
            "objf1": float(objf),
            "objf2": float(objf2),
            "objf_rel": abs(objf2 - objf) / (abs(objf) if abs(objf) > 1e-30 else 1.0),
            "conf": drift,
        })

    _finish_call(objf, conf, time.perf_counter() - t0, _SWEEPS_THIS_CALL)
    return objf, conf


def summary() -> dict:
    """Aggregate counters and a sweeps-per-call histogram split by phase."""
    hist: dict[str, dict[int, int]] = {}
    walls: dict[str, float] = {}
    for r in _records:
        if r.get("kind") != "call":
            continue
        ph = r["phase"]
        hist.setdefault(ph, {})
        hist[ph][r["sweeps"]] = hist[ph].get(r["sweeps"], 0) + 1
        walls[ph] = walls.get(ph, 0.0) + r["wall"]
    return {
        "mode": MODE,
        "n_call_models": N_CALL_MODELS,
        "n_sweeps": N_SWEEPS,
        "n_retries": N_RETRIES,
        "sweeps_per_call_hist_by_phase": {
            ph: {str(k): v for k, v in sorted(d.items())} for ph, d in hist.items()
        },
        "wall_in_call_models_by_phase": walls,
        "census": dict(
            sorted(CENSUS.items(), key=lambda kv: -kv[1]["max_rel"])
        ),
        "census_n_entries": len(CENSUS),
    }
