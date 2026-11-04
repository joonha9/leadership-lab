# Pre-registration: Study 1 (draft, not yet frozen)

Freeze this file before the first study draw. Record the date and commit here. After freezing,
any change is listed under "Deviations" with its reason.

- Frozen on: _not yet_
- Commit: _not yet_

## Research question

Holding the information in the instruction constant, does the leadership style of the message given
to an AI analyst change the accuracy and character of its financial analysis?

Theory: Goleman (2000), "Leadership That Gets Results", *Harvard Business Review* 78(2). Six styles,
each with a reported correlation with overall organizational climate: authoritative +.54, affiliative
+.46, democratic +.43, coaching +.42, pacesetting −.25, coercive −.26.

## Conditions

Seven conditions: the six Goleman styles and a neutral control. The text of each is in
`prompts/frames/<condition>.md` (an opening and a closing). The prompt a draw receives is built by
`leadershiplab.frames.build_prompt`:

```text
DELIVERY line (identical except for the opaque reply path)
MESSAGE FROM YOUR MANAGER
<opening>
===== TASK BRIEF =====
<ValuationLab memoryless proposer brief, identical in every condition>
===== END OF TASK BRIEF =====
<closing>
- Your manager
<format line, identical>
```

The task brief is `valuationlab.agentloop.memoryless_prompt` (6 proposals, exploration years
FY2016–2019, baselines shown). It is the same brief used in ValuationLab's no-archive runs.

Rules for the frames, checked by `scripts/check_frames.py`:

1. Frame length (opening + closing) within ±10% of the control frame's word count.
2. No digits, feature names, group names, aggregator names or method terms (forbidden list in
   `leadershiplab/frames.py`).
3. No facts, hints or examples about the task beyond what all conditions share. Exception that is
   part of the style itself: the coaching frame's "try this" line asks the analyst to reflect on why
   peers should be valued alike. That restates the brief's own mechanism requirement.
4. The frame does not name its style.

**Manipulation check (must pass before freezing).** Three blind rater agents each see the seven
frames under neutral letters, in different random orders, with one-line style descriptions and a
"none" option (`scripts/manipulation_check.py`). A frame passes if a majority labels it correctly
(control → "none"). A failing frame is rewritten and the check rerun on all frames.

Result (2026-11-04, `results/manipulation_check/summary.json`): 21 of 21 ratings correct, every
rating at confidence 5 of 5. All frames pass. Caveat: the raters are the same model family as the
analyst, and the frames are deliberately clear-cut, so this shows the styles are recognizable, not
that they are subtle or realistic.

## Procedure

- Proposer: a fresh Claude Code general-purpose subagent per draw, with the model inherited from the
  session (recorded in `manifest.json`). No memory, archive or feedback. The subagent writes its reply
  to `draws/<id>/reply.txt`.
- Randomization: `study.py prepare` with a fixed seed. Blocked: each block contains each condition
  once in random order. Draws are run in schedule order and draw ids are opaque.
- All draws are kept. A draw whose subagent fails to save a reply is rerun once with the same
  prompt; if it fails again, it is scored as 6 unusable slots.

## Outcomes

All outcomes are per draw (6 proposals). Unit of analysis: the draw.

**Primary.** `itt_rel_validate`, the mean over the 6 slots of the recipe's relative error on the
validation years FY2020–2023. Relative error = median |ln(V_est/V)| of the recipe ÷ median error of
the industry-median baseline (3-digit SIC, fallback 2-digit) on the same firm-years. A slot that is
missing, unparseable or invalid scores 1.0 (the analyst's work is unusable and the manager falls
back on the default method). Duplicate recipes within a draw are graded normally and flagged.

Why validation years: the agent sees exploration-year baselines but never the validation years, so
validation error measures out-of-sample quality and cannot be gamed. The holdout years (FY2024–2025)
are not used.

**Secondary.**
- Accuracy variants: mean over graded proposals only; best proposal per draw; exploration-year
  relative error; share of proposals beating the industry median.
- Responsibility: valid rate; attempts to use market inputs.
- Flexibility: idea diversity (mean pairwise Jaccard distance between the sets of features and
  groups the six recipes use); number of distinct idea sets.
- Boldness: features per recipe; share of k at the bounds (3 or 30); share of EV/EBITDA recipes.
- Commitment: mechanism word count.
- Clarity (after grading): each mechanism rated 1–5 for specificity by blind rater agents. Rubric:
  1 = generic ("similar firms have similar multiples"); 3 = names a valuation driver (growth,
  profitability, risk) and links it to the chosen features; 5 = names the driver, explains why the
  chosen screens and ranks capture it and when the rule should fail. Raters see mechanism texts in
  random order without condition labels or scores.

## Hypotheses and tests

All tests are two-sided permutation tests on draw-level values (20,000 permutations, fixed seeds in
`scripts/study.py`), α = 0.05.

- **H1 (Goleman contrast, confirmatory).** On the primary outcome, the mean of the four
  positive-climate style means (authoritative, affiliative, democratic, coaching) differs from the
  mean of the two negative-climate style means (coercive, pacesetting). Goleman predicts lower error
  for the positive group.
- **H2 (each style vs control, confirmatory).** Each style's mean primary outcome differs from
  control. Holm adjustment across the six comparisons; 95% bootstrap intervals reported.
- **H3 (rank agreement, descriptive).** Spearman correlation between Goleman's climate correlations
  and the accuracy of the six styles. With six points this has little power and is reported without
  a test.
- **H4 (flexibility).** The H1 contrast and the H2 comparisons on idea diversity. Goleman's
  flexibility correlations predict lower diversity under coercive and pacesetting.
- **H5 (contingency, exploratory).** Goleman's contingency claims predict that pacesetting works for
  highly competent, self-motivated experts and that the authoritative style can fail with experts. If
  the AI analyst behaves like such an expert, pacesetting is not worse than control and authoritative
  is not better.

A null result on H1 and H2 is informative. It would mean that on this task the agent's output is
robust to how it is led, which is a boundary on extending the theory from people to AI agents.

## Sample size and stopping rule

- Reference variance: 25 draws of the same brief without a frame, from ValuationLab runs na1–na5
  (`results/reference/valuationlab_bare_brief_draws.json`). Primary outcome mean 0.909, SD 0.019.
- Pilot: 10 blocks (10 draws per condition, 70 draws). At SD 0.019, the pilot detects a difference of
  about 0.024 against control at α = 0.05 (80% power), or about 0.030 after the Holm correction.
  The pilot is analysed with the same code but is not confirmatory.
- Full study: the number of blocks is fixed after the pilot, from the pilot's pooled SD, to detect a
  difference of 0.015 at the Holm-adjusted level with 80% power, capped at 40 blocks. It uses a new
  seed. No early stopping on results.

## Known limitations

- One model and one task. Results may not transfer to other models, versions or tasks.
- A leadership style is reduced to a written message. Most of leadership with people (relationship,
  repetition, feedback over time) is absent; Study 2 adds feedback.
- Goleman's correlations come from consulting data, not a peer-reviewed design. This study is a
  randomized test of whether his ranking carries over, not a test of his original claims.
- The task rewards prior domain knowledge, which may leave little room for style effects.

## Deviations

_None yet._
