"""Repeat real Ollama fixture runs and record portable evidence, including failures."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from alphapulse.agents.artifacts import save_json
from alphapulse.agents.monitor import OllamaClient, SNAPSHOTS, run_agent
from alphapulse.agents.transport import request_json


def evaluate(client, output_dir, symbols, repetitions, metadata):
    if (
        not 1 <= repetitions <= 10
        or not symbols
        or any(s not in SNAPSHOTS for s in symbols)
    ):
        raise ValueError("use supported symbols and 1 to 10 repetitions")
    # Require a fresh run directory; never silently replace earlier evidence.
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    save_json(output_dir / "metadata.json", metadata)
    summary = []
    for symbol in dict.fromkeys(symbols):
        for attempt in range(1, repetitions + 1):
            start = time.monotonic()
            result = run_agent(client, symbol)
            result.update(
                mode="ollama",
                model=client.model,
                symbol=symbol,
                elapsed_seconds=round(time.monotonic() - start, 3),
                recorded_at=datetime.now(timezone.utc).isoformat(),
            )
            name = f"{symbol.lower()}-{attempt}.json"
            save_json(output_dir / name, result)
            record = {
                k: result.get(k)
                for k in ("symbol", "status", "error", "elapsed_seconds")
            }
            record["trace_file"] = name
            summary.append(record)
            print(json.dumps(record), flush=True)
    save_json(output_dir / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="new directory for this run"
    )
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument(
        "--host", default=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    parser.add_argument(
        "--symbols", nargs="+", choices=list(SNAPSHOTS), default=list(SNAPSHOTS)
    )
    parser.add_argument("--repetitions", type=int, choices=range(1, 11), default=3)
    parser.add_argument(
        "--code-commit",
        required=True,
        help="source revision tested (git rev-parse HEAD)",
    )
    args = parser.parse_args(argv)
    try:
        client = OllamaClient(args.model, args.host)
        tags = request_json(client.host, "/api/tags")
        # Only record the selected model, not the user's full model inventory or endpoint.
        model = next(m for m in tags["models"] if m["name"] == args.model)
        metadata = {
            "model": args.model,
            "digest": model["digest"],
            "ollama_version": request_json(client.host, "/api/version")["version"],
            "code_commit": args.code_commit,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        results = evaluate(
            client, args.output_dir, args.symbols, args.repetitions, metadata
        )
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as exc:
        # Avoid logging endpoints, credentials, or arbitrary server response bodies.
        parser.exit(
            1,
            "Evaluation failed: "
            + type(exc).__name__
            + ". Check local service, model and new output directory.\n",
        )
    return 0 if all(r["status"] == "completed" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
