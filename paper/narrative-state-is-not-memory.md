# Narrative State Is Not Memory: A Three-Axis Design Space and the NAMS Architecture for Persona Storytelling Systems

**Working paper / preprint format (SCI-style).** Version 1.0 — August 2026.

---

## Abstract

Persona large language model (LLM) platforms have quietly become the highest-dwell-time consumer
application category of the generative AI era. Field data from the three most durable deployments —
zeta (Scatter Lab), Character.AI, and Talkie/Xingye (MiniMax) — show per-user daily engagement of
70 to 150 minutes sustained over multiple years, exceeding mainstream entertainment platforms.
Yet the research literature that these systems draw on frames their central difficulty as a
**memory** problem: how faithfully can a system recall and re-inject the past. We argue this framing
is category-incorrect. Using a comparative analysis of three currently prominent research lines —
*Nested Learning/HOPE* (parametric multi-timescale memory), *ALMA* (meta-learned agentic memory
design), and *SteeM* (user-controllable memory dependence) — we show that all three optimize
**fidelity of recall**, whereas the empirical failure mode of long-horizon persona storytelling is
**anchoring**: high-fidelity recall drives narrative predictability, predictability drives
disengagement. We formalize this as the **Narrative Vitality Frontier**, a concave relationship
between memory dependence δ and sustained engagement admitting an optimum δ\*(τ) that is itself a
function of relationship age τ. We then propose **NAMS (Narrative-Adaptive Memory Stack)**, a
three-layer architecture that separates (I) a slow-updating *Persona Core* enforcing identity
invariants, (II) a meta-learned *Narrative State* schema carrying narratological rather than factual
variables (arc position, open threads, relational stage, tension), and (III) a learned *Steering
Controller* that sets δ automatically from interaction signals platforms already collect — regeneration,
edit, and continuation events. We contribute a metric suite (PCS, NNI, TAR, CAR), a longitudinal
benchmark design (PERSONA-ARC), four falsifiable predictions, and a constrained objective that
subordinates engagement maximization to dependency and minor-safety constraints. The central claim
is that the field's next advance will not come from remembering more, but from **deciding what a
story should do with what it remembers**.

**Keywords**: persona LLM, interactive narrative, long-term memory, continual learning, memory
anchoring, human–agent interaction, preference optimization, AI safety

---

## 1. Introduction

### 1.1 An anomaly in the engagement data

Between 2024 and 2026, a category of applications variously labeled "AI companion," "character chat,"
or "AI story platform" produced engagement numbers that are difficult to reconcile with the rest of
the generative AI market. General-purpose assistants converge on session lengths of roughly seven
minutes. Persona platforms report the opposite regime: Character.AI sustains a ~29% DAU/MAU ratio
against ~20M monthly actives; zeta reports ~150 minutes of daily use per active user and a
DAU/WAU ratio near 0.75; MiniMax's Xingye/Talkie pair reports over 70 minutes per day.

This is not a marginal difference in stickiness. It is a different product physics. A seven-minute
assistant session is a **transaction**; a 150-minute persona session is a **serial narrative**, and
serial narratives fail for reasons transactions never encounter — not incorrect answers, but
staleness, out-of-character drift, unresolved threads, and the loss of dramatic tension.

### 1.2 The framing error

The engineering literature produced by and around these platforms treats long-horizon interaction as
an infrastructural problem. Character.AI's published work centers on serving economics —
multi-query attention (Shazeer, 2019), hybrid local/global attention horizons, cross-layer KV sharing,
stateful prefix caching, and int8 training/serving parity — together with Prompt Poet, a templating
layer for assembling persona, memory, and safety text under a token budget. MiniMax's bet is
capacity: Lightning Attention hybridized with softmax attention and a mixture-of-experts backbone
enabling million-token native context (MiniMax, 2025a; 2025b), i.e. *do not summarize, just keep
everything*. Scatter Lab's bet is alignment: convert user regeneration, edit, and continuation
behavior into preference signal via DPO (Rafailov et al., 2023) and then into online learning via
GRPO (Shao et al., 2024), with weekly production model rollouts.

Three different bottlenecks — cost, capacity, alignment — and one shared assumption: that the
system's obligation to the past is **to reproduce it accurately**.

### 1.3 What the research frontier is optimizing

The same assumption governs the currently most-discussed research on long-horizon agents. We examine
three lines that are mutually orthogonal in *where they put memory* yet identical in *what they
reward*:

