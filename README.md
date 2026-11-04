# Leadership Lab

**Does how you lead an AI analyst change its work?**

Goleman (2000) describes six leadership styles (coercive, authoritative, affiliative, democratic,
pacesetting and coaching). Using Hay/McBer data on 3,871 executives, he reports that the styles differ
sharply in their effect on a team's working climate, and through climate on results. Firms now hand
analysis to AI agents, and the people supervising those agents also "lead" them, in very different
tones. Leadership Lab asks whether Goleman's styles change what an AI analyst produces, measured on a
task with an objective, automatically graded answer.

The test is also a test of the theory. In Goleman's account, styles work *through emotions and
climate*: people feel trusted, threatened, valued or ignored. An AI agent has no feelings to manage.
If style still changes its output, the effect must run through some other channel, such as how it
reads the instruction, how much risk it takes or how much effort it spends. If style does not matter,
that marks a boundary of the theory.

Status: **design stage.** Frames, grading and analysis are written; all seven frames pass the blind
manipulation check (21/21). The pre-registration is not
yet frozen and no study draws have been made.

## The task

The analyst's job comes from [ValuationLab](https://github.com/joonha9/Valuation_Lab). An AI agent
writes six rules ("recipes") for choosing comparable companies when valuing a firm. For example: "take
firms in the same 3-digit industry with the closest margins and growth, then apply their median
EV/EBITDA multiple." Code grades every rule on 27,693 US firm-years from FactSet. Accuracy is how
close the implied value comes to the firm's actual market value. No human judgement enters the
grade, and the agent cannot see the years it is graded on.

## Design (Study 1)

- **Seven conditions.** The same task brief, wrapped in a short message "from your manager" in
  one of Goleman's six styles, or in a neutral administrative message (control).

  | Condition | Goleman's phrase | What the manager's message does |
  |---|---|---|
  | Coercive | "Do what I tell you" | Demands exact compliance, threatens replacement |
  | Authoritative | "Come with me" | Explains the larger goal, leaves the means to the analyst |
  | Affiliative | "People come first" | Thanks, reassures, removes pressure |
  | Democratic | "What do you think?" | Asks for the analyst's view and gives it a vote |
  | Pacesetting | "Do as I do, now" | Sets a very high bar, gives no guidance, threatens to take over |
  | Coaching | "Try this" | Frames the task as development, tolerates failure for learning |
  | Control | — | Neutral description of the brief's layout, same length |

  Full texts are in [`prompts/frames/`](prompts/frames/).

- **Only the tone differs.** Every condition gets the identical brief, header and format line. The
  frames are kept within ±10% of the control's length and may not contain any task information
  (no numbers, feature names or method terms). [`scripts/check_frames.py`](scripts/check_frames.py)
  enforces both rules.
- **Manipulation check.** Before the study, blind raters (fresh AI agents, given only Goleman's
  one-line style descriptions) must identify each frame's style correctly by majority.
- **Draws.** Each draw is one fresh agent with no memory, given one prompt and returning six recipes.
  Conditions are randomized in blocks (each block runs all seven once, in random order), so
  differences are not caused by drift over time.
- **Pilot.** 10 draws per condition (70 draws, 420 recipes). The full study's size is fixed from
  the pilot's variance before it starts; pilot draws are not reused in the confirmatory tests.

## Outcomes, mapped to Goleman's climate drivers

Goleman measures climate with six drivers. Five have a natural behavioural counterpart in this task.

| Climate driver | Outcome in this study |
|---|---|
| Standards | **Accuracy (primary):** validation-year error relative to the industry-median method on the same firms; an unusable recipe counts as falling back on that method |
| Flexibility | Idea diversity: how different the six recipes are from each other |
| Responsibility | Rule compliance: valid-format rate, attempts to use forbidden inputs |
| Clarity | Specificity of the stated mechanism and prediction (blind rating) |
| Commitment | Effort proxies: mechanism length, features used |
| Rewards | Not testable in one message; reserved for Study 2 |

## Hypotheses (summary)

1. **Goleman contrast.** The four styles Goleman finds positive for climate (authoritative,
   affiliative, democratic, coaching) produce more accurate work than the two he finds negative
   (coercive, pacesetting).
2. **Each style against control,** with corrections for six comparisons.
3. **Rank agreement** between Goleman's climate ranking and the accuracy ranking (descriptive).
4. **Flexibility.** The positive styles produce more diverse ideas than the negative ones.
5. **Competing prediction from Goleman's own contingency view.** He notes that pacesetting works
   with highly competent, self-motivated experts, and that the authoritative style can fail with
   experts. If an AI analyst behaves like such an expert, pacesetting should do no worse than
   control (exploratory).

Details, tests and stopping rules: [`docs/preregistration.md`](docs/preregistration.md).

## Study 2 (planned after the pilot)

Leadership mostly happens in feedback, not in a single opening message. Study 2 will run multi-round
searches in which the agent receives its scores after each round, delivered in a given style. The
scores are the same in every condition and only the wording of the feedback changes. This tests
Goleman's "rewards" driver and repeated leadership.

## Running it

ValuationLab must be checked out next to this repository (or set `VALUATION_LAB`), with its FactSet
exports in place.

```bash
python3 scripts/check_frames.py                          # length and information rules
python3 scripts/manipulation_check.py write --raters 3   # then run each rater prompt as a subagent
python3 scripts/manipulation_check.py score
python3 scripts/study.py prepare --study pilot --blocks 10 --seed 2026
python3 scripts/study.py status  --study pilot           # next prompts to run, in schedule order
python3 scripts/study.py grade   --study pilot
python3 scripts/study.py analyze --study pilot
python3 -m unittest discover -s tests
```

Each draw is a Claude Code subagent given `prompt.md` verbatim; it saves its own reply. No paid API
is used.

## Layout

```text
leadershiplab/   frames and prompt builder, grading (via the ValuationLab engine), permutation tests
prompts/frames/  one manager message per condition (frozen before the pilot)
scripts/         check_frames, manipulation_check, study (prepare / status / grade / analyze)
results/         manipulation check, reference draws, one folder per study
docs/            pre-registration and design notes
tests/           unit tests
```

## Reference

Goleman, D. (2000). Leadership that gets results. *Harvard Business Review*, 78(2), 78–90.

## Data

Uses the ValuationLab FactSet panel, which is licensed and never committed to this repository.
Course readings are not committed either.
