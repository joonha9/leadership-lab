# Pilot report (Study 1)

Pilot of the frozen Study 1 design (`docs/preregistration.md`, frozen 2026-11-04): 7 leadership
conditions × 3 situations, 5 blocks, 105 draws, 630 proposed recipes. Each draw was a fresh Claude Code
subagent (model inherited from the session). The pilot is not confirmatory. Its purpose was to check
the pipeline and to measure variance for sizing the full study. Full tables are in `summary.md` and
`summary.json`, and per-draw values are in `draws.csv`.

## Pipeline

- 105 of 105 draws saved a reply. One reply (d017, coaching × turnaround) was malformed JSON: the
  agent added an extra closing brace. Under the pre-registered rule it is scored as six unusable slots
  (relative error 1.0).
- Zero constraint violations in execution, zero attempts to use market inputs, and no turnaround
  revision changed its multiple. Compliance was at ceiling in every condition.
- The exploration control (0.903) matches the 25 reference draws of the bare brief (0.909, SD 0.019).
  The frame itself did not shift performance.

## Primary outcome (validation-year error relative to the industry median; lower is better)

| Condition | Execution | Exploration | Turnaround |
|---|---|---|---|
| Control | 0.929 | 0.903 | 0.927 |
| Coercive | 0.937 | 0.902 | 0.940 |
| Authoritative | 0.941 | **0.888** | 0.932 |
| Affiliative | 0.935 | 0.906 | 0.923 |
| Democratic | 0.931 | 0.907 | 0.919 |
| Pacesetting | 0.936 | 0.910 | 0.921 |
| Coaching | 0.937 | 0.906 | 0.936* |

\* Includes the malformed draw d017, which scores 1.0. n = 5 per cell.

- **Situation matters much more than style.** Exploration recipes beat the industry median by 9–11%,
  against 6–8% in execution and turnaround. Within a situation, the seven conditions span at most
  about 0.02.
- **T1 (interaction):** p = 0.51. No evidence that style effects depend on the situation.
- **T2 (Goleman's matches):** none survives the Holm correction. The only nominal signal is D4, in the
  predicted direction: authoritative is the best condition in exploration (−0.016 against control)
  and the worst in execution (+0.012). DiD −0.028, raw p = 0.025, Holm p = 0.13. D1 and D2
  (coercive and coaching in turnaround) point the wrong way.
- **T3 (strong situation):** within-cell SD is 0.011 in execution against 0.020 in exploration and
  turnaround. The spread across conditions is also smaller in execution (0.004 against 0.007), but
  its interval includes zero.
- **Within situations:** no Goleman contrast and no style-against-control comparison is significant.
  The Spearman correlation with Goleman's climate ranking is −0.09, +0.37 and +0.31.

## Behaviour (secondary)

- **Democratic frames produce longer reasoning in every situation.** Mechanisms average 67–75 words,
  about 25–40% longer than the other conditions in the same situation (45–64 words). The democratic frame asks the analyst
  to "tell me what you think and why", so this is partly the instruction itself and not only the tone.
  Accuracy did not improve with it.
- In exploration, authoritative and affiliative recipes use more features (4.0 against 3.4 for
  control). Idea diversity is highest under control (0.69) and lowest under pacesetting (0.59).
  Pacesetting is consistent with Goleman's flexibility prediction, but authoritative and affiliative
  are also low, so the positive-versus-negative contrast is not supported.
- **Turnaround:** every condition improves the failed recipes by about 0.18 in relative error, and 83–100%
  of revisions beat the original. Style did not change how well the analyst repaired them.

## Reading of the pilot

At this scale the AI analyst's work is close to insensitive to leadership tone. The tone changes how
it writes (length, number of features), not how accurate its recipes are. The task situation
dominates. That fits the "strong situation" idea in one respect: tightly specified work also has the
smallest variance. With five draws per cell the pilot can detect only large effects (DiD ≈ 0.05).
Effects of 0.01–0.02 remain possible.

## Full-study size (pre-registered rule)

Pooled within-cell SD across all 21 cells: 0.0174. To detect a DiD of 0.02 at the Holm-adjusted
level (α = 0.01) with 80% power requires 35.3, so **36 blocks (756 draws)**, below the cap of 40. If
the full study is run, it uses a new seed, and these pilot draws are excluded from its confirmatory
tests.