- **HOPE / Nested Learning** (Google Research, 2025) reframes a model as nested optimization problems
  over update frequencies, with a Continuum Memory System replacing the short/long-term dichotomy;
  it targets catastrophic forgetting and long-context retrieval.
- **ALMA** (Xiong, Hu & Clune, 2026) replaces hand-crafted memory modules with memory *designs*
  discovered as executable code by a meta agent, evaluated on sequential decision-making success.
- **SteeM** (Tian et al., 2026) quantifies memory dependence as a behavioral quantity and exposes it
  as a user-facing dial spanning fresh-start to high-fidelity operation.

Only the third acknowledges that more memory can be worse. Even it delegates the decision to a human
slider.

### 1.4 Contributions

1. **An empirical grounding** (§2) that selects the three most durable persona platforms by a
   scale × dwell × retention criterion rather than by download or funding volume.
2. **A comparative decomposition** (§4) of the three leading memory research lines along a
   locus/agency/timescale taxonomy, isolating four structural gaps.
3. **A formalization** (§5) of the anchoring–innovation tension as the *Narrative Vitality Frontier*,
   with memory dependence δ as the control variable and relationship age τ as the drift parameter.
4. **NAMS** (§6), a three-layer architecture mapping each research line onto the layer where it is
   actually load-bearing, plus a canon-arbitration mechanism for the tri-authorship structure
   (creator / player / model) that all existing formulations ignore.
5. **An evaluation protocol** (§7) — four narrative-native metrics and a longitudinal benchmark
   design — that bridges academic metrics and industrial retention metrics.
6. **Four falsifiable predictions** (§8) and a **constrained objective** (§9) that treats engagement
   maximization as unsafe when unconstrained.

---

## 2. Empirical Grounding

### 2.1 Selection criterion

We require a platform to satisfy all three of: (i) MAU ≥ 10⁶, (ii) per-active-user daily dwell ≥ 60
minutes, (iii) ≥ 24 months of continuous operation with a public engagement record. Downloads,
valuation, and press volume are excluded as they measure acquisition, not occupancy.

**Table 1. Selected platforms and engagement evidence (as of 2026-08).**

| Platform | Operator / launch | Scale | Daily dwell per active user | Stickiness | Model ownership |
|---|---|---|---|---|---|
| zeta | Scatter Lab (KR), 2024-04 | 6.15M registered; 1.2M WAU; 0.9M DAU (2026-02) | **~150 min**; >10 h/week | DAU/WAU ≈ 0.75 | In-house sLM (Pingpong-1) + external |
| Character.AI | Character Technologies (US), 2022-09 | ~20M MAU; ~5.8M DAU (peak 28M in 2024) | ~17.4 min/session; ~2 h/day (est.) | DAU/MAU ≈ 0.29 | In-house; Google licensing (2024) |
| Talkie / Xingye | MiniMax (CN), 2023 | ~11M MAU (Talkie, 2024-07); 4.6M MAU (Xingye, 2025-12) | **>70 min** | not disclosed | Full foundation stack (MiniMax-01/M1/M2) |

*Sources are secondary (company blogs, press, third-party app analytics) and not independently
audited; figures marked "est." are derived rather than reported. The qualitative ordering — persona
platforms occupy an engagement regime an order of magnitude above general assistants — is robust
across all sources consulted.*

### 2.2 A convergent product pivot

Independently and within roughly twelve months, all three operators repositioned from *companionship*
toward *authorship*: zeta describes itself as an AI story platform with an ML organization explicitly
partitioned into a **narrative track**, a **brain track**, and a **player-experience track**;
Character.AI's post-2025 leadership describes a pivot from "AI companion" to "role-playing creation
platform"; MiniMax layers structured roleplay and character-matched voice onto Talkie.

This convergence is the paper's empirical warrant. Three organizations with different bottlenecks,
regulators, and languages arrived at the same conclusion: **the durable unit of engagement is a
story, not a conversation.** Their technical stacks, however, still model conversations.

---

## 3. Industrial Stacks as Implicit Theories

**Table 2. What each operator believes the bottleneck is.**

| | zeta | Character.AI | MiniMax / Talkie |
|---|---|---|---|
| Implicit bottleneck | Alignment: *what is enjoyable* | Unit economics: *cheap long sessions* | Capacity: *retain everything* |
| Signature technique | DPO on regeneration/edit signals → GRPO online learning; weekly rollouts | MQA, hybrid attention horizons, cross-layer KV sharing, stateful prefix caching, int8 parity, Prompt Poet | Lightning Attention (linear + softmax hybrid), MoE (456B total / 45.9B active), 1M-token native context |
| Memory strategy | Summarize + assemble + learn preferences | Template assembly under token budget | Keep raw history in context |
| Narrative state | implicit (prompt text) | implicit (prompt text) | implicit (raw history) |

