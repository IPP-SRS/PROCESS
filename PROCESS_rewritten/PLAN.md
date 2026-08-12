# Functional rewrite of PROCESS analysis models — plan

Status: **Stage 1 (proof of principle) in progress.** Do not scale to full
tokamak/stellarator batches until the proof-of-principle rewrites below are
confirmed.

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
5. **Model granularity — REVISED, 2026-08-10, overrides the original
   decision 5 below.** **One rewritten model per original *method*, no
   further decomposition.** A dependency-analysis node (§3) is a *file*
   boundary; within it, every existing method (a static/instance method on
   the node's class, or a module-level function for a `file_model` node)
   becomes exactly one `ExplicitFunction`/`ImplicitFunction`, reproducing
   that method's own logic — including its own internal calls to sibling
   methods, translated into calls to *their* rewritten classes — without
   pulling any of it apart into further classes, and without merging two
   methods into one. Whether any given method's internals should be split
   further (or two methods merged) is an open question, deferred until
   there's a working set of models to look at — see §13.

   *Original decision (2026-08-06), now superseded — kept for the record,
   not as guidance*: where a node bundled genuinely independent
   input→output relationships (no shared inputs, no data flow between
   them), each was split into its own class regardless of original method
   boundaries, and inline expressions with more than one internal consumer
   were promoted to their own class. Reasoning was the same rationale
   given in §11 items 5/8 (an honest data-flow graph, avoid hidden coupling
   inherited from the original class boundary). You corrected this after
   seeing it applied to `density_limit.py` (11 classes for 2 original
   methods, plus 3 more invented for inline fragments) and
   `stellarator.py` (10 classes for 3 original methods) — it went further
   than "wrap as per the template" and started making judgment calls about
   the *right* decomposition, which is explicitly something to assess
   later, deliberately, with a full set of models to look at, not something
   to bake in ad hoc per model during stage 1.

   Naming convention under the revised rule: a rewritten class is named
   after its original method — either a PascalCase transliteration
   (`st_new_config` -> `StNewConfig`) or a clear descriptive noun close to
   the method name (`calculate_asdex_density_limit` -> `AsdexDensityLimit`,
   as already used before this revision) — both are fine, what matters is
   the structural rule (one method, one class), not the exact spelling.
   The one fixed exception: the node's own entry method (`run`, `__init__`,
   ...) takes the node's own *class* name instead of a transliteration of
   "run"/"init", since every `Model` subclass has one of those and it
   carries no information on its own (`PlasmaDensityLimit.run` ->
   `PlasmaDensityLimit`).

## 5. Scope boundary: what counts as "a model" to rewrite

**In scope**: the 60 nodes in §3 — their `run()`/`calculate_*`/module-level
computational methods only.

**Out of scope, explicitly**:
- `output()` reporting methods (decision 1) — **but narrowly**: this
  excludes the literal print/format calls (`po.ovarre`, `po.oheadr`, ...),
  not every computation that happens to feed them. Corrected after stage 1
  (originally read too broadly — see §11 item 4): a real computed quantity
  stays in scope and gets its own model even if, in the original, its only
  current reader is an excluded `output()` block. Only reproduce the print
  statement's *absence*, not its input's absence too. A quantity like this
  may become an actual functional output later under a different
  optimiser/reporting architecture regardless of who reads it in PROCESS
  today.
- `Caller` itself and any composition/orchestration layer (decision 2).
- Anything inside a model that is itself calling *another* model node from
  §3 — that call becomes a call to the other node's rewritten class/function
  instead of being inlined. Rewritten models are allowed to depend on each
  other; they just never depend on `process.data_structure`.
- Fixing PROCESS bugs encountered along the way. If a rewrite surfaces one
  (see §10), it gets **noted, not fixed** — same rule your other project
  uses (`process-idf-refactor-paper` boundary conditions): PROCESS content
  is used as-is, behavioural fixes are a separate report.

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
after global attributes, no branching, no state). So this stage covers four
models/slices chosen to each stress a different real difficulty, not just
the one `exhaust.py` happens to be good at:

