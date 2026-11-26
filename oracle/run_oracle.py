"""CLI — wire T1..T5 and print an auditable necessity report.

Usage:
    python -m oracle.run_oracle            # default 24 seeds
    python -m oracle.run_oracle --seeds 48

The report prints the pre-registration hash first, so a reviewer can confirm the
signed predictions were fixed before these numbers existed.
"""

from __future__ import annotations

import argparse

from oracle.benchmark import PHASE_CONTEXTS, PhaseContext
from oracle.oracle import Verdict, adjudicate, run_battery
from oracle.predictions import registry_hash


def _format(verdicts: list[Verdict], n_seeds: int, phase_context: PhaseContext) -> str:
    lines = [
        "=" * 74,
        "NECESSITY-GATED RETRIEVAL ORACLE  -  Hippocampal-CA1-LAM",
        "=" * 74,
        f"Pre-registration sha256 : {registry_hash()}",
        f"Seeds                   : {n_seeds}",
        f"Phase context           : {phase_context}",
        "Scope                   : synthetic associative-recall ablation",
        "-" * 74,
        f"{'mechanism':<26}{'metric':<26}{'Δ(base-ko)':>11}{'verdict':>11}",
        "-" * 74,
    ]
    for v in verdicts:
        lines.append(f"{v.mechanism:<26}{v.metric:<26}{v.mean_delta:>+11.3f}{v.verdict:>11}")
    lines.append("-" * 74)
    for v in verdicts:
        lines.append(
            f"  {v.knockout:<12} base={v.mean_base:.3f} ko={v.mean_ko:.3f} "
            f"95%CI=[{v.ci_low:+.3f},{v.ci_high:+.3f}] pred_sign={v.predicted_sign:+d}"
        )
    n_pass = sum(v.verdict == "PASS" for v in verdicts)
    n_ref = sum(v.verdict == "REFUTED" for v in verdicts)
    n_null = sum(v.verdict == "NULL" for v in verdicts)
    lines.append("=" * 74)
    lines.append(
        f"SUMMARY: {n_pass} PASS / {n_ref} REFUTED / {n_null} NULL  "
        f"(of {len(verdicts)} pre-registered mechanisms)"
    )
    lines.append(
        "PASS supports the signed task effect. REFUTED supports the opposite sign. "
        "NULL leaves the sign unresolved."
    )
    lines.append("=" * 74)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the necessity-gated retrieval oracle.")
    parser.add_argument("--seeds", type=int, default=24, help="number of seeds (default 24)")
    parser.add_argument("--phase-context", choices=PHASE_CONTEXTS, default="matched")
    args = parser.parse_args()
    if args.seeds < 2:
        parser.error("--seeds must be at least 2")

    seeds = list(range(args.seeds))
    phase_context: PhaseContext = args.phase_context
    battery = run_battery(seeds, phase_context=phase_context)
    verdicts = adjudicate(battery)
    print(_format(verdicts, len(seeds), phase_context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
