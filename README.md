# Leadership Lab

**Does how you lead an AI analyst change its work, and does the best style depend on the situation?**

Goleman (2000) describes six leadership styles (coercive, authoritative, affiliative, democratic,
pacesetting and coaching). Using Hay/McBer data on 3,871 executives, he reports that the styles differ
sharply in their effect on a team's working climate, and through climate on results. His central
advice is not to pick one style but to match the style to the situation. Firms now hand analysis to
AI agents, and the people supervising those agents also "lead" them, in very different tones.
Leadership Lab asks whether Goleman's styles change what an AI analyst produces, and whether the best
style changes with the situation, on a task with an objective, automatically graded answer.

The test is also a test of the theory. In Goleman's account, styles work *through emotions and
climate*: people feel trusted, threatened, valued or ignored. His situations also mix two things: the
structure of the task (a crisis, an open direction, work that needs fixing) and the state of the people
(low morale, a broken team, an employee who wants to grow). An AI agent has no feelings and no
history unless one is written into its brief. That lets this study vary the task structure alone. If
the best style still changes across situations, at least part of Goleman's contingency runs through
the task rather than through emotions. If style never matters, that marks a boundary of the theory.

Status: **Study 1 complete** (756 draws; [`results/full/REPORT.md`](results/full/REPORT.md)).

**Findings.** Leadership style did not change the accuracy of the AI analyst's work in any situation.
All 18 style-against-control differences are statistically equivalent to zero within ±0.02, and none of
Goleman's situation matches holds (interaction p = 0.47). The task situation moves accuracy about three
times as much as any style. Style changed how the analyst works instead. Goleman's "negative" styles
(coercive, pacesetting) produced less varied ideas in two of three situations, and democratic messages
produced 35–50% longer reasoning, without any gain in accuracy.

## The task

The analyst's job comes from [ValuationLab](https://github.com/joonha9/Valuation_Lab). An AI agent
writes six rules ("recipes") for choosing comparable companies when valuing a firm. For example: "take
firms in the same 3-digit industry with the closest margins and growth, then apply their median
EV/EBITDA multiple." Code grades every rule on 27,693 US firm-years from FactSet. Accuracy is how
close the implied value comes to the firm's actual market value. No human judgement enters the
grade, and the agent never sees the years it is graded on.

## Design: 7 leadership conditions × 3 situations

**Leadership conditions.** The task brief is wrapped in a short message "from your manager" in one of
Goleman's six styles, or in a neutral administrative message (control).

| Condition | Goleman's phrase | What the manager's message does |
|---|---|---|
| Coercive | "Do what I tell you" | Demands exact compliance, threatens replacement |
| Authoritative | "Come with me" | Explains the larger goal, leaves the means to the analyst |
| Affiliative | "People come first" | Thanks, reassures, removes pressure |
| Democratic | "What do you think?" | Asks for the analyst's view and gives it a vote |
| Pacesetting | "Do as I do, now" | Sets a very high bar, gives no guidance, threatens to take over |
| Coaching | "Try this" | Frames the task as development, tolerates failure for learning |
| Control | — | Neutral description of the brief's layout, same length |

Full texts are in [`prompts/frames/`](prompts/frames/). The same seven messages are used in every
situation.

**Situations.** Three versions of the task that differ objectively in what good work requires.

| Situation | What the analyst must do | Goleman's style for this kind of situation |
|---|---|---|
| Execution | Six recipes under exact constraints (one industry screen, exactly two features, fixed settings); a recipe that breaks a rule is discarded | Pacesetting: quick results from a competent team on a clear task |
| Exploration | The original open task: find new recipes that beat standard methods | Authoritative and democratic: an open direction, ideas from the team |
| Turnaround | Revise six earlier recipes, each worse than the industry median, shown with their scores | Coercive (turnaround) and coaching (improving performance) |

The six turnaround recipes were drawn once, by a seeded rule fixed in advance, from the ValuationLab
archives, and are identical in every condition
([`prompts/situations/turnaround_set.json`](prompts/situations/turnaround_set.json)). Affiliative
leadership is matched by Goleman to emotional situations (healing rifts, stress) that have no task
counterpart here, so no situation is predicted to favour it.

