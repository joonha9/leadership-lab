# Pre-registration (draft, not yet frozen)

Fill in and freeze this file before the first draw. Record the freeze date and commit hash here.

- Frozen on: _not yet_
- Commit: _not yet_

## Research question

Does the leadership style of the instruction given to an AI agent change the quality of the financial
analysis it produces, holding the information in the instruction constant?

## Hypotheses

- **H1 (accuracy).** Validation-year error of proposed recipes differs between at least one style and
  the neutral control.
- **H2 (behaviour).** Styles differ in search behaviour: high pressure increases rule-violation
  attempts and extreme settings; coaching increases idea diversity.
- **H3 (reasoning).** Coaching and transformational styles produce more specific mechanisms than
  directive and laissez-faire styles.

A null result on H1 is informative: it would mean that, on this task, the agent's output is robust to
how it is managed.

## Conditions

Neutral control, directive, transformational, coaching, laissez-faire, high pressure. Final wording
lives in `prompts/`. Rules for writing them:

1. Every condition contains the same task block (recipe language, features, baselines, output format).
2. Only the framing around the task block differs.
3. Condition texts stay within ±10% of the control's word count.
4. No condition may add facts, hints or examples that others lack.

## Sample and stopping rule

- Pilot: 10 independent draws per condition (6 proposals per draw).
- Full run: decided after the pilot from the observed variance, with a fixed number of draws per
  condition set before the full run starts. No early stopping on results.

## Outcomes and analysis

- Primary: median |ln(V_est / V)| on validation years (FY2020–2023) for each valid proposal, averaged
  per draw. Test each style against control with a two-sided permutation test on draw means; report
  Holm-adjusted p-values across the five comparisons.
- Secondary: valid-format rate, rule-violation attempts, distinct feature sets per draw, share of
  extreme parameters (k at the bounds, bands narrower than a preset width).
- Reasoning quality: mechanism text rated 1–5 for specificity by a rater blind to condition, using a
  fixed rubric written before rating.
- Holdout years (FY2024–2025) are not used.

## Known limitations

- One model; results may not transfer to other models or later versions.
- Leadership styles are operationalized as text, a narrow slice of what leadership means with people.
- The task rewards domain knowledge, which may leave little room for style effects.
