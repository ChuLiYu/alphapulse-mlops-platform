"""No database, credentials, network, or heavyweight ML dependencies required."""

import copy
import json
import os
import unittest
from unittest.mock import patch

from alphapulse.agents.monitor import OllamaClient, ReplayClient, run_agent


def call(name, **arguments):
    return {"function": {"name": name, "arguments": arguments}}


class Script:
    def __init__(self, turns):
        self.turns = iter(turns)
        self.histories = []

    def chat(self, messages, tools):
        self.histories.append(copy.deepcopy(messages))
        return next(self.turns)


def assistant(*calls, content=""):
    return {"role": "assistant", "tool_calls": list(calls), "content": content}


class AgentTests(unittest.TestCase):
    def test_dependent_tools_receive_results_on_separate_turns(self):
        client = Script(
            [
                assistant(call("get_snapshot", symbol="BTCUSDT")),
                assistant(call("evaluate_snapshot", snapshot_id="fixture-btc-001")),
                assistant(content="Synthetic BTC snapshot requires review."),
            ]
        )
        result = run_agent(client)
        self.assertEqual(result["status"], "completed")
        self.assertEqual([t["turn"] for t in result["trace"]], [1, 2])
        self.assertEqual(
            json.loads(client.histories[1][-1]["content"])["snapshot_id"],
            "fixture-btc-001",
        )
        evaluation = json.loads(client.histories[2][-1]["content"])
        self.assertEqual(evaluation["status"], "review")
        self.assertEqual(len(evaluation["checks"]), 3)
        self.assertTrue(all(c["breached"] for c in evaluation["checks"]))

    def test_healthy_fixture(self):
        result = run_agent(ReplayClient("ETHUSDT"), symbol="ETHUSDT")
        self.assertEqual(result["evaluations"][0]["status"], "ok")
        self.assertFalse(any(c["breached"] for c in result["evaluations"][0]["checks"]))

    def test_reject_unknown_tool_malformed_arguments_and_scope_escape(self):
        for bad_call in [
            call("execute_shell", command="whoami"),
            call("get_snapshot", symbol="ETHUSDT"),
            call("get_snapshot", symbol="BTCUSDT", path="/etc/passwd"),
            {"function": {"name": "get_snapshot", "arguments": "{broken"}},
            None,
        ]:
            with self.subTest(bad_call=bad_call):
                result = run_agent(Script([assistant(bad_call)]), max_turns=1)
                self.assertEqual(
                    result["trace"][0]["result"]["error"], "invalid_tool_call"
                )
                self.assertEqual(result["status"], "incomplete")

    def test_same_turn_dependency_is_rejected_then_recovers(self):
        result = run_agent(
            Script(
                [
                    assistant(
                        call("get_snapshot", symbol="BTCUSDT"),
                        call("evaluate_snapshot", snapshot_id="fixture-btc-001"),
                    ),
                    assistant(call("evaluate_snapshot", snapshot_id="fixture-btc-001")),
                    assistant(content="Review the synthetic metrics."),
                ]
            )
        )
        self.assertEqual(result["trace"][1]["result"]["error"], "invalid_tool_call")
        self.assertEqual(result["status"], "completed")

    def test_fabricated_snapshot_is_rejected(self):
        result = run_agent(
            Script([assistant(call("evaluate_snapshot", snapshot_id="invented"))]),
            max_turns=1,
        )
        self.assertEqual(result["evaluations"], [])

    def test_premature_final_and_empty_summary_never_complete(self):
        result = run_agent(
            Script([assistant(content="Everything is fine")]), max_turns=1
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["trace"][0]["event"], "premature_final_rejected")
        result = run_agent(
            Script(
                [
                    assistant(call("get_snapshot", symbol="BTCUSDT")),
                    assistant(call("evaluate_snapshot", snapshot_id="fixture-btc-001")),
                    assistant(content=""),
                ]
            ),
            max_turns=3,
        )
        self.assertEqual(result["status"], "incomplete")

    def test_budgets_bound_loop_and_large_tool_batches(self):
        result = run_agent(
            Script([assistant(call("get_snapshot", symbol="BTCUSDT"))] * 3),
            max_turns=3,
        )
        self.assertEqual(result["error"], "model_turn_budget_exhausted")
        result = run_agent(
            Script([assistant(*[call("get_snapshot", symbol="BTCUSDT")] * 20)]),
            max_tool_calls=2,
        )
        self.assertEqual(result["error"], "tool_call_budget_exhausted")
        self.assertEqual(len(result["trace"]), 2)

    def test_bad_model_response_and_transport_error_fail_closed(self):
        for message in [
            None,
            {"role": "user"},
            assistant(content=7),
            {"role": "assistant", "tool_calls": "bad"},
        ]:
            result = run_agent(Script([message]), max_turns=1)
            self.assertEqual(result["status"], "incomplete")
        with patch(
            "alphapulse.agents.monitor.request_json", side_effect=TimeoutError("secret")
        ):
            result = run_agent(OllamaClient("test", "http://localhost:11434"))
        self.assertEqual(result["error"], "model_response_error:TimeoutError")
        self.assertNotIn("secret", json.dumps(result))

    def test_ollama_payload_and_thinking_is_not_recorded(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OLLAMA_NUM_THREAD", None)
            client = OllamaClient("test", "http://localhost:11434")
        with patch("alphapulse.agents.monitor.request_json") as request:
            request.return_value = {
                "message": {
                    "role": "assistant",
                    "content": "done",
                    "thinking": "hidden",
                }
            }
            message = client.chat([], [])
        payload = request.call_args.args[2]
        self.assertEqual(payload["model"], "test")
        self.assertIs(payload["think"], False)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"], {"temperature": 0, "num_predict": 1024})
        self.assertNotIn("thinking", message)

    def test_ollama_num_thread_is_optional_and_bounded(self):
        with patch.dict(os.environ, {"OLLAMA_NUM_THREAD": ""}):
            client = OllamaClient("test", "http://localhost:11434")
            with patch("alphapulse.agents.monitor.request_json") as request:
                request.return_value = {"message": {"role": "assistant"}}
                client.chat([], [])
            self.assertNotIn("num_thread", request.call_args.args[2]["options"])

        for value in ("1", "2", "32"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"OLLAMA_NUM_THREAD": value}
            ):
                client = OllamaClient("test", "http://localhost:11434")
                with patch("alphapulse.agents.monitor.request_json") as request:
                    request.return_value = {"message": {"role": "assistant"}}
                    client.chat([], [])
                self.assertEqual(
                    request.call_args.args[2]["options"]["num_thread"], int(value)
                )

        for value in ("0", "33", "2.0", "-1", "abc", "２"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"OLLAMA_NUM_THREAD": value}
            ), self.assertRaises(ValueError):
                OllamaClient("test", "http://localhost:11434")

    def test_ollama_thinking_markers_are_removed_without_losing_tool_calls(self):
        tool_calls = [call("get_snapshot", symbol="BTCUSDT")]
        cases = [
            ("prefix<think>private text</think>final answer", "final answer"),
            ("private text</think>final answer", "final answer"),
            ("<think>private text without closing", ""),
        ]
        for raw_content, expected in cases:
            with self.subTest(expected=expected), patch(
                "alphapulse.agents.monitor.request_json",
                return_value={
                    "message": {
                        "role": "assistant",
                        "content": raw_content,
                        "tool_calls": tool_calls,
                    }
                },
            ):
                message = OllamaClient(
                    "test", "http://localhost:11434"
                ).chat([], [])
            self.assertEqual(message["content"], expected)
            self.assertEqual(message["tool_calls"], tool_calls)

    @unittest.skipUnless(
        os.getenv("ALPHAPULSE_LIVE_AGENT") == "1", "opt-in real Ollama run"
    )
    def test_live_ollama_tool_chain(self):
        result = run_agent(
            OllamaClient(
                os.getenv("ALPHAPULSE_AGENT_MODEL", "qwen3:4b"),
                os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            )
        )
        self.assertEqual(result["status"], "completed", result)
        self.assertEqual(result["evaluations"][0]["status"], "review")
        successful = [t for t in result["trace"] if "error" not in t.get("result", {})]
        reads = [t["turn"] for t in successful if t.get("tool") == "get_snapshot"]
        checks = [t["turn"] for t in successful if t.get("tool") == "evaluate_snapshot"]
        self.assertLess(min(reads), min(checks))


if __name__ == "__main__":
    unittest.main()
