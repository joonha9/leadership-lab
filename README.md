# Leadership Lab

**Does how you manage an AI analyst change its work?**

Firms are starting to hand financial analysis to AI agents, and the people supervising those agents
manage them in very different ways: some give step-by-step orders, some explain why the work matters,
some coach, some barely instruct, some apply pressure. Leadership research has studied these styles
for decades with human teams. Leadership Lab asks whether they also change what an AI analyst
produces, measured on a task with an objective answer.

Status: **design stage.** No runs yet.

## Why this is testable here

[ValuationLab](https://github.com/joonha9/Valuation_Lab) already provides a fixed task with a
deterministic grader: AI agents propose comparable-company valuation rules ("recipes"), and code
grades every rule on 27,693 US firm-years from FactSet, with exploration, validation and sealed
holdout years. Its ablation found that the gain over random search comes from the proposer itself,
not from the referee or the archive. The natural next question is whether the way the proposer is
*instructed* matters.

## Design (draft)

- **Task:** the ValuationLab proposer brief (propose 6 comps recipes, each with a mechanism and a
  falsifiable prediction), with no archive, so every draw is independent.
- **Conditions:** the same brief wrapped in different leadership styles.

  | Style | What the instruction sounds like |
  |---|---|
  | Directive | Exact steps and the criteria the work will be judged on |
  | Transformational | Why the research matters and what it could change |
  | Coaching | Think it through first and explain the reasoning |
  | Laissez-faire | Minimal instruction |
  | High pressure | The result carries high stakes |
  | Neutral (control) | The current ValuationLab brief |

- **Control for information:** every condition carries the same task facts (recipe language,
  features, baseline scores, output format). Only tone and framing change, and condition texts are
  kept within a fixed length band so that style is not confounded with information or length.
- **Outcomes:**
  1. Accuracy (primary): validation-year median |ln(V_est / V)| of each proposed recipe.
  2. Search behaviour: valid-format rate, attempted rule violations (e.g. using market value),
     diversity of ideas, how often extreme settings are tried.
  3. Reasoning quality: specificity of the stated mechanism, rated blind to condition.
- **Unit of analysis:** one draw of 6 proposals. Differences between styles are tested with
  permutation tests on draw-level means. Holdout years stay sealed.
- **Pilot:** 4 styles + control, 10 draws each, before deciding on the full run.

Hypotheses, the analysis plan and stopping rules are fixed in `docs/preregistration.md` before any
draw is made.

## Layout

```text
docs/        pre-registration and design notes
prompts/     one brief per leadership style (frozen before the pilot)
scripts/     draw, grade and analysis scripts (reuse the ValuationLab grader)
results/     raw replies, graded archives, summaries
```

## Data

Uses the ValuationLab FactSet panel. FactSet data is licensed and is never committed to this
repository.
