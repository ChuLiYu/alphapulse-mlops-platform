# LLM and agent evidence audit

Audited on 2026-10-18. Baseline: AlphaPulse main commit
`2d1db3fee1f5e027d2c7130cc24b1510573b1be8`.

| Component | Source evidence | What can be claimed |
| --- | --- | --- |
| LLM sentiment classification | [SentimentAnalyzer.classify_text](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/airflow/plugins/alphapulse_utils/sentiment_analyzer.py) posts a prompt to Ollama `/api/generate` and parses JSON | A real LLM integration exists in source. This audit did not verify deployment or a real inference run. |
| News pipeline | [news_sentiment_dag.py](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/airflow/dags/news_sentiment_dag.py) loads news, invokes classification, saves scores | An Airflow pipeline incorporating an LLM; each article uses one LLM call. The model does not choose tools or coordinate the workflow. |
| Explanation field | [signals.py](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/src/alphapulse/api/routes/signals.py) returns hard-coded summaries under `llm_summary` | A mock explanation; do not present it as model-generated text. |
| Installed libraries | [setup.py](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/src/setup.py) lists LangChain, OpenAI and Groq | Dependency declarations alone do not prove agent functionality. |
| New monitoring PoC | [monitor.py](../../src/alphapulse/agents/monitor.py), [tests](../../tests/agent_poc/test_monitor.py), [guide](README.md) | Implemented native Ollama tool-calling adapter and bounded multi-turn runtime, validated offline and with real Ollama runs on synthetic fixtures; see records below. |

## Scope and missing evidence

No model-driven tool-call loop was found in the baseline public AlphaPulse source
by inspection and searches for `tool_calls`, `bind_tools`, `langgraph`, and agent
implementations. This does not rule out unpublished work.

The `private` Git submodule was not initialized or audited. The separate project
called **Portfolio & Risk Analytics** could not be identified from the connected
repository listing. The public `ChuLiYu/liyu-portfolio` main at
`9294abdc07669dfab3765a0941f93736bf59758c` was inspected as a possible pointer;
it is a portfolio website linking AlphaPulse, Raft-Recovery, and Chainy and did
not identify that project. No conclusion about LLM support in Portfolio & Risk
Analytics is warranted until its actual repository is supplied.

## Verification record for this change

- Offline protocol suite: 13 passed; live Ollama test skipped by default.
- Scripted BTC replay: two successful tool calls on separate turns, then summary;
  trace committed as [replay-btc.json](../../examples/agent/replay-btc.json).
- Real model runs, 2026-10-18: **6/6 completed**, BTCUSDT 3/3 and ETHUSDT
  3/3, using Ollama 0.40.6 and `qwen3:4b` at source commit
  `2593bd66f2a8bdc3bf679447c50692bc1250b62c`. Each run called `get_snapshot`
  on turn 1, `evaluate_snapshot` on turn 2, then produced a final summary.
  All six summaries were manually checked: metrics, thresholds and review/ok
  classifications matched tool evaluations. The runtime does not automatically
  verify free-text semantics. These six runs do not establish general reliability.
  [Metadata](../../examples/agent/live/original/metadata.json),
  [summary](../../examples/agent/live/original/summary.json) and adjacent fixture
  traces preserve the evidence without local paths or the full model inventory.
- Security regression suite: 9 passed (SQLite API boundary and mocked sentiment,
  plus Compose policy); see [security scope](SECURITY_REVIEW.md).
- Existing production services and full ML/database test suite were not exercised
  by this isolated PoC validation.
