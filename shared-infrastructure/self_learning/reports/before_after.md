# Self-learning v0 — before/after adjustment cycle

*Generated 2026-07-12T01:22:41+00:00 · site `oystermouth-chapel` · v0 (rule-based — NOT a trained model)*
*Data provenance: synthetic — synthetic/replay sessions are labelled as such everywhere they appear.*

**Action:** `LOOSEN` — 8/10 recent sessions landed just below the cutoff yet rendered acceptably via fallback (drift <=0.5m) — cutoff rejects locks that would have worked

| | Before | After |
|---|---|---|
| Threshold version | v1 | v2 |
| `visual_confidence_min` | 0.7 | 0.65 |
| visual locks | 2 | 10 |
| anchor fallbacks | 8 | 0 |
| no usable render | 0 | 0 |

*"Replayed window outcomes" re-applies the visual-lock rule to the same 10
logged sessions under each cutoff — a replay of recorded data, not a prediction of future performance.*

Rollback: re-issue v1 values via `PUT /api/sites/oystermouth-chapel/thresholds`
(every change is an append-only version; nothing is overwritten).