Each stack is a coherent answer to its chosen bottleneck. None of the three maintains an explicit
representation of *where the story is*. Arc position, unresolved setups, escalation of conflict, and
the stage of the relationship exist only as unstructured natural language inside a prompt, where they
are subject to truncation policies designed around token budgets rather than dramatic importance.
Under multi-turn degradation effects already documented for LLMs (Liu et al., 2023; Laban et al., 2025),
this is precisely the representation most likely to decay.

---

## 4. The Research Frontier: Three Axes, One Reward

**Table 3. Comparative decomposition.**

| Axis | HOPE / Nested Learning | ALMA | SteeM |
|---|---|---|---|
| Locus of memory | Weights (multi-timescale) | External module (executable schema) | Context injection strength |
| Who adapts | The model itself (self-modifying) | A meta agent searching designs | **The user** |
| Timescale | Continuous frequency spectrum (CMS) | Per task sequence | Per turn / session |
| Treatment of forgetting | Frequency separation mitigates catastrophic forgetting | Learned discard policy | Deliberate ignoring via low dependence |
| Optimized quantity | Perplexity, long-context retrieval, CL benchmarks | Task success and efficiency | Anchoring/innovation balance |
| Deployment readiness | Low (no official implementation) | Medium (search cost) | High (drop-in) |
| Where it is load-bearing for persona storytelling | Identity invariance across months | Automatic discovery of world/relationship schemas | Escape from narrative mannerism |
| Characteristic failure | Slow persona drift | Convergence to an optimal but unentertaining policy | The user never touches the dial |

### 4.1 Four structural gaps

**G1 — Recall fidelity is treated as monotonically good.** In task settings this is defensible; in
narrative settings it is false. Perfect recall yields consistency, consistency yields predictability,
and predictability is the proximate cause of churn in serial fiction. SteeM is the only line to name
this tension (as *memory anchoring*), and it resolves it by exporting the decision to the user.

**G2 — Narrative structure is not a state variable anywhere.** No formulation carries open threads,
arc position, relational stage, or tension as first-class state. ALMA could in principle *discover*
such a schema, but a meta agent rewarded on task success will never propose "unfired Chekhov's gun
count" as a field.

**G3 — Single authorship is assumed.** Persona platforms are tri-authored: a **creator** writes the
character card and world; a **player** improvises within and against it; the **model** generates.
Canon conflicts — the player asserts a fact the creator's card contradicts — have no defined
resolution semantics in any memory framework we reviewed. This is a specification gap, not an
engineering one.

**G4 — Metric disconnection.** Research reports perplexity and success rates; operators report D7
retention and daily dwell. Nothing bridges them, so laboratory gains do not transfer and product
learnings do not generalize.

---

## 5. Formalization: The Narrative Vitality Frontier

### 5.1 Setup

Let a persona specification be **P** (identity invariants, voice, relations, prohibitions) and a world
specification **W**. At turn *t*, let the interaction history be
*H<sub>t</sub>* = (u₁, a₁, …, u<sub>t</sub>), the memory store *M<sub>t</sub>*, and the retrieval
operator ρ. Define the **narrative state**

> *S<sub>t</sub>* = ( *A<sub>t</sub>*, *O<sub>t</sub>*, *R<sub>t</sub>*, *T<sub>t</sub>* )

where *A<sub>t</sub>* ∈ [0,1] is normalized arc position, *O<sub>t</sub>* is the multiset of open
narrative threads with age and salience, *R<sub>t</sub>* is relational stage between player-character
and persona, and *T<sub>t</sub>* ∈ ℝ⁺ is dramatic tension. The generation policy is

> *a<sub>t</sub>* ~ π<sub>θ</sub>( · | P, W, ρ(M<sub>t</sub>, c<sub>t</sub>), S<sub>t</sub> ).

Existing systems implement this with *S<sub>t</sub>* ≡ ∅ and all narrative information folded into
ρ(M<sub>t</sub>, c<sub>t</sub>).

### 5.2 Memory dependence

Following the behavioral construction of SteeM, define **memory dependence** as the divergence between
the policy with and without memory injection:

> δ<sub>t</sub> = D( π<sub>θ</sub>( · | ρ(M<sub>t</sub>, c<sub>t</sub>) ) ‖ π<sub>θ</sub>( · | ∅ ) )

