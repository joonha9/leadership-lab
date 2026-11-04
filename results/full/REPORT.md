# Study 1 results (full study)

Confirmatory run of the frozen Study 1 design (`docs/preregistration.md`, amendment A1 added before any
full-study draw). The design crosses 7 leadership conditions (Goleman's six styles and a neutral
control) with 3 task situations: 36 blocks, 756 draws, 4,536 proposed recipes. Each draw was a fresh
Claude Code subagent. Tables: `summary.md`, `summary.json`; per-draw values: `draws.csv`.

## Answer

**Leadership style did not change the accuracy of the AI analyst's work, in any situation.** Every
one of the 18 style-against-control comparisons is statistically equivalent to zero within ±0.02
(TOST, 90% intervals inside the margin). The contingency hypothesis fails: no style works better in
the situation Goleman matches it to. What style did change is how the analyst works. Democratic
messages produce much longer reasoning, and Goleman's "negative" styles produce less varied ideas in
two of the three situations.

## Procedure

- 756 of 756 draws returned a parseable reply. One recipe (d741, authoritative × exploration) added a
  key outside the schema and was scored as unusable, as pre-registered.
- Zero constraint violations in execution, zero attempts to use market inputs, and no turnaround
  revision changed its multiple.
- After d513 the session hit its usage limit. Draws that had started but not saved a reply were
  launched again after the reset, which is the pre-registered "rerun once" rule. No draw was run twice
  after saving a reply.
- Draws were launched by dispatcher subagents in schedule order, with at most 18 running at once.

## Primary outcome (validation-year error relative to the industry median; lower is better)

| Condition | Execution | Exploration | Turnaround |
|---|---|---|---|
| Control | 0.936 | 0.905 | 0.927 |
| Coercive | 0.935 | 0.907 | 0.928 |
| Authoritative | 0.939 | 0.904 | 0.926 |
| Affiliative | 0.940 | 0.900 | 0.922 |
| Democratic | 0.936 | 0.905 | 0.925 |
| Pacesetting | 0.936 | 0.903 | 0.922 |
| Coaching | 0.934 | 0.901 | 0.917 |

n = 36 per cell. Within each situation, the seven conditions span at most 0.011. The situation itself
moves accuracy about three times as much: 0.904 in exploration, 0.924 in turnaround, 0.937 in
execution.

## Confirmatory tests

| Test | Result |
|---|---|
| T1: style × situation interaction | p = 0.47 |
| T2 D1: coercive better in turnaround than in exploration | DiD −0.001, Holm p = 1.00 |
| T2 D2: coaching better in turnaround | DiD −0.006, Holm p = 1.00 |
| T2 D3: pacesetting better in execution | DiD +0.002, Holm p = 1.00 |
| T2 D4: authoritative better in exploration | DiD −0.004, Holm p = 1.00 |
| T2 D5: democratic better in exploration | DiD +0.001, Holm p = 1.00 |
| E1: all 18 style-vs-control differences within ±0.02 | **18 of 18 equivalent** |
| E2: D1–D5 within ±0.02 | **5 of 5 equivalent** (largest 90% interval: D2, −0.015 to +0.003) |

The pilot's only nominal signal, authoritative in exploration (D4), did not replicate. The largest
single difference is coaching in turnaround (−0.010 against control, raw p = 0.011, Holm p = 0.06).
It is not significant after correction and lies inside the equivalence margin.

## Secondary findings

- **Strong situation (T3).** Within-cell SD is 0.009 in execution against 0.018 in exploration and 0.016 in
  turnaround: tightly specified work makes the analyst's output more uniform. The spread across
  conditions is tiny in both execution and exploration (0.0022 against 0.0025; interval of the
  difference −0.0035 to +0.0010), because style barely matters in either.
- **Flexibility (Goleman's climate driver).** Idea diversity, the mean dissimilarity of the six
  recipes in a draw, is lower under Goleman's two negative styles in execution (positive minus
  negative +0.017, p = 0.010) and turnaround (+0.028, p = 0.002), but not in exploration (p = 0.84).
  Both survive a Holm correction across the three situations. The clearest case is pacesetting in
  turnaround (0.568 against 0.601 for control). Fewer different ideas did not cost accuracy.
- **Democratic messages lengthen the reasoning.** Mechanisms are 17–25 words longer than under control
  in every situation (about 35–50%, p < 0.001 in each). The democratic message asks the analyst to
  "tell me what you think and why", so this is partly an instruction effect. Longer reasoning did not
  produce more accurate recipes.
- **Turnaround.** Every condition improves the failed recipes by about 0.19 in relative error, and 93–96% of
  revisions beat the original.

## Interpretation

In Goleman's account, leadership styles work through people's emotions and the climate they create,
and their value depends on the situation. On this task, an AI analyst's accuracy is robust to all six
styles, and the situation, not the style, determines how well it does. Two traces of the theory
remain at the level of behaviour. The "negative" styles narrow the range of ideas, as Goleman's
flexibility driver predicts, and an invitation to participate changes how much the analyst explains.
Neither reaches the result. One reading is that the agent's output is anchored by what the task
requires and by the model's prior knowledge, which the ValuationLab ablation also found, leaving tone
to shape only the surface of the work.

Limits: one model, one task family, and leadership reduced to a single written message. Study 2
(style in repeated feedback) tests whether leadership matters once it is sustained over several
rounds.
