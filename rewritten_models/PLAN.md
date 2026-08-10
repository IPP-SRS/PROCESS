# Functional rewrite of PROCESS analysis models — plan

Status: **Stage 1 (proof of principle) in progress.** Do not scale to full
tokamak/stellarator batches until the three proof-of-principle rewrites
below are confirmed.

## 1. Context

This is an experiment, not (yet) a proposal to change PROCESS itself.
W.J. Rutten is writing a paper (Martins & Ning MDO framing) arguing that
PROCESS's optimisation architecture — a large mutable central `DataStructure`
threaded through ~60 model objects that read and write it by side effect —
is a structural problem, separate from and prior to the MDF/IDF architecture
work already underway in `~/projects/PROCESS_code_analysis`
(`IDF_EXPERIMENT_PLAN.md`). This rewrite is a companion probe: show, model
by model, what PROCESS looks like if every model is instead a pure function
with an explicit signature — no shared mutable state, inputs and outputs
named after the one global variable namespace PROCESS already has (just not
enforced as function boundaries).

`rewritten_models/` mirrors `process/models/`'s folder layout but contains
none of its code paths — nothing here is imported by, or imports from, the
real `process` package's runtime (`process.core`, `process.data_structure`,
`Model`, `Caller`, …). It exists purely to be read, and to be checked against
`process/models/` by hand for behavioural fidelity.

## 2. The template (as given)

Explicit model — `outputs = f(inputs)`:

```python
class model_name(ExplicitFunction):
    output_1: Output()
    output_2: Output()

    def __call__(self, input_1, input_2, ...):
        return ...
```

Implicit model — unknowns double as outputs, `__call__` becomes `residual`,
zero at the solution:

```python
class DiscA(ImplicitFunction):
    """u is determined by requiring u**2 - k*y to vanish. Nonlinear."""
    u = Output()
    def residual(self, u, y, k):
        return u * u - k * y
```

Rules given alongside the template:
- Names come from the global namespace already implicit in
  `process/data_structure/*.py`'s attribute names (PROCESS variable names
  are effectively globally unique already, even though they're nested under
  per-group dataclasses — that convention is exactly why names like
  `p_plasma_separatrix_mw` are as long and specific as they are).
- On a name clash, suffix with the owning class/model name.
- Never name anything `r_...` in an `ImplicitFunction` (reserved for the
  residual).
- No parametrized/config sub-objects — switches and options become plain
  input arguments (prefixed with the model name if the bare name would
  clash).

## 3. What "a model" means here

