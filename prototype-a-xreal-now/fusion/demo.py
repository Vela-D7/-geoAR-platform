"""Run every mock scenario through the fusion machine and print the state
trajectory + emitted session log. Writes output/fusion_sessions.jsonl.

Usage: cd prototype-a-xreal-now && python -m fusion.demo
"""

from __future__ import annotations

import json
from pathlib import Path

from .mocks import ALL_SCENARIOS
from .session import run_session
from .state_machine import FusionStateMachine


def main() -> None:
    out = Path("output")
    out.mkdir(exist_ok=True)
    log_path = out / "fusion_sessions.jsonl"

    with log_path.open("w") as fh:
        for factory in ALL_SCENARIOS:
            scenario = factory()
            machine = FusionStateMachine()
            trajectory = [machine.step(t).state.value for t in scenario.ticks]

            print(f"\n=== {scenario.name} — {scenario.description}")
            print("    " + " -> ".join(trajectory))

            record = run_session(scenario)
            print(f"    outcome={record['outcome']}  final={record['final_state']}  "
                  f"time_to_lock={record['time_to_lock_s']}s  flags={record['flags']}")
            fh.write(json.dumps(record) + "\n")

    print(f"\nsession logs (source=synthetic): {log_path}")


if __name__ == "__main__":
    main()