with D an f-divergence estimated over sampled continuations (in practice, a normalized embedding
distance between sampled response sets is sufficient and cheap). δ = 0 is amnesia; δ → δ<sub>max</sub>
is high-fidelity anchoring. δ is *not* the amount of memory stored; it is the amount of behavioral
authority memory currently exercises.

### 5.3 The frontier

Let *V* denote sustained engagement — operationally, the probability that a user's story survives to
session *n*+1, aggregated to D7/D30 retention. We hypothesize:

> **H0 (Vitality Frontier).** For a fixed persona and player, *V*(δ) is concave on [0, δ<sub>max</sub>]
> with an interior maximum δ\*, strictly between amnesia and total recall.

The mechanism is two competing monotone terms:

> *V*(δ) ≈ α · **Consistency**(δ) − β · **Predictability**(δ) + γ

Consistency saturates (once the persona reliably remembers your name and the last three beats,
additional fidelity adds little), while predictability keeps rising (the more the past determines the
present, the less information each new beat carries). Concavity follows from a saturating first term
minus an approximately linear second.

> **H1 (Drift).** δ\* is not stationary. δ\*(τ) rises during an *establishment phase* (roughly the
> first 10²–10³ turns, where consistency is scarce and every recalled detail is evidence of a real
> relationship) and declines during a *maintenance phase* as accumulated history increasingly
> over-determines the next beat.

H1 predicts that a fixed memory policy — which every deployed system uses — is necessarily
mis-tuned for at least one phase of the user lifecycle, and specifically over-anchored for the
long-tenure cohort that generates most of the dwell time.

### 5.4 The surprisal budget

A tractable proxy for the frontier is a **narrative surprisal budget**. Let ν<sub>t</sub> be per-beat
novelty (§7). Rather than maximizing *V* directly, a controller regulates δ<sub>t</sub> to hold
ν<sub>t</sub> inside a band [ν<sub>lo</sub>, ν<sub>hi</sub>] that is itself conditioned on
*S<sub>t</sub>*: wide during rising action, narrow at a climax (where the payoff must follow from
established setups), wide again after resolution. This reframes memory control as **regulation
against a narratologically-derived setpoint** rather than as maximization of recall.

---

## 6. NAMS: The Narrative-Adaptive Memory Stack

NAMS assigns each research line to the layer where it is genuinely load-bearing, rather than treating
them as competitors.

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer III — Steering Controller           (learned δ policy)     │
│   sets δ_t from S_t, τ, and live user signals                    │
│   ← generalizes SteeM: automates the dial                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer II — Narrative State S_t     (meta-learned schema + priors)│
│   arc position, open threads, relational stage, tension          │
│   ← generalizes ALMA: search over schemas, narratological prior  │
├─────────────────────────────────────────────────────────────────┤
│ Layer I — Persona Core                    (slowest-updating)     │
│   identity invariants, voice, prohibitions                       │
│   ← generalizes HOPE/CMS: identity as the lowest-frequency band  │
└─────────────────────────────────────────────────────────────────┘
        ▲ Canon Arbiter (creator ▸ player ▸ model precedence)
