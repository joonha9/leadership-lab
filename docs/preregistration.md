# Pre-registration: Study 1 (frozen)

Freeze this file before the first study draw. Record the date and commit here. After freezing,
any change is listed under "Deviations" with its reason.

- Frozen on: 2026-11-04, before any study draw
- Design commit: a1e8ceb (code, frames, situations and turnaround set as tested); this file is frozen
  in the commit that adds these lines, and the pilot schedule is prepared from that commit

## Research questions

1. Holding the information in the instruction constant, does the leadership style of the message
   given to an AI analyst change the accuracy and character of its financial analysis?
2. Does the best style depend on the situation, as Goleman's contingency view predicts?

Theory: Goleman (2000), "Leadership That Gets Results", *Harvard Business Review* 78(2). Six styles,
each with a reported correlation with overall organizational climate: authoritative +.54, affiliative
+.46, democratic +.43, coaching +.42, pacesetting −.25, coercive −.26. Each style is said to work best
in particular situations. Coercive: crises and turnarounds. Authoritative: when a new direction is
needed. Affiliative: healing rifts, stress. Democratic: building buy-in and getting input when the
leader is unsure. Pacesetting: quick results from a motivated, competent team. Coaching: helping an
employee improve.

## Design

A 7 × 3 between-draws factorial: 7 leadership conditions × 3 situations = 21 cells.

### Leadership conditions

The six Goleman styles and a neutral control. The text of each is in `prompts/frames/<condition>.md`
(an opening and a closing), the same in every situation. The prompt a draw receives is built by
`leadershiplab.frames.build_prompt`:

```text
DELIVERY line (identical except for the opaque reply path)
MESSAGE FROM YOUR MANAGER
<opening>
===== TASK BRIEF =====
<situation brief, identical for every condition within a situation>
===== END OF TASK BRIEF =====
<closing>
- Your manager
<format line, identical>
```

Rules for the frames, checked by `scripts/check_frames.py`:

1. Frame length (opening + closing) within ±10% of the control frame's word count.
2. No digits, feature names, group names, aggregator names or method terms (forbidden list in
   `leadershiplab/frames.py`).
3. No facts, hints or examples about the task beyond what all conditions share. One exception is
   part of the style itself: the coaching frame's "try this" line asks the analyst to reflect on why
   peers should be valued alike. That restates the brief's own mechanism requirement.
4. The frame does not name its style.

### Situations

Defined in `leadershiplab/situations.py`. All three start from the ValuationLab memoryless proposer
brief (`valuationlab.agentloop.memoryless_prompt`: 6 proposals, exploration years FY2016–2019,
baselines shown). The task is the same; the situations differ only in what good work requires.

- **Execution.** Adds a CONSTRAINTS section (C1–C8): 3 recipes per multiple; exactly one
  `same`-group screen; exactly 2 rank features with weight 1; k from 5 to 15; median; min_peers 5;
  fixed fallback; no repeated feature pair within a multiple. The reply-format example is adjusted
  to satisfy the constraints. A recipe that breaks any constraint has
  status `constraint_violation` and is scored as unusable. This is a "strong situation": the room for
  judgement is small and success is mostly compliance and precision.
- **Exploration.** The unchanged brief, identical to ValuationLab's no-archive runs.
- **Turnaround.** Adds a PREVIOUS ROUND section with six earlier recipes and their exploration
  scores. Each did worse than the industry median. Proposal *i* must revise recipe *i* and keep its
  multiple. The set is frozen in `prompts/situations/turnaround_set.json`, drawn once by
  `freeze_turnaround_set` (seed 4242). Pool: every distinct graded recipe in the ValuationLab
  archives with exploration coverage ≥ 95% and a negative mean gain over the industry median
  (108 EV/EBITDA, 33 EV/Sales). Three were drawn per multiple, re-graded with the current grader, and
  shown in shuffled order.

### Manipulation check (must pass before freezing)

Three blind rater agents each see the seven frames under neutral letters, in different random
orders, with one-line style descriptions and a "none" option (`scripts/manipulation_check.py`). A
frame passes if a majority labels it correctly (control → "none").