Per your instruction, model boundaries are **not** something I'm inventing —
they're taken directly from `~/projects/PROCESS_code_analysis
/dependency_analysis`, which has already walked PROCESS's call graph from
`Caller._call_models_once` and bucketed it into 48 tokamak nodes / 33
stellarator nodes (both include `Caller` itself as node 0, the orchestrator —
excluded here, see §5). A node is either:
- a **class model** (`class_model`): one PROCESS class, reached from a
  `self.models.<x>.<entry_method>()` call in `Caller`, or from another node —
  e.g. `PlasmaExhaust`, entry `calculate_separatrix_power`, in
  `models/physics/exhaust.py`;
- a **file model** (`file_model`): a bucket of module-level functions in one
  file that don't belong to any traced class — e.g. `superconductors_functions`
  in `models/superconductors.py`.

This tool was known-broken as of 2026-08-06 (3.5% variable coverage, 0
model↔model edges — see `dependency_analysis/docs/COVERAGE_INVESTIGATION.md`)
and has since been repaired and gated (`gates/gate1/report.md`, 11/11 pass,
100% DFS-reachable coverage, pinned to PROCESS `710a75c9`). The **node list**
(which classes/files count as models) was not the part that was broken —
that came from step 1 (call-graph discovery), not step 2 (the broken
variable-access parser) — so I'm treating the 48/33 node lists as reliable.
What I do *not* trust blindly is each node's exact `functions_to_parse` set
(F2/F3 in the coverage doc could still under-scope a node reached through
inheritance or a second entry point) — so for every model I read the actual
source file rather than trusting the tool's function list as complete.

Union of both graphs, `Caller` excluded: **60 models** (47 from the tokamak
graph + 13 stellarator-only; 19 are shared, mostly physics). Full lists:

<details><summary>Tokamak — 47 models (execution order from the tool)</summary>

| # | model | kind | file |
|---|---|---|---|
| 1 | PlasmaGeom | class | models/physics/plasma_geometry.py |
| 2 | Build | class | models/build.py |
| 3 | Physics | class | models/physics/physics.py |
| 4 | PlasmaCurrent | class | models/physics/plasma_current.py |
| 5 | PlasmaFields | class | models/physics/plasma_fields.py |
| 6 | PlasmaInductance | class | models/physics/physics.py |
| 7 | NeProfile | class | models/physics/profiles.py |
| 8 | PlasmaDensityLimit | class | models/physics/density_limit.py |
| 9 | PlasmaProfile | class | models/physics/plasma_profiles.py |
| 10 | TeProfile | class | models/physics/profiles.py |
| 11 | PlasmaBeta | class | models/physics/physics.py |
| 12 | PlasmaDiamagneticCurrent | class | models/physics/plasma_current.py |
| 13 | PlasmaBootstrapCurrent | class | models/physics/bootstrap_current.py |
| 14 | CurrentDrive | class | models/physics/current_drive.py |
| 15 | LowerHybrid | class | models/physics/current_drive.py |
| 16 | ElectronCyclotron | class | models/physics/current_drive.py |
| 17 | NeutralBeam | class | models/physics/current_drive.py |
| 18 | FusionReactionRate | class | models/physics/fusion_reactions.py |
| 19 | PlasmaConfinementTime | class | models/physics/confinement_time.py |
| 20 | PlasmaConfinementTransition | class | models/physics/l_h_transition.py |
| 21 | PlasmaExhaust | class | models/physics/exhaust.py |
| 22 | physics.fusion_reactions_functions | file | models/physics/fusion_reactions.py |
| 23 | physics.impurity_radiation_functions | file | models/physics/impurity_radiation.py |
| 24 | physics.radiation_power_functions | file | models/physics/radiation_power.py |
| 25 | ImpurityRadiation | class | models/physics/impurity_radiation.py |
| 26 | CICCSuperconductingTFCoil | class | models/tfcoil/superconducting.py |
| 27 | tfcoil.quench_functions | file | models/tfcoil/quench.py |
| 28 | engineering.materials_functions | file | models/engineering/materials.py |
| 29 | superconductors_functions | file | models/superconductors.py |
| 30 | PFCoil | class | models/pfcoil.py |
| 31 | CSCoil | class | models/pfcoil.py |
| 32 | CsFatigue | class | models/cs_fatigue.py |
| 33 | Pulse | class | models/pulse.py |
| 34 | Divertor | class | models/divertor.py |
| 35 | FirstWall | class | models/fw.py |
| 36 | engineering.ivc_functions_functions | file | models/engineering/ivc_functions.py |
| 37 | Shield | class | models/shield.py |
| 38 | VacuumVessel | class | models/vacuum.py |
| 39 | CCFE_HCPB | class | models/blankets/hcpb.py |
| 40 | Cryostat | class | models/cryostat.py |
| 41 | Structure | class | models/structure.py |
| 42 | Power | class | models/power.py |
| 43 | Vacuum | class | models/vacuum.py |
| 44 | Buildings | class | models/buildings.py |
| 45 | Availability | class | models/availability.py |
| 46 | WaterUse | class | models/water_use.py |
| 47 | Costs | class | models/costs/costs.py |

</details>

<details><summary>Stellarator-only additions — 13 models (not already in the tokamak list)</summary>

| model | kind | file |
|---|---|---|
| Stellarator | class | models/stellarator/stellarator.py |
| stellarator.density_limits_functions | file | models/stellarator/density_limits.py |
| stellarator.coils.calculate_functions | file | models/stellarator/coils/calculate.py |
| stellarator.coils.mass_functions | file | models/stellarator/coils/mass.py |
| stellarator.coils.quench_functions | file | models/stellarator/coils/quench.py |
| stellarator.coils.forces_functions | file | models/stellarator/coils/forces.py |
| stellarator.coils.coils_functions | file | models/stellarator/coils/coils.py |
| stellarator.build_functions | file | models/stellarator/build.py |
| stellarator.divertor_functions | file | models/stellarator/divertor.py |
| stellarator.preset_config_functions | file | models/stellarator/preset_config.py |
| Neoclassics | class | models/stellarator/neoclassics.py |
| physics.physics_functions | file | models/physics/physics.py |
| stellarator.heating_functions | file | models/stellarator/heating.py |

</details>

Note `PlasmaBeta`, `PlasmaInductance` are entry methods `run` on the
`Physics` *class itself* (`models/physics/physics.py`) — i.e. distinct
model nodes that happen to live in the same file/class as `Physics.run`. I
give them their own rewritten classes, not folded into a monolithic
`Physics` rewrite, since that's the tool's (and hence PROCESS's own call
graph's) model boundary.

## 4. Decisions made before starting (your answers)

1. **Reporting scope**: `output()` methods (the `po.ovarre`/`oheadr`
   report-writing side of every `Model`) are **excluded**. Only
   computational entry points (`run`, `calculate_*`, module-level functions)
   are rewritten. `output()` has no return value and isn't part of any data
   flow — it's a consumer of already-computed results, not a producer of
   any input another model needs.
2. **Composition layer**: **deferred.** `Caller._call_models_once` (the
   execution-order + outer VMCON/sub-solver-convergence driver) is not
   reproduced here. Each rewritten model is a standalone, independently
   readable/testable function; wiring 60 of them into a runnable pipeline
   (including the parts of `Caller` that aren't just a call sequence — the
   convergence loop around the whole thing) is a distinct, larger task for
   later, once the leaf models exist and are trusted.
3. **Namespace**: **fully isolated.** `process/data_structure/*.py` is never
   touched. `rewritten_models/_namespace.py` is a hand-maintained registry
   that mirrors it and, where necessary, extends it with new names — see
   §6. This means two sources of truth can drift; that's an accepted cost
   of keeping this experiment from touching the real codebase at all.
4. **Agent batching**: group by size/complexity for stages 4–5, not one
   agent per model — see §8.
5. **Model granularity**: a dependency-analysis node (§3) is a *file*
   boundary, not necessarily a *class* boundary. Where a node bundles
   genuinely independent input→output relationships (no shared inputs, no
   data flow between them — `PlasmaExhaust`'s four static methods are the
   worked example, see §7/§9), each becomes its own `ExplicitFunction`/
   `ImplicitFunction` class, co-located in one file named after the node.
   Rationale: the whole point of this rewrite is an honest data-flow graph;
   bundling unrelated calculations into one class because they happened to
   live in one PROCESS class would just re-create, inside the new
   abstraction, the exact problem (hidden/over-stated coupling) the rewrite
   exists to expose. One node → one file, but node → class is many-to-one
   only when the node's own outputs are actually coupled through shared
   inputs or intermediate values.

## 5. Scope boundary: what counts as "a model" to rewrite

**In scope**: the 60 nodes in §3 — their `run()`/`calculate_*`/module-level
computational methods only.

**Out of scope, explicitly**:
- `output()` reporting methods (decision 1).
- `Caller` itself and any composition/orchestration layer (decision 2).
- Anything inside a model that is itself calling *another* model node from
  §3 — that call becomes a call to the other node's rewritten class/function
  instead of being inlined. Rewritten models are allowed to depend on each
  other; they just never depend on `process.data_structure`.
- Fixing PROCESS bugs encountered along the way. If a rewrite surfaces one
  (see the aside in §9), it gets **noted, not fixed** — same rule your other
  project uses (`process-idf-refactor-paper` boundary conditions):
  PROCESS content is used as-is, behavioural fixes are a separate report.

## 6. Naming rules actually applied

1. If a global name for a quantity already exists in
   `process/data_structure/*.py` (regardless of which group dataclass it
   lives on — group membership is metadata, not part of the name), **reuse
   it verbatim**, including when the call site currently uses a different
   local parameter name than the true global one (this happened even in
   `exhaust.py` — see §9). The rename is a deliberate correction, called out
   in a comment.
2. If no such name exists (common for small pure helper functions whose
   inputs/outputs were never promoted to central-data attributes — e.g. most
   of `superconductors.py`), mint one in the same PROCES naming convention
   (`<quantity>_<subject>_<unit-ish suffix>`) and register it in
   `_namespace.py` with `origin="new"` plus a one-line reason.
3. On a genuine clash — two different models each want a name for a
   *different* quantity — suffix the newer one with the owning model's
   class name. `_namespace.declare()` raises `ValueError` automatically if
   this rule is skipped (same name, different `description`), so this is a
   real check, not just a convention on paper.
4. Switches/options (PROCESS's `i_*` integers selecting among correlations)
   are passed as plain input arguments using their existing global name —
   they're already global-namespace attributes in PROCESS (e.g.
   `i_density_limit`), so rule 1 usually applies directly; only prefix them
   if the same switch name is reused by two models for different meanings.
5. `ImplicitFunction.residual` never introduces a local or parameter named
   `r_...`.
6. Only the model's *interface* (declared `Output()`s and `__call__`/
   `residual` parameters) needs a global name. Internal intermediates stay
   as ordinary, undecorated local variables — turning every intermediate
   into a namespace entry would both balloon `_namespace.py` and misrepresent
   which quantities are actually shared data-flow versus scratch work.

## 7. Proof of principle (this stage)

You asked, correctly, whether `exhaust.py` alone would prove the approach
works on the *hard* cases, not just the easy one. It wouldn't — it's close
to being a pure-function set already (static methods, kwargs already named
after global attributes, no branching, no state). So this stage does three
models chosen to each stress a different real difficulty, not just the one
`exhaust.py` happens to be good at:

| model | file | what it tests |
|---|---|---|
| `PlasmaExhaust` | `models/physics/exhaust.py` | Baseline: does the mechanism (framework + namespace registry + isolation) work cleanly at all, on the simplest case. Cheap to do, so no reason to skip it — just not sufficient alone. |
| `PlasmaDensityLimit` | `models/physics/density_limit.py` | The single most common PROCESS pattern not exercised by exhaust: an `i_density_limit` switch (an `IntEnum`) selecting among 8 named correlations, all computed, one enforced; illegal-switch-value error handling; multiple named outputs from one entry point. This shape recurs across most of the physics models in §3 (confinement time, L-H transition, current drive, density limit all follow it) — validating it here is the highest-leverage single check before scaling out. |
| `current_sharing_rebco` / `jcrit_rebco` | `models/superconductors.py` | The `ImplicitFunction` half of the template, untested by the other two: `current_sharing_rebco` solves, via `scipy.optimize.newton`, for the temperature at which `jcrit_rebco(temperature, bfield) == j`. Maps directly onto the `DiscA` example in your brief, and is directly relevant to the IDF/MDF paper's interest in embedded sub-solvers. Also a real test of explicit↔implicit composition: the residual calls the rewritten `jcrit_rebco` `ExplicitFunction`. |

Together these cover: pure arithmetic, switch/enum-dispatched correlation
families (the dominant shape in the physics models), and embedded
root-finding — but **not** every difficulty category in §3. Known gaps,
deliberately not covered in stage 1, flagged so stage 4/5 batching (§8)
gives them a dedicated slot rather than being lumped in with "easy" models:

- **Stateful entry-via-`__init__`**: `FusionReactionRate`'s model-graph
  entry method is `__init__` itself, meaning instance state set up at
  construction is read by other methods later — closer to an object than a
  function. `__call__`/`residual` as given assumes a stateless call; this
  needs a translation decision I haven't made yet (candidate: treat the
  whole "construct, then call the methods that use its state" sequence as
  one `ExplicitFunction.__call__`, folding `__init__`'s body into it).
- **Very large single-node models**: `Physics.run` and
  `PlasmaConfinementTime` (single file, 4060 lines, ~30+ scaling-law
  branches) are far bigger than anything in this stage. `PlasmaDensityLimit`
  de-risks the *shape* of that problem but not its *scale*.
- **True cross-file coupling**: none of the three POC models read another
  §3 node's declared `Output()`s as an `Input` — real inter-model data flow
  (the actual point of this whole exercise) is only exercised in miniature
  here, via `current_sharing_rebco` calling `jcrit_rebco`.

## 8. Stages 4–5: batching for parallel agents

Once stage 1 is confirmed: batch the remaining 44 tokamak-only models (47
minus the 3 already done) and then the 13 stellarator-only models into
~8–12 agents per stage, grouped by size/complexity rather than 1:1 with
model nodes — a large monolith (`Physics`, `CCFE_HCPB`, `CICCSuperconductingTFCoil`,
`current_drive.py`'s 4 nodes) gets its own dedicated agent; several small
single-function-file nodes (e.g. `engineering.materials_functions`,
`engineering.ivc_functions_functions`) are grouped together. Each agent gets:
this plan, the specific node(s) from §3's tables, the naming rules in §6,
and instructions to append to `_namespace.py` (append-only within a batch;
I resolve any cross-agent clashes `_namespace.declare()` surfaces before the
batch is called done) and to flag anything matching a §7 "known gap" rather
than silently improvising a convention for it.

## 9. Findings along the way (log)

- **`exhaust.py`**: `PlasmaExhaust.calculate_radiation_fraction`'s parameter
  is named `p_plasma_heating_mw`, but every call site feeds it
  `physics.p_plasma_heating_total_mw` — the real global name is
  `p_plasma_heating_total_mw` (confirmed: `p_plasma_heating_mw` doesn't
  exist anywhere in `process/data_structure`). Renamed in the rewrite per
  naming rule 1; flagged, not fixed, in PROCESS itself.
- **`superconductors.py`**: `models/stellarator/coils/coils.py:127` calls
  `superconductors.jcrit_rebco(t_helium, b_max, 0)` — three positional
  arguments against a two-parameter function
  (`jcrit_rebco(temp_conductor, b_conductor)`). This branch
  (`i_tf_sc_mat == 6`, REBCO in a stellarator coil) would raise `TypeError`
  if ever executed. Out of scope to fix here (§5); worth a separate PROCESS
  bug report if you want to chase it — flagging since it's the kind of thing
  this exercise is well-placed to surface (a mismatched call site is far more
  visible once the callee has an explicit signature).

## 10. Open questions / room for feedback

*(nothing outstanding right now — filled in as you give feedback on the
stage 1 rewrites)*