| model | file | what it tests |
|---|---|---|
| `PlasmaExhaust` | `models/physics/exhaust.py` | Baseline: does the mechanism (framework + namespace registry + isolation) work cleanly at all, on the simplest case — 4 original static methods, 4 rewritten classes, already 1:1 under §4 decision 5. Cheap to do, so no reason to skip it — just not sufficient alone. |
| `PlasmaDensityLimit` | `models/physics/density_limit.py` | The single most common PROCESS pattern not exercised by exhaust: an `i_density_limit` switch (an `IntEnum`) selecting among 8 named correlations, all computed, one enforced; illegal-switch-value error handling. 11 original methods -> 11 rewritten classes (8 correlations + `CalculateDensityLimit` + `GetDensityLimitValue` + the entry method `PlasmaDensityLimit`), each calling the others exactly where the original does. This shape recurs across most of the physics models in §3 (confinement time, L-H transition, current drive, density limit all follow it) — validating it here is the highest-leverage single check before scaling out. |
| `current_sharing_rebco` / `jcrit_rebco` | `models/superconductors.py` | The `ImplicitFunction` half of the template, untested by the other two: `current_sharing_rebco` solves, via `scipy.optimize.newton`, for the temperature at which `jcrit_rebco(temperature, bfield) == j`. Maps directly onto the `DiscA` example in your brief, and is directly relevant to the IDF/MDF paper's interest in embedded sub-solvers. Also a real test of explicit↔implicit composition: the residual calls the rewritten `jcrit_rebco` `ExplicitFunction`. 2 original methods -> 2 rewritten classes. |
| `Stellarator` geometry-scaling slice (`st_new_config`+`st_geom`+`st_strc`) | `models/stellarator/stellarator.py` | Stellarator-only pattern: config-object-driven scaling with real chained coupling inside each method (`aspect`→`rminor`→`f_st_rminor`; `f_st_rmajor`→coil radii, all within `StNewConfig`; `aintmass`→`clgsmass`/`coldmass` within `StStrc`) — 3 original methods -> 3 rewritten classes, each bundling every output the corresponding original method has. Also the first case of a node that's mostly composition-in-disguise (`run()`/`output()`, excluded — §11 item 1) and of a call belonging to a *different* node (`load_stellarator_config` — §11 item 2). |

Together these cover: pure arithmetic, switch/enum-dispatched correlation
families (the dominant shape in the physics models), embedded root-finding,
and config-driven chained geometry scaling — but **not** every difficulty
category in §3. Known gaps, deliberately not covered in stage 1, flagged so
stage 4/5 batching (§9) gives them a dedicated slot rather than being
lumped in with "easy" models:

- **Stateful entry-via-`__init__`**: `FusionReactionRate`'s model-graph
  entry method is `__init__` itself, meaning instance state set up at
  construction is read by other methods later — closer to an object than a
  function. `__call__`/`residual` as given assumes a stateless call; this
  needs a translation decision I haven't made yet (candidate: treat the
  whole "construct, then call the methods that use its state" sequence as
  one `ExplicitFunction.__call__`, folding `__init__`'s body into it).
- **Very large single-node models**: `Physics.run`, `PlasmaConfinementTime`
  (4060 lines, ~30+ scaling-law branches), and `Stellarator`'s own
  `st_fwbs` (~1200 lines)/`st_phys` (~570 lines) are far bigger than
  anything actually rewritten in this stage. `PlasmaDensityLimit`/
  `StNewConfig` de-risk the *shape* of that problem (switch dispatch,
  chained scaling) but not its *scale* — and under the revised §4 decision
  5, a method that large becomes one very large class, unless/until §13's
  decomposition-necessity assessment says otherwise.
- **Cross-*node* Output→Input coupling** (one rewritten node's declared
  `Output()` consumed as another rewritten node's `Input`, the actual point
  of this whole exercise) is still only exercised in miniature, via
  `current_sharing_rebco` calling `jcrit_rebco` — both in the same file.
  Stellarator's `StStrc` (specifically its `coldmass` output) takes
  `m_tf_coils_total`/`dewmkg` as inputs whose *true* producers (the TF coil
  model, the blanket/shield model) aren't rewritten yet, so those stay
  plain inputs for now rather than calls into another rewritten class —
  real multi-file node-to-node wiring is still untested.

## 8. Numerical equivalence testing (mandatory for every model)

