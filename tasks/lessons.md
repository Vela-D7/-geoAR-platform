# Lessons — patterns, not just fixes

Reviewed at the start of every session on this project. Sourced from real
corrections (self-caught or from Vela); newest first.

## 2026-07-12 — design synthetic data at the *aggregation* level
The seeded "near-miss" dusk sessions initially never tripped the self-learning
rule because the session log records **best** confidence over the session, and
the chosen scenario peaked above the cutoff before degrading. The tick-level
story and the aggregated row told different stories.
**Rule:** when synthesising data to exercise a downstream consumer, assert on
the *aggregated record* the consumer actually reads, not the raw feed. Add a
test that the seed data actually trips the rule it exists to demonstrate.

## 2026-07-12 — a correct adjustment can still be an invisible demo
The first LOOSEN cycle was real but the before/after outcome table showed no
change (2→2 locks) because the loosened cutoff still sat above the synthetic
confidences. Fix was to place the data just under the old cutoff and above the
new one.
**Rule:** for any "before/after" demo artifact, verify the *visible delta*, not
just that the mechanism fired.

## 2026-07-12 — cwd-relative resource paths break cross-package runners
`sqlite:///./geoar.db` resolved differently for the API (run from `backend/`)
and the self-learning runner (run from `shared-infrastructure/`), silently
creating a second empty DB.
**Rule:** default file-based resources to absolute paths anchored at the owning
package (`Path(__file__)`), never the process cwd.

## 2026-07-12 (repeat offence) — process management must be isolated tool calls
Re-broke the pkill rule the same day it was written, by chaining
`pkill … ; (worker &) && sleep …` in one compound command: the pattern matched
the invoking shell again, and the harness blocks foreground `sleep`. The
compound died mid-chain (exit 144) leaving a half-started stack.
**Rule (supersedes the entry below):** never mix process kill/start/wait in one
compound command. Kill via `pgrep`+PID in its own call, start long-lived
processes with the harness's background-task mechanism, and wait by polling in
a separate call. If a lesson exists, *reread it before writing shell that
touches the same territory* — that is what this file is for.

## 2026-07-12 — pkill patterns can match their own invocation
`pkill -f "next-server"` matched the shell running the compound command and
killed it (exit 144), aborting the rest of the chain.
**Rule:** bracket a character (`pkill -f 'next[-]server'`) or use pgrep+PID,
and never chain `pkill` with `&&` onto work that must still run.

## 2026-07-12 — spec-conformance beats spec-adjacent invention
XREAL NRSDK anchor API names were not verifiable in this environment; instead
of inventing calls, the adapter compiles behind `XREAL_SDK_PRESENT` with the
call sites left explicitly unwritten and tagged [Needs verification].
**Rule:** when an SDK surface can't be verified, ship the seam + loud stub, not
plausible-looking code that will silently fail review on the dev machine.
