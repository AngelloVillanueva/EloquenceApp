#!/usr/bin/env python3
"""Compare Ollama models on dual-channel tutor turns (TTFT / dual JSON / VRAM).

Does not change the default OLLAMA_MODEL. Run from repo root:

  .venv\\Scripts\\python.exe scripts/eval_ollama_models.py
  .venv\\Scripts\\python.exe scripts/eval_ollama_models.py --models llama3.1:8b gemma2:9b
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.prompts.tutor_system import SPOKEN_TUTOR_PROMPT, scenario_instruction  # noqa: E402
from app.services.llm import OllamaLLM  # noqa: E402
from app.ws.dual_channel import DualChannelSplitter  # noqa: E402

TURNS = [
    ("free", "Hi — I'm a bit nervous speaking English today. I work in a small office."),
    ("free", "Yesterday I go to the store and I buyed some bread for dinner."),
    ("job", "I have five years of experience as a software engineer in backend systems."),
    ("job", "My weakness is that I am too perfectionist and I take too much time."),
    ("free", "Can you help me say that last idea more naturally?"),
]


def gpu_memory_mb() -> dict[str, int | None]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=8,
        )
        used, total = [int(x.strip()) for x in out.strip().split(",")[:2]]
        return {"used_mb": used, "total_mb": total}
    except Exception:  # noqa: BLE001
        return {"used_mb": None, "total_mb": None}


def run_turn(llm: OllamaLLM, model: str, scenario: str, user: str) -> dict:
    system = f"{SPOKEN_TUTOR_PROMPT}\n\n{scenario_instruction(scenario)}"
    splitter = DualChannelSplitter()
    t0 = time.perf_counter()
    ttft = None
    ttf_speak = None
    spoken = ""
    raw = ""
    for delta in llm.chat_stream(user, system=system, model=model):
        now = time.perf_counter()
        if ttft is None:
            ttft = now - t0
        raw += delta
        chunk = splitter.push(delta)
        if chunk:
            if ttf_speak is None:
                ttf_speak = now - t0
            spoken += chunk
    spoken += splitter.flush()
    total = time.perf_counter() - t0
    feedback = splitter.parse_feedback()
    return {
        "scenario": scenario,
        "user": user,
        "ttft_s": round(ttft or total, 3),
        "ttf_speak_s": round(ttf_speak or total, 3),
        "total_s": round(total, 3),
        "saw_speak_marker": splitter._saw_speak_marker,
        "saw_feedback_marker": splitter._saw_feedback_marker,
        "raw_has_speak": "<<<SPEAK>>>" in raw.upper().replace(" ", ""),
        "raw_has_feedback": "<<<FEEDBACK>>>" in raw.upper().replace(" ", ""),
        "feedback_ok": feedback is not None,
        "feedback_keys": sorted(feedback.keys()) if isinstance(feedback, dict) else [],
        "speak_has_json": "{" in spoken,
        "speak_chars": len(spoken.strip()),
        "speak_preview": spoken.strip()[:160],
        "raw_preview": raw[:220],
    }


def eval_model(llm: OllamaLLM, model: str) -> dict:
    vram_before = gpu_memory_mb()
    t_warm = time.perf_counter()
    llm.warmup_model(model)
    warmup_s = round(time.perf_counter() - t_warm, 2)
    vram_warm = gpu_memory_mb()
    turns = [run_turn(llm, model, sc, utt) for sc, utt in TURNS]
    vram_after = gpu_memory_mb()
    ttf_speak = [t["ttf_speak_s"] for t in turns]
    dual_ok = sum(1 for t in turns if t["saw_speak_marker"] and t["feedback_ok"])
    warm_tts = ttf_speak[1:] or ttf_speak
    return {
        "model": model,
        "warmup_s": warmup_s,
        "vram_before_mb": vram_before["used_mb"],
        "vram_warm_mb": vram_warm["used_mb"],
        "vram_after_mb": vram_after["used_mb"],
        "vram_total_mb": vram_warm["total_mb"],
        "mean_ttf_speak_s": round(sum(ttf_speak) / len(ttf_speak), 3),
        "mean_ttf_speak_warm_s": round(sum(warm_tts) / len(warm_tts), 3),
        "mean_ttft_s": round(sum(t["ttft_s"] for t in turns) / len(turns), 3),
        "mean_total_s": round(sum(t["total_s"] for t in turns) / len(turns), 3),
        "dual_ok": f"{dual_ok}/{len(turns)}",
        "json_leaked_to_speak": sum(1 for t in turns if t["speak_has_json"]),
        "turns": turns,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["llama3.1:8b", "gemma2:9b"])
    args = parser.parse_args()
    llm = OllamaLLM()
    available = llm.list_models()
    results = []
    for name in args.models:
        if not any(name == m or m.startswith(name) for m in available):
            print(f"SKIP {name}: not pulled. Available: {available}")
            continue
        print(f"\n=== {name} ===")
        row = eval_model(llm, name)
        results.append(row)
        print(
            json.dumps(
                {k: v for k, v in row.items() if k != "turns"},
                indent=2,
            )
        )
        for t in row["turns"]:
            print(
                f"  [{t['scenario']}] ttf_speak={t['ttf_speak_s']}s dual="
                f"{t['saw_speak_marker']}/{t['feedback_ok']} json_leak={t['speak_has_json']} "
                f"speak={t['speak_preview']!r}"
            )
    # Restore the product default so the next session is not a Gemma cold-swap.
    if "llama3.1:8b" in args.models or any("llama3.1" in m for m in available):
        print("\nReloading default llama3.1:8b into VRAM...")
        llm.warmup_model("llama3.1:8b")
    out = ROOT / "data" / "output" / "gemma_vs_llama.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
