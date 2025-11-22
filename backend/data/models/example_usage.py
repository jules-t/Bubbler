"""Example entry points for teammates (UI/TTS) to consume the scoring engine."""

from __future__ import annotations

import json
from pathlib import Path

from scoring_engine import calculate_bubble_score


DATA_PATH = Path(__file__).resolve().parent / "outputs" / "bubble_data.json"


def get_bubble_analysis():
    """Return all metrics + final score from local bubble_data.json."""

    return calculate_bubble_score(DATA_PATH)


def format_for_speech(result: dict) -> str:
    """Produce a speech-friendly summary for TTS teammates."""

    overall = result["overall_bubble_score"]
    state = result["bubble_state"]
    speech = f"The AI bubble risk score is {overall} out of 100. "
    speech += f"Current state: {state.replace('_', ' ').lower()}. "

    speech += "Individual metrics: "
    for name, data in result["metrics"].items():
        metric_state = data["state"].replace("_", " ").lower()
        speech += f"{name}, {data['score']} out of 100, {metric_state}. "

    warnings = result.get("warning_signals", [])
    if warnings:
        speech += "Warning signals: " + " ".join(warnings)

    return speech


if __name__ == "__main__":
    analysis = get_bubble_analysis()
    print("📊 Full Analysis (JSON):")
    print(json.dumps(analysis, indent=2))

    print("\n🎙️ Speech-Ready Format:")
    print(format_for_speech(analysis))