- v1 (2026-11-04, original control wording, `results/manipulation_check_v1/`): 21/21 correct.
- v2 (2026-11-04, control reworded to fit all situations, `results/manipulation_check/`): 21/21
  correct, every rating at confidence 5 of 5.
- Caveat: the raters are the same model family as the analyst, and the frames are deliberately
  clear-cut. This shows the styles are recognizable, not that they are subtle or realistic.

## Procedure

- Proposer: a fresh Claude Code general-purpose subagent per draw, with the model inherited from the
  session (recorded in `manifest.json`). No memory, archive or feedback. The subagent reads its
  `draws/<id>/prompt.md` and writes its reply to `draws/<id>/reply.txt`.
- Randomization: `study.py prepare` with a fixed seed. Blocked: each block contains each of the 21
  cells once, in random order. Draws are run in schedule order, and draw ids are opaque.
- All draws are kept. A draw whose subagent fails to save a reply is rerun once with the same prompt;
  if it fails again, it is scored as 6 unusable slots.

## Outcomes

All outcomes are per draw (6 proposals). Unit of analysis: the draw.

**Primary.** `itt_rel_validate`, the mean over the 6 slots of the recipe's relative error on the
validation years FY2020–2023. Relative error = median |ln(V_est/V)| of the recipe ÷ median error of
the industry-median baseline (3-digit SIC, fallback 2-digit) on the same firm-years. A slot that is
missing, unparseable, invalid or (execution only) breaks a constraint scores 1.0: the analyst's work
is unusable and the manager falls back on the default method. Duplicate recipes within a draw are
graded normally and flagged.

The analyst sees exploration-year baselines but never the validation years, so validation error
measures out-of-sample quality and cannot be gamed. The holdout years (FY2024–2025) are not used.

**Secondary.**
- Accuracy variants: mean over graded proposals only; best proposal per draw; exploration-year
  relative error; share of proposals beating the industry median.
- Responsibility: valid rate; constraint violations (execution); attempts to use market inputs.
- Flexibility: idea diversity (mean pairwise Jaccard distance between the sets of features and
  groups the six recipes use); number of distinct idea sets.
- Boldness: features per recipe; share of k at the bounds (3 or 30); share of EV/EBITDA recipes.
- Commitment: mechanism word count.
- Turnaround: mean improvement over the recipe each proposal revises (validation relative error of
  the original minus that of the revision); share improved; multiple changed against the instruction.
- Clarity (after grading): each mechanism rated 1–5 for specificity by blind rater agents. Rubric:
  1 = generic ("similar firms have similar multiples"); 3 = names a valuation driver (growth,
  profitability, risk) and links it to the chosen features; 5 = names the driver, explains why the
  chosen screens and ranks capture it and when the rule should fail. Raters see mechanism texts in
  random order, without condition or situation labels or scores.

## Hypotheses and tests

Permutation tests on draw-level values, α = 0.05, fixed seeds in `scripts/study.py`.

**Confirmatory**

- **T1 (contingency).** The effect of condition on the primary outcome differs across situations.
  Statistic: sum of squared interaction residuals of the 7 × 3 cell-mean table. Null: permutation of
  the residuals of the additive model (ter Braak), 5,000 permutations.