A rewrite that hasn't been checked against the original is a guess, not a
result — this applies to every one of the 60 models, not just the stage-1
proof of principle. **Every rewritten model must ship with a test in
`rewritten_models/idempotence_tests/` before it counts as done.** ("Idempotence
tests" is the requested folder name; what they actually check is *numerical
equivalence* between the rewrite and the original, not idempotence in the
strict sense.)

Shared harness: `idempotence_tests/_harness.py` — read its module docstring
for the full rationale. In short, every test combines two things, applied
the same way across all of stage 1, 4, and 5:

1. **A random sweep**, `random_samples(ranges, n, seed)` — typically
   `n=300`, always a fixed explicit `seed` (reproducible, not "whatever
   numpy's default state happens to be"). `ranges` must bracket a
   *physically realistic* span for each input (document the reasoning, not
   just the numbers) — wide enough to stress the arithmetic, not so wide
   the correlation is being evaluated somewhere physically meaningless.
   Comparison is **exact equality**, not a tolerance — these are meant to
   be line-for-line translations, and every stage-1 rewrite achieved exact
   equality across its whole sweep. A tolerance would hide the class of bug
   (reordered ops, `np.sqrt` swapped for `math.sqrt`, a dropped term) this
   testing exists to catch.
2. **Explicit branch/edge-case coverage** — read the original source, list
   every conditional branch and error path by hand, and add one hand-picked
   case landing in each (including ones a random sweep is very unlikely to
   hit, like an exact switch-domain boundary or a `denom == 0` guard). Say,
   in the test file's docstring, concretely which branch each case covers.

For an `ImplicitFunction`, one more layer: `assert_residual_matches_explicit`
checks the residual formula itself, pointwise, against an independently
written reference expression — not by re-deriving it via the rewritten
`ExplicitFunction` it happens to call, which would let a shared bug hide on
both sides. `assert_roots_match_via_solver` then separately confirms that
solving the rewritten residual with the same solver call as the original
converges to the same root. Two different residual formulas can converge to
the same root under a forgiving solver, so root-matching alone isn't
sufficient — see `test_superconductors.py` for the worked example of both
layers together.

Requires the real `process` package: run with
`conda run -n PROCESS_env python -m pytest rewritten_models/idempotence_tests/`.
Every test module calls `require_process()` first so running outside
`PROCESS_env` skips with a clear reason instead of an opaque import error.

Every stage 4/5 agent gets this section verbatim as part of its brief, and
its work isn't done until its models' `idempotence_tests` pass.

## 9. Stages 4–5: batching for parallel agents

Once stage 1 is confirmed: batch the remaining 44 tokamak-only models (47
minus the 3 already done) and then the 13 stellarator-only models into
~8–12 agents per stage, grouped by size/complexity rather than 1:1 with
model nodes — a large monolith (`Physics`, `CCFE_HCPB`, `CICCSuperconductingTFCoil`,
`current_drive.py`'s 4 nodes) gets its own dedicated agent; several small
single-function-file nodes (e.g. `engineering.materials_functions`,
`engineering.ivc_functions_functions`) are grouped together. "Size" here
means the original's line count / method count directly, now that §4
decision 5 fixes the mapping at one class per original method — an agent's
job per model is closer to mechanical translation (wrap each method, wire
calls between the resulting classes exactly as the original wires calls
between methods) than the judgment-heavy decomposition stage 1 initially
did, which should make batches more predictable to size. Each agent gets:
this plan, the specific node(s) from §3's tables, the naming rules in §6,
the testing methodology in §8, the judgment-call patterns in §11 (read
before starting, not after getting stuck — several of them are easy to miss
on a first read of a new model), and instructions to append to
`_namespace.py` (append-only within a batch; I resolve any cross-agent
clashes `_namespace.declare()` surfaces before the batch is called done)
and to flag anything matching a §7 "known gap" rather than silently
improvising a convention for it.

**Escalation protocol.** Not everything an agent hits belongs in the §10
bug log or the §11 judgment-call log — those are for things that fit within
this plan's existing rules, however non-obvious. Some things won't: a model
that can't be expressed as `ExplicitFunction`/`ImplicitFunction` without
breaking purity in a way §7's known gaps don't already cover; an
equivalence test (§8) that fails for a reason that isn't a translation bug
but a sign the *exact-equality standard itself* doesn't hold here (e.g. the
original is genuinely nondeterministic); a namespace clash §6 rule 3's
suffixing doesn't cleanly resolve; a dependency-analysis node boundary (§3)
that looks wrong for a specific model. When an agent hits something in this
category, it must **not** silently invent and apply its own precedent —
with several agents running in parallel, that's how the rewrite ends up
inconsistent in ways nobody notices until much later. Instead: stop, write
up what broke and why none of the existing rules resolve it, and put that
at the top of its final report to me under its own clearly marked heading
(not buried in prose describing otherwise-normal progress). I bring these
to you before considering the batch done, rather than letting an agent's
one-off resolution quietly become the de facto rule for everyone after it.

## 10. Findings along the way (log)

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
- **`density_limit.py`**: `PlasmaDensityLimit.calculate_density_limit`
  computes the switch-enforced density limit value *twice* — once as its
  own second return value, once (independently, via a dict lookup on the
  array) inside `get_density_limit_value`. `run()` only ever calls the
  latter; the former's return value is assigned to `_` and never read.
  Provably dead code, not just redundant-looking — confirmed by tracing
  every caller of `calculate_density_limit` (`run()` is the only one).
  Not fixed in PROCESS itself (§5); the rewrite (`CalculateDensityLimit`)
  implements the computation once, see §11 item 3.

## 11. Non-trivial rewrite judgment calls (log)

This is **not** the PROCESS-bug list — that's §10. This is a log of places
where translating a model into the template required a real judgment call,
not a mechanical rename — kept so stage 4/5 agents recognize the pattern
when they hit it again (most of these will recur), instead of either
missing it or re-deriving the reasoning from scratch. Read before starting
a new model, not after getting stuck on one.

1. **A "model" node can secretly be a composition layer.** `Stellarator`'s
   `run()`/`output()` are almost entirely a call sequence into ~10 *other*
   models (`self.costs.run()`, `st_heat(...)`, `self.power.tfpwr(...)`, ...)
   plus a documented double-call convergence pattern the original's own
   comment admits is a hack ("should be integrated to avoid this double
   call"). This is `Caller`-shaped, not model-shaped — out of scope per §5
   decision 2, however class-model-y it looks in the dependency graph. Read
   a node's *whole* set of methods before rewriting any of them; if most of
   a node's body is calls into other nodes rather than arithmetic, that
   part is orchestration, not computation.

2. **A call inside your node might actually belong to a different node.**
   `Stellarator.st_new_config`'s call to `load_stellarator_config` is
   dependency-analysis node `stellarator.preset_config_functions`, a
   *different* node from `Stellarator` itself, just imported and called
   from within it. Don't inline or reimplement another node's logic —
   treat its outputs as already-computed plain inputs (naming rule 4) and
   say so in a comment, the same way switches/config are handled.

3. **Recognize provably-dead computation, and don't reproduce it — but log
   it as a PROCESS bug, not just a rewrite footnote.** `PlasmaDensityLimit.
   calculate_density_limit` computes its own "enforced value" as a second
   return value that its only caller (`run()`) never reads
   (`get_density_limit_value` recomputes the identical thing from the array
   instead). The rewrite implements it once. "Faithful to the original"
   means faithful to its *observable behaviour*, not to redundant internal
   computation nothing reads — but this isn't only a rewrite note: dead
   code in PROCESS itself is a defect (§10), same category as the other
   findings there, not just something noted in passing in a module
   docstring.

4. **`output()` being out of scope does not mean its *inputs* are out of
   scope — reproduce them anyway, corrected after stage 1.** The original
   framing here was "check whether anything else reads it before
   reconstructing it" (`nd_plasma_electron_max_array` in density_limit.py,
   `msupstr`/`m_struc` in stellarator.py both looked, at first read, like
   pure reporting artefacts with no other consumer). That framing was
   wrong: a real computed quantity stays in scope regardless of who reads
   it *today* in PROCESS — only the literal `po.ovarre`/`oheadr` print call
   itself has no return value and doesn't fit the template. Both are now
   reproduced — `nd_plasma_electron_max_array` as an output of
   `CalculateDensityLimit` (initially, before §4 decision 5's revision,
   its own class, `DensityLimitCorrelationArray`; folded back in once
   decomposition below the method level was reversed), `msupstr` as an
   output of `StStrc` (initially its own class,
   `AlternativeIntercoilStructureMassScaling`, same fold-back) — even
   though, in PROCESS as it stands, nothing but the excluded print reads
   them — a different optimiser/reporting architecture might read either
   as a genuine functional output later, and there's no cost to keeping
   that possible.
   Applying this retroactively: **re-check every model already rewritten**
   for anything excluded on the old "only output() reads this" reasoning,
   not just new ones going forward. Done for the other three stage-1
   models: `exhaust.py`'s `output()` only reads values that are already
   real `Output()`s of the 4 rewritten classes, nothing computed solely for
   print; `superconductors.py` has no `Model` subclass / `output()` at all
   (plain module functions) — nothing to find in either.

5. **SUPERSEDED 2026-08-10 — kept for the record, not as guidance; see §4
   decision 5's revision.** *Promote a private local to its own node
   exactly when more than one sibling needs it, not before.* `p_perp` in
   the original `calculate_density_limit` was a plain local, recomputed
   inline wherever needed. Once split into independent correlation classes
   (under the original, now-superseded decision 5), 3 of them needed it —
   at that point it stopped being "scratch work" (naming rule 6) and became
   real shared data flow, with its own name and its own tiny producing
   model (`PerpendicularPowerDensity`). Under the revised decision 5, this
   doesn't arise the same way: `p_perp` is back to being a plain local
   inside `CalculateDensityLimit`, since `calculate_density_limit` is one
   method and stays one class.

6. **Anticipate naming clashes from not-yet-rewritten siblings — don't wait
   to be told by `_namespace.declare()`.** `superconductors.py`'s
   `jcrit_rebco` outputs were pre-emptively named `j_crit_rebco`,
   `b_c20max_rebco`, `temp_c0max_rebco` even though none of that file's
   ~10 other superconductor correlations (`itersc`, `gl_nbti`, `bi2212`,
   ...) have been rewritten yet — because they're siblings in the *same*
   dependency-analysis node and will each want a "critical field"/"critical
   temperature" of their own. Skim a node's full sibling list (not just the
   function you're rewriting right now) before picking a name for anything
   generic-sounding.

7. **Reusing a name as both an Output and an Input is the whole point of
   `ImplicitFunction`, and a red flag everywhere else.** Stellarator's
   `aspect` is conditionally either kept from an existing value or
   overwritten from a config default — the existing value is a genuine
   *different* role from the computed output, so it's named
   `aspect_iterated_value` on the input side, keeping `aspect` itself as
   the Output's true global name. Don't reuse an Output's bare name for an
   unrelated same-model Input just because they're "the same PROCESS
   variable" outside an `ImplicitFunction`'s unknown-as-parameter pattern.

8. **SUPERSEDED 2026-08-10 — kept for the record, not as guidance; see §4
   decision 5's revision.** *A node's outputs need real dependency tracing
   before deciding the split, not a guess from "these were separate
   lines."* `st_new_config`'s 11 original outputs required tracing which
   ones share intermediates (`aspect` → `rminor`/`eps` → `f_st_rminor`;
   `f_st_rmajor` → `r_coil_major`/`r_coil_minor`) before splitting — 2 of 11
   (`n_tf_coils`, `f_coil_shape`) turned out fully independent and got
   their own classes under the original, now-superseded decision 5; the
   rest were bundled as a genuinely coupled chain. Under the revised
   decision 5, none of this tracing happens: `st_new_config` is one method,
   so all 12 of its outputs (the 11 above, plus `eps` which the
   independent-computation version also bundled in) stay on one class
   (`StNewConfig`) regardless of which of them share intermediates. The
   dependency-tracing skill demonstrated here isn't wasted — it's exactly
   what "assess the necessity of further decomposition" (§13) will need
   later — but it no longer decides class boundaries during stage 1/4/5.

9. **Testing an instance method doesn't require fighting through the real
   dependency-injection graph.** `Stellarator.__init__` takes 12 injected
   models that `st_new_config`/`st_geom`/`st_strc` never touch — building a
   real one via the full `Caller`/fixture graph would be disproportionate.
   `Class.__new__(Class)` plus attaching a fresh `process.core.model.DataStructure()`
   to `.data` is enough whenever the method under test only reads/writes
   `self.data` (true of every `Model.run`-shaped method so far) — see
   `idempotence_tests/stellarator/test_stellarator.py`'s `_make_stellarator()`.
   Reusable for every other `class_model` node with a heavy constructor.

## 12. Stage 1 verification

**Layout**: `rewritten_models/` and `idempotence_tests/` live side by side
under `PROCESS_rewritten/`, both at the PROCESS repo root
(`PROCESS_rewritten/rewritten_models/`, `PROCESS_rewritten/idempotence_tests/`).
`PROCESS_rewritten/conftest.py` puts `PROCESS_rewritten/` itself on
`sys.path` so both resolve as top-level packages (`rewritten_models.physics.exhaust`,
`idempotence_tests._harness`, ...) regardless of pytest's rootdir, which is
still the PROCESS repo root (`pyproject.toml` lives there).

All rewrites are checked by `PROCESS_rewritten/idempotence_tests/` (§8's
methodology — random sweeps + explicit branch coverage, exact equality),
run against the live `process` package. Current status, **27/27 passing**
(count reflects the §4 decision 5 revision — density_limit.py/stellarator.py
were restructured from independent-computation classes to one-class-per-
original-method, so both the rewrites and their tests were rewritten; see
§11 item 4 for the two classes reproduced despite feeding only the excluded
`output()` in the original, now `CalculateDensityLimit.nd_plasma_electron_max_array`
and `StStrc.msupstr`):

| test file | model(s) | sweep size | branch/edge cases covered |
|---|---|---|---|
| `idempotence_tests/physics/test_exhaust.py` | `PlasmaExhaust`'s 4 classes (4 original methods) | 300/class | zero-heating-power guard in `RadiationFraction` |
| `idempotence_tests/physics/test_density_limit.py` | `PlasmaDensityLimit`'s 11 classes (11 original methods: 8 correlations + `CalculateDensityLimit` + `GetDensityLimitValue` + `PlasmaDensityLimit`) | 300/correlation; 40×8 switch values for the full top-level sweep | `denom<=0` guard (`JetEdgeRadiationDensityLimit`); all 8 switch values exhaustively at every level (`CalculateDensityLimit`, `GetDensityLimitValue`, `PlasmaDensityLimit`); illegal-switch error path at every level |
| `idempotence_tests/test_superconductors.py` | `jcrit_rebco`/`current_sharing_rebco`, 2 classes (2 original functions) | 300 (+50 for the root-solve check) | temp-vs-`temp_c0max_rebco`, field-too-high, out-of-validity-range branches; residual formula pointwise vs. solved-root layers |
| `idempotence_tests/stellarator/test_stellarator.py` | `Stellarator` geometry-scaling slice, 3 classes (`StNewConfig`, `StGeom`, `StStrc` — 3 original methods) | 300 (150×2 for `StNewConfig`) | `is_aspect_iteration_variable` branch, both sides, full random sweep each side (not just one hand-picked case per side) |

Run: `conda run -n PROCESS_env python -m pytest PROCESS_rewritten/idempotence_tests/ -v`.

One bug caught by this process, in the *test*, not the rewrite: an early
version of `test_tf_coil_count_from_config_random_sweep` wrapped the
original's `st_new_config()` call in a bare `try/except: pass` (reasoning:
"only n_tf_coils is under test, ignore errors from the rest") — which
silently masked a `ZeroDivisionError` (missing `stella_config_aspect_ref`
input → `aspect=0.0` → `rminor = rmajor/aspect` raises, *before* the
`n_tf_coils` line even executes) and let the test pass against a stale
default value instead of a real computed one. Caught by manually inspecting
a passing-but-suspicious result, not by the harness itself — worth having
future agents remember: a swallowed exception during setup is exactly the
kind of thing that makes a numerical-equivalence test lie. Don't
`except: pass` around a call to the code under test.

(An earlier, pre-harness pass hand-checked `exhaust`/`density_limit`/
`superconductors` with ad hoc scratch scripts before this suite existed;
superseded by the table above, not kept.)

## 13. Open questions / room for feedback

- **Deferred: necessity of further decomposition below the method level.**
  §4 decision 5 (revised) fixes granularity at one class per original
  method for now. Whether any of these classes should later be split
  further — and by what rule, if the original independent-computation
  approach (§11 items 5/8, superseded) isn't it — is explicitly not decided
  yet. Revisit once stage 4/5 produces a fuller set of models to assess
  against, per your instruction.