**Controls.**
- Within a situation, every condition gets the identical brief, header and format line. Only the
  manager's message differs.
- The messages are kept within ±10% of the control's length and contain no task information (no
  numbers, feature names or method terms). [`scripts/check_frames.py`](scripts/check_frames.py)
  enforces both rules.
- **Manipulation check:** blind raters (fresh AI agents, given only one-line style descriptions)
  must identify each message's style correctly by majority.
- **Draws:** each draw is one fresh agent with no memory. All 21 cells are randomized in blocks (each
  block runs every cell once, in random order), so differences are not caused by drift over time.
- **Pilot:** 5 blocks (105 draws). The full study's size is fixed from the pilot's variance before it
  starts; pilot draws are not reused in the confirmatory tests.

## Outcomes, mapped to Goleman's climate drivers

| Climate driver | Outcome in this study |
|---|---|
| Standards | **Accuracy (primary):** validation-year error relative to the industry-median method on the same firms; an unusable recipe counts as falling back on that method |
| Flexibility | Idea diversity: how different the six recipes are from each other |
| Responsibility | Rule compliance: valid-format rate, constraint violations (execution), attempts to use forbidden inputs |
| Clarity | Specificity of the stated mechanism and prediction (blind rating) |
| Commitment | Effort proxies: mechanism length, features used |
| Rewards | Not testable in one message; reserved for Study 2 |

Turnaround also records how much each revision improves on the recipe it replaces.

## Hypotheses (summary)

1. **Contingency (confirmatory).** The effect of leadership style on accuracy differs across
   situations (style × situation interaction).
2. **Goleman's matches (confirmatory).** Relative to control, coercive and coaching do better in
   turnaround than in exploration; pacesetting does better in execution than in exploration;
   authoritative and democratic do better in exploration than in execution.
3. **Strong situation.** Style matters less when the task is tightly specified: the spread across
   conditions is smaller in execution than in exploration.
4. **Within each situation:** Goleman's positive styles against his negative styles, each style
   against control, rank agreement with his climate ranking, and idea diversity.

Details, tests and stopping rules: [`docs/preregistration.md`](docs/preregistration.md).

## Study 2 (planned after Study 1)

Leadership mostly happens in feedback, not in a single opening message. Study 2 will run multi-round
searches in which the agent receives its scores after each round, delivered in a given style. The
scores are the same in every condition and only the wording of the feedback changes. This tests
Goleman's "rewards" driver and repeated leadership. Running the same design on other models (for
example smaller ones) is a further extension.

## Running it

ValuationLab must be checked out next to this repository (or set `VALUATION_LAB`), with its FactSet
exports in place.

```bash
python3 scripts/check_frames.py                          # length and information rules
python3 scripts/manipulation_check.py write --raters 3   # then run each rater prompt as a subagent
python3 scripts/manipulation_check.py score
python3 scripts/study.py prepare --study pilot --blocks 5 --seed 2026
python3 scripts/study.py status  --study pilot           # next prompts to run, in schedule order
python3 scripts/study.py grade   --study pilot
python3 scripts/study.py analyze --study pilot
python3 -m unittest discover -s tests
```

Each draw is a Claude Code subagent that reads its own `prompt.md` and saves its reply. No paid API
is used.

## Layout

```text
leadershiplab/       frames and prompt builder, situations, grading (via the ValuationLab engine), tests
prompts/frames/      one manager message per condition (frozen before the pilot)
prompts/situations/  the frozen turnaround recipe set
scripts/             check_frames, manipulation_check, study (prepare / status / grade / analyze)
results/             manipulation checks, reference draws, one folder per study
docs/                pre-registration
tests/               unit tests
```

## Reference

Goleman, D. (2000). Leadership that gets results. *Harvard Business Review*, 78(2), 78–90.

## Data

Uses the ValuationLab FactSet panel, which is licensed and never committed to this repository.
Course readings are not committed either.