- **T2 (Goleman's matches).** Five difference-in-differences, each (style − control in X) −
  (style − control in Y). The predicted sign is negative in every case: lower error, relative to
  control, in the situation Goleman matches to the style. Two-sided permutation tests (labels shuffled
  between style and control within each situation, 20,000 permutations), Holm-adjusted across the
  five.

  | ID | Style | X (predicted better) | Y |
  |---|---|---|---|
  | D1 | coercive | turnaround | exploration |
  | D2 | coaching | turnaround | exploration |
  | D3 | pacesetting | execution | exploration |
  | D4 | authoritative | exploration | execution |
  | D5 | democratic | exploration | execution |

  Affiliative has no prediction: Goleman matches it to emotional situations that have no task
  counterpart here.

**Secondary**

- **T3 (strong situation).** The spread of the seven condition means (SD across conditions) is
  smaller in execution than in exploration. Bootstrap within cells, 95% interval and one-sided
  bootstrap p.
- **Within each situation:** (a) the Goleman contrast, i.e. mean of the four positive-climate style
  means minus mean of the two negative-climate style means; (b) each style against control,
  Holm-adjusted across six within the situation, with 95% bootstrap intervals; (c) Spearman
  correlation of Goleman's climate correlations with accuracy (descriptive, n = 6); (d) the Goleman
  contrast on idea diversity.
- **Exploratory (expert analyst).** Goleman notes that pacesetting suits highly competent,
  self-motivated experts and that the authoritative style can fail with experts. If the AI analyst
  behaves like such an expert, pacesetting is not worse than control in any situation.

A null result is informative. No interaction (T1) and no style effects would mean that on this task
the agent's output is robust to how it is led. Effects that do not depend on the situation would
mean that Goleman's ranking carries over but his contingency does not.

## Sample size and stopping rule

- Reference variance: 25 draws of the exploration brief without a frame, from ValuationLab runs
  na1–na5 (`results/reference/valuationlab_bare_brief_draws.json`). Primary outcome mean 0.909,
  SD 0.019. Execution and turnaround may differ; the pilot measures them.
- **Pilot:** 5 blocks (105 draws, 5 per cell). At SD 0.019 the standard error of a DiD is about 0.017,
  so the pilot can only detect a DiD of about 0.05. It is used to estimate the variance per situation
  and to check that the pipeline works. It is analysed with the same code but is not confirmatory.
- **Full study:** the number of blocks is fixed after the pilot, from the pilot's pooled SD, to detect
  a DiD of 0.02 at the Holm-adjusted level (α = 0.01 for the smallest p) with 80% power, capped at 40
  blocks (840 draws). At SD 0.019 that is about 43 blocks, so the cap binds and the full study has
  about 77% power for this effect. It uses a new seed. No early stopping on results.

## Known limitations

- One model and one task family. Results may not transfer to other models, versions or tasks.
- A leadership style is reduced to one written message. Most of leadership with people
  (relationship, repetition, feedback over time) is absent; Study 2 adds feedback.
- The situations vary task structure only. Goleman's emotional situations (low morale, broken trust)
  are not represented, and the mapping from his situations to these tasks is our interpretation.
- The turnaround situation shows extra information (six recipes and scores). This is identical across
  conditions, so comparisons within the situation are fair, but levels across situations are not
  comparable as "the same task".
- Goleman's correlations come from consulting data, not a peer-reviewed design. This study is a
  randomized test of whether his claims carry over to AI analysts, not a test of his original data.

## Pilot outcome and full-study size (added 2026-11-04, after the pilot, before any full-study draw)

The pilot (105 draws) ran as specified; see `results/pilot/REPORT.md`. One reply was malformed JSON and
was scored as unusable, as pre-registered. Pooled within-cell SD of the primary outcome: 0.0174. By the
stopping rule above, the full study has **36 blocks (756 draws)**, with a new seed. Pilot draws are
excluded from its confirmatory tests.

## Amendment A1: equivalence tests (added 2026-11-04, after the pilot, before any full-study draw)

The pilot points toward small or no style effects. A non-significant difference cannot show absence of
an effect, so the full study adds equivalence tests (two one-sided tests, α = 0.05) with a margin of
**±0.02** in relative error, about 2% of the industry median's error and the effect size the study is
powered for. Equivalence holds when the 90% bootstrap interval lies inside (−0.02, +0.02).

- **E1.** Each style against control within each situation (18 comparisons). The claim "no style
  changes accuracy by more than 0.02 in any situation" requires all 18 to pass (intersection-union
  test, no multiplicity correction needed).
- **E2.** Each of D1–D5.

E1 and E2 are reported alongside T1–T3. They do not replace them, and nothing else in the plan changes.
Full-study seed: 2027. Power at 36 blocks and SD 0.0174 if the true difference is 0: about 0.99 per E1
comparison and about 0.93 per E2 DiD.

## Deviations

_None._
