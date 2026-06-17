# Why the Severity Model Was Removed

## Decision
The severity machine-learning model was **intentionally removed** from the
system. Severity is now produced by a transparent rule derived from the
predicted resolution-time class, implemented in `src/rules_engine.py`.

## What the investigation found
During Phase 3, the severity classifier scored ~99.8% weighted F1 across all
three algorithms — a result far too high to be genuine. Investigation showed:

- Severity is almost entirely determined by **location identity**, not by
  incident characteristics.
- Nearly all monitored corridors are labelled **High**; nearly all
  non-corridor locations are labelled **Low**. 8,153 of 8,173 rows obey the
  single rule *"on a monitored corridor ⟺ High priority."*
- The models reached 99.8% F1 only by **memorising the location → severity
  mapping** (the dominant feature was `corridor_frequency`, effectively a
  corridor identifier).
- When location identity was removed, severity prediction fell to **~59% F1**,
  *below* the always-High baseline of 61.5% — i.e. there is essentially **no
  genuine incident-level signal** for severity.

## Conclusion
Severity in this dataset is an **administrative, location-based label**, not a
learnable outcome. Training a model on it produces an impressive-looking but
misleading score: the "model" is just a lookup table for which corridors are
monitored.

## Why rules are better here
Replacing the model with an explicit rule:

- **Improves interpretability** — the logic is one readable mapping, not an
  opaque 300-tree ensemble.
- **Improves trustworthiness** — no inflated accuracy claim that collapses
  under scrutiny.
- **Is easy to govern** — thresholds live in `config.py` and can be changed by
  a traffic authority without retraining anything.

## New design
The only machine-learning prediction is **resolution-time class**
(Quick / Moderate / Prolonged), produced by **LightGBM** (selected as best by
weighted F1, tie-broken on recall). Severity, impact score, and resource
recommendations are all transparent rules layered on top of that prediction.