# LLM and agent evidence audit

Audited on 2026-10-18. Baseline: AlphaPulse main commit
`2d1db3fee1f5e027d2c7130cc24b1510573b1be8`.

| Component | Source evidence | What can be claimed |
| --- | --- | --- |
| LLM sentiment classification | [SentimentAnalyzer.classify_text](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/airflow/plugins/alphapulse_utils/sentiment_analyzer.py) posts a prompt to Ollama `/api/generate` and parses JSON | A real LLM integration exists in source. This audit did not verify deployment or a real inference run. |
| News pipeline | [news_sentiment_dag.py](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/airflow/dags/news_sentiment_dag.py) loads news, invokes classification, saves scores | An Airflow pipeline incorporating an LLM; each article uses one LLM call. The model does not choose tools or coordinate the workflow. |
| Explanation field | [signals.py](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/src/alphapulse/api/routes/signals.py) returns hard-coded summaries under `llm_summary` | A mock explanation; do not present it as model-generated text. |
| Installed libraries | [setup.py](https://github.com/ChuLiYu/alphapulse-mlops-platform/blob/2d1db3fee1f5e027d2c7130cc24b1510573b1be8/src/setup.py) lists LangChain, OpenAI and Groq | Dependency declarations alone do not prove agent functionality. |
| New monitoring PoC | [monitor.py](../../src/alphapulse/agents/monitor.py), [tests](../../tests/agent_poc/test_monitor.py), [guide](README.md) | Implemented native Ollama tool-calling adapter and bounded multi-turn runtime, validated offline with a scripted client. Real model run remains unverified. |

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

- Offline protocol suite: 9 passed; live Ollama test skipped by default.
- Scripted BTC replay: two successful tool calls on separate turns, then summary;
  trace committed as [replay-btc.json](../../examples/agent/replay-btc.json).
- Real model run: **not executed**; Ollama executable was not installed in the
  implementation environment. Do not describe this change as a live-validated
  or production agent until completing the guide's real-model checks.
- Existing production services and full ML/database test suite were not exercised
  by this isolated PoC validation.