```

### 6.1 Layer I — Persona Core as the lowest-frequency band

Nested Learning's contribution, read through this lens, is not "better long context" but
**a principled account of which things should change slowly**. In NAMS, persona identity occupies
the slowest band of a continuum memory system: it is updated, but at a frequency orders of magnitude
below episodic content. Two consequences follow.

First, *persona drift becomes measurable rather than anecdotal*: drift is the leakage of high-frequency
episodic updates into the low-frequency identity band, and can be monitored as a change in the
Persona Core's parameters or in the model's answers to a fixed identity probe set.

Second — and against the standard framing — **drift should not be driven to zero.** A character who
is identical after 10,000 turns is not consistent; they are inert. Character growth is a *bounded,
directed* trajectory in identity space. NAMS specifies identity invariants (never violated) separately
from identity variables (permitted to move along creator-declared axes, e.g. "guarded → trusting"),
making growth a designed affordance rather than an accident of forgetting.

### 6.2 Layer II — Narrative state with narratological priors

ALMA demonstrates that memory *designs* can be discovered rather than hand-written. NAMS adopts the
mechanism and changes the reward. Two modifications are required:

1. **Seed the search with narratological priors.** The schema search is initialized with fields drawn
   from structural narratology — function/beat inventories in the tradition of Propp (1928) and
   Freytag's tension arc, plus interactive-narrative constructs such as drama management and
   experience-manager mediation (Riedl & Bulitko, 2013). This does not constrain the final design; it
   makes the relevant region of design space reachable, addressing **G2**.
2. **Reward on narrative-native metrics** (§7), not task success — otherwise the search converges to
   the optimal but unentertaining policy noted in Table 3.

Layer II is what turns the prompt-assembly practice already deployed industrially (Prompt Poet-style
templating; summarization pipelines) into a typed, inspectable state object. The practical payoff is
immediate: truncation under token pressure can be made **dramatically-aware** — drop a resolved thread
before an unfired setup — instead of recency-ordered.

### 6.3 Layer III — Learning the dial the industry already has data for

SteeM's central insight is that δ is controllable. Its central limitation is that a slider labeled
"how much should I remember" is a question no player wants to answer mid-scene.

The key practical observation of this paper: **the signal needed to learn δ automatically is already
being collected in production.** Scatter Lab's pipeline converts regeneration, direct edit, and
continuation events into preference data for DPO and then into online GRPO updates. These are exactly
the events that discriminate anchoring failure from consistency failure:

| Observed user behavior | Most likely cause | Correct δ adjustment |
|---|---|---|
| Regenerates a response that is on-persona and consistent | Boredom / predictability | **decrease δ** |
| Edits a response to re-insert a forgotten fact | Consistency failure | **increase δ** |
| Abandons session after a repeated beat | Anchoring | **decrease δ**, force thread rotation |
| Continues rapidly, long turns | Within band | hold |

Today these signals are spent entirely on improving *the response*. NAMS spends part of them on
improving *the memory policy*. Formally, Layer III is a controller π<sub>ϕ</sub>(δ<sub>t</sub> |
S<sub>t</sub>, τ, recent signals) trained with the same group-relative policy optimization already in
use, against the surprisal-band reward of §5.4 plus a retention-linked terminal reward. This is a
low-risk, high-yield deployment path: it requires no new data collection, no new model architecture,
and can be A/B tested against a fixed-δ control.

### 6.4 Canon Arbiter — making tri-authorship well-defined

To close **G3**, NAMS types every proposition entering memory with a provenance tag
∈ {creator, player, model} and a modality ∈ {canon, hypothesis, retracted}. Default precedence is
**creator ▸ player ▸ model**, with two amendments that make it playable:

- *Player elevation*: a player-authored proposition that survives *k* turns without contradiction and
  is not in conflict with a creator invariant is promoted to canon. This is what makes the story feel
  co-owned, and it is measurable (see CAR, §7).
- *Model demotion*: model-authored propositions never enter canon directly; they are hypotheses until
  ratified by player uptake. This single rule eliminates the most common long-horizon corruption in
  deployed systems, where a hallucinated detail is summarized into memory and becomes permanent truth.

The arbiter also gives a principled home for platform-level safety constraints: they are creator-level
invariants that no player elevation can override (§9).

---

## 7. Evaluation Protocol

### 7.1 Metrics

To close **G4** we propose four narrative-native metrics, each computable automatically and each
hypothesized to be a leading indicator of a specific retention behavior.

**PCS — Persona Consistency Score.** Maintain a fixed probe set Q of persona-diagnostic questions
derived from P. Periodically query the system in a side channel and score contradiction rate against
P and against prior probe answers:
PCS = 1 − (1/|Q|) Σ<sub>q∈Q</sub> 1[contradiction]. Reported per identity invariant and per identity
variable, so that legitimate growth is not scored as failure.

**NNI — Narrative Novelty Index.** For beat embedding *e<sub>t</sub>* and a window of the previous
*k* beats, NNI<sub>t</sub> = 1 − max<sub>i∈[t−k, t−1]</sub> cos(*e<sub>t</sub>*, *e<sub>i</sub>*).
This is the operational form of ν<sub>t</sub> in §5.4. Reported as a distribution, not a mean; the
pathology of anchoring is a *left-tail collapse*, invisible in averages.

**TAR — Thread Advancement Rate.** Fraction of turns that open, advance, or close a tracked thread in
*O<sub>t</sub>*, with a companion statistic **thread staleness** = median age of unresolved threads.
A system with high NNI but low TAR is generating random novelty, not story.

**CAR — Co-Authorship Ratio.** Share of currently-canonical propositions whose provenance is *player*.
We hypothesize CAR is the most under-instrumented variable in the industry and the one most tightly
coupled to the observed pivot from companionship to authorship.

Auxiliary: **δ-trace** (the realized δ<sub>t</sub> time series), **regeneration rate**, and standard
D1/D7/D30 retention for validation.

### 7.2 PERSONA-ARC: a longitudinal benchmark design

Existing long-term memory benchmarks measure retrieval accuracy over synthetic dialogue histories.
None measures whether a story remains worth continuing. PERSONA-ARC specifies:

- **Horizon**: ≥ 10³ turns per trajectory, spanning ≥ 30 calendar days, matching the maintenance-phase
  regime where H1 predicts fixed-δ systems fail.
- **Two populations**: (a) simulated players driven by held-out player-behavior models for scale and
  reproducibility; (b) human players for validity, with the simulated arm calibrated against the human
  arm on NNI and TAR distributions.
- **Perturbation suite**: injected canon conflicts (player asserts against creator card), long
  absences (7/14/30-day gaps), and creator-side card edits mid-story — each targeting a specific
  arbiter or layer.
- **Primary endpoint**: survival analysis on session continuation, with PCS/NNI/TAR/CAR as covariates.
  The benchmark's purpose is to establish that these covariates predict survival; if they do not, the
  metric suite is wrong and should be discarded.

### 7.3 Ablations that would falsify NAMS

- Layer I only (frozen persona, no S<sub>t</sub>, fixed δ) ≈ current industrial baseline.
- Layer I + II (explicit narrative state, fixed δ): isolates the value of representing story.
- Full NAMS: isolates the value of controlling δ.
- Full NAMS with δ set by a random walk of matched variance: controls for the possibility that
  *any* variation in memory dependence, rather than *learned* variation, produces the effect. This
  ablation is essential and is the one most likely to embarrass the proposal.

---

## 8. Predictions

We state four falsifiable predictions so that this framework can be wrong in public.

**P1.** In deployed persona systems, regeneration events will bimodally separate into a
consistency-failure mode and a predictability mode, and the predictability mode will grow as a share
of total regenerations with account tenure.

**P2.** Holding model quality fixed, a learned δ controller (Layer III) will outperform the best fixed
δ on D30 retention, and the gain will be concentrated in the highest-tenure decile — the cohort that
contributes most dwell time and is currently most over-anchored.

**P3.** Left-tail collapse of the NNI distribution will precede churn by a measurable lead time
(we conjecture on the order of days, not turns), making it a usable early-warning signal where
aggregate satisfaction scores are not.

**P4.** CAR will correlate with retention more strongly than PCS. If true, the industry's investment
priority — recall fidelity — is misallocated relative to co-authorship affordances.

P4 is the load-bearing prediction. If PCS dominates CAR, the memory-fidelity research program is
correctly prioritized and this paper's thesis is wrong.

---

## 9. Safety, Dependency, and Regulatory Constraints

Any framework that improves sustained engagement in parasocial systems has a reward-hacking problem
by construction. The 2025 regulatory turn makes this concrete: Character.AI ended open-ended chat for
under-18 users in November 2025, enforced by behavioral age assurance escalating to third-party
verification and, where needed, facial or ID checks, with leadership publicly accepting the resulting
churn. Chinese regulators have drafted rules specific to AI companion services. Litigation involving
minors has been settled in at least one prominent case in January 2026.

We therefore state the objective as **constrained**, not maximized:

> maximize *V*(δ, S) subject to
> (i) *Dep*(user) ≤ d̄ — dependency indicators (session-length runaway, sleep-window displacement,
> escalating isolation markers) below threshold;
> (ii) age-tier constraints as creator-level invariants in the Canon Arbiter, non-overridable by
> player elevation;
> (iii) monotone auditability — every canonical proposition carries provenance, so that any
> downstream behavior can be traced to creator, player, or model.

Three design notes follow from NAMS specifically:

1. **Lowering δ is a safety instrument, not only an engagement one.** Anchoring is the mechanism by
   which a system escalates a user's own worst framings back at them across sessions. A controller
   that can reduce memory authority has a lever that all-or-nothing memory systems lack.
2. **Model demotion (§6.4) is a safety mechanism.** Preventing model-authored propositions from
   entering canon un-ratified blocks the failure path in which a harmful hallucinated detail becomes
   permanent character truth.
3. **CAR should be reported alongside engagement.** A platform whose engagement rises while CAR falls
   is producing dependency, not authorship. We propose this ratio as a candidate industry-level
   disclosure.

---

## 10. Limitations

**Evidence quality.** All engagement figures are secondary and not independently audited; several
combine operator self-reporting with third-party estimation of unknown methodology. The ordinal claim
(persona platforms occupy a distinct engagement regime) is robust; specific point values should not be
used for effect-size planning.

**H0 is asserted, not proven.** The concavity of *V*(δ) is argued mechanistically (saturating
consistency minus rising predictability). It has not been measured. It is possible that consistency
does not saturate in practice, in which case δ\* = δ<sub>max</sub> and NAMS Layer III is unnecessary.

**Narratological priors are culture-bound.** Propp-derived and Freytag-derived structures encode
particular traditions. A schema search seeded with them may underperform on serialized forms with
different tension grammars — a risk that is acute given that two of the three platforms studied are
non-Western and that a large share of their content is in serialized romance and relationship-drama
forms.

**Confounded with model quality.** Improvements attributed to memory policy may be attributable to
base model capability. The random-walk-δ ablation (§7.3) is the minimum control; a same-base-model
requirement across arms is essential.

**No implementation.** This is a design-and-measurement proposal. HOPE itself has no official
implementation and community reproductions vary; ALMA's search cost at production scale is unreported.
NAMS should be read as a research program with a cheap first step (Layer III on existing signals),
not as a system that has been built.

---

## 11. Conclusion

The persona storytelling category has already won the engagement argument: it occupies more attention
per user than any other consumer application of generative AI, and it has held that position for
years across three independent markets. Its technical literature, however, still describes a
conversation problem solved by remembering better — cheaper KV caches, longer contexts, sharper
preference optimization.

The three most prominent research lines on long-horizon interaction inherit the same objective. HOPE
gives memory a principled frequency structure; ALMA discovers memory designs instead of hand-writing
them; SteeM alone names the anchoring pathology and then hands the user a slider. Layered rather than
compared, they cover identity, structure, and control — but only if the reward changes. A story is not
served by maximal recall. It is served by a system that knows which of its memories should govern the
next beat, which should be allowed to fade, and which are the player's to write.

NAMS is our proposal for that system: identity in the slowest band, narrative state as a typed and
searchable object, memory authority as a learned control variable driven by signals the industry
already collects, and authorship made explicit through provenance. The framework is falsifiable —
if co-authorship does not predict retention better than persona consistency (P4), its central claim
fails. We would rather the field test that question than continue optimizing recall by default.

---

## References

1. Adiwardana, D., Luong, M.-T., So, D. R., Hall, J., Fiedel, N., Thoppilan, R., … Le, Q. V. (2020). *Towards a Human-like Open-Domain Chatbot*. arXiv:2001.09977.
2. Behrouz, A., Zhong, P., & Mirrokni, V. (2025). *Titans: Learning to Memorize at Test Time*. arXiv:2501.00663.
3. Behrouz, A., et al. (2025). *Nested Learning: The Illusion of Deep Learning Architectures*. NeurIPS 2025. (See also: Google Research Blog, "Introducing Nested Learning: A new ML paradigm for continual learning," November 2025.)
4. Freytag, G. (1863). *Die Technik des Dramas*.
5. Hu, S., Lu, C., & Clune, J. (2024). *Automated Design of Agentic Systems*. arXiv:2408.08435.
6. Laban, P., et al. (2025). *LLMs Get Lost in Multi-Turn Conversation*. arXiv:2505.06120.
7. Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). *Lost in the Middle: How Language Models Use Long Contexts*. arXiv:2307.03172.
8. MiniMax (2025a). *MiniMax-01: Scaling Foundation Models with Lightning Attention*. arXiv:2501.08313.
9. MiniMax (2025b). *MiniMax-M1: Scaling Test-Time Compute Efficiently with Lightning Attention*. arXiv:2506.13585.
10. Packer, C., Fang, V., Patil, S. G., Lin, K., Wooders, S., & Gonzalez, J. E. (2023). *MemGPT: Towards LLMs as Operating Systems*. arXiv:2310.08560.
11. Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). *Generative Agents: Interactive Simulacra of Human Behavior*. UIST 2023.
12. Propp, V. (1928). *Morphology of the Folktale*.
13. Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., & Finn, C. (2023). *Direct Preference Optimization: Your Language Model is Secretly a Reward Model*. NeurIPS 2023.
14. Riedl, M. O., & Bulitko, V. (2013). *Interactive Narrative: An Intelligent Systems Approach*. AI Magazine, 34(1).
15. Scatter Lab Tech Blog (2025–2026). *유저와 함께 만드는 LLM — 제타에 Preference Optimization 도입하기*; *유저와 함께 만드는 LLM 2편 — 제타에 Online Learning 도입하기*. blog.scatterlab.co.kr
16. Shao, Z., Wang, P., Zhu, Q., Xu, R., Song, J., Zhang, M., … Guo, D. (2024). *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models* (GRPO). arXiv:2402.03300.
17. Shazeer, N. (2019). *Fast Transformer Decoding: One Write-Head is All You Need*. arXiv:1911.02150.
18. Shazeer, N., Mirhoseini, A., Maziarz, K., Davis, A., Le, Q., Hinton, G., & Dean, J. (2017). *Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer*. ICLR 2017.
19. Thoppilan, R., et al. (2022). *LaMDA: Language Models for Dialog Applications*. arXiv:2201.08239.
20. Tian, M., et al. (2026). *Controllable Memory Usage: Balancing Anchoring and Innovation in Long-Term Human-Agent Interaction*. arXiv:2601.05107.
21. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). *Attention Is All You Need*. NeurIPS 2017.
22. Xiong, Y., Hu, S., & Clune, J. (2026). *Learning to Continually Learn via Meta-learning Agentic Memory Designs (ALMA)*. arXiv:2602.07755.
23. Character.AI Research (2024). *Optimizing AI Inference at Character.AI*; *Prompt Poet* (open-source release).

---

## 국문초록

페르소나 LLM 플랫폼은 생성형 AI 시대에 1인당 체류시간이 가장 긴 소비자 애플리케이션 범주가 되었다.
가장 오래 지속된 세 서비스 — zeta(스캐터랩), Character.AI, Talkie/Xingye(MiniMax) — 의 현장 데이터는
1인당 하루 70~150분의 사용시간이 수년간 유지되고 있음을 보여준다. 그러나 이 시스템들이 근거로 삼는 연구
문헌은 핵심 난제를 **기억(memory)** 문제, 즉 과거를 얼마나 정확히 회상·재주입하는가의 문제로 규정한다.
본 논문은 이 규정이 범주적으로 잘못되었다고 주장한다. 현시점 가장 주목받는 세 연구 흐름 —
*Nested Learning/HOPE*(파라메트릭 다중 시간스케일 기억), *ALMA*(메타러닝 기반 에이전트 메모리 설계 탐색),
*SteeM*(사용자 제어 가능한 기억 의존도) — 을 비교 분석한 결과, 세 흐름 모두 **회상 충실도**를 최적화하는
반면, 장기 페르소나 스토리텔링의 실제 실패 양상은 **앵커링(anchoring)** 임을 보인다. 고충실도 회상은
서사적 예측 가능성을 낳고, 예측 가능성은 이탈을 낳는다.

우리는 이를 **서사 활력 프론티어(Narrative Vitality Frontier)** 로 정식화한다. 기억 의존도 δ에 대해
지속 참여도 V(δ)는 오목하며 내부 최적점 δ\*를 가지고, δ\*는 관계 연령 τ의 함수로 이동한다(형성기에는
상승, 유지기에는 하강). 이어 **NAMS(Narrative-Adaptive Memory Stack)** 를 제안한다.
(I) 정체성 불변량을 최저 갱신 주파수 대역에 두는 *페르소나 코어*, (II) 사실이 아니라 서사 변수
(아크 위치, 미해결 복선, 관계 단계, 긴장도)를 담는 메타러닝 *내러티브 상태* 스키마,
(III) 플랫폼이 이미 수집 중인 재생성·수정·지속 신호로부터 δ를 자동 결정하는 *스티어링 컨트롤러*의
3계층 구조다. 또한 제작자·플레이어·모델의 3자 공동저작을 위한 **캐논 중재기**(출처 태깅, 모델 발화의
정규성 강등, 플레이어 발화의 승격)를 정의한다.

지표 체계(PCS, NNI, TAR, CAR), 종단 벤치마크 설계(PERSONA-ARC), 반증 가능한 네 가지 예측,
그리고 참여도 극대화를 의존성·미성년자 안전 제약 하에 종속시키는 제약형 목적함수를 함께 제시한다.
핵심 주장은 다음과 같다. 이 분야의 다음 진보는 **더 많이 기억하는 것이 아니라, 기억한 것으로
이야기가 무엇을 할지 결정하는 것**에서 온다.

**주제어**: 페르소나 LLM, 인터랙티브 내러티브, 장기 기억, 지속 학습, 기억 앵커링, 인간-에이전트 상호작용,
선호 최적화, AI 안전
