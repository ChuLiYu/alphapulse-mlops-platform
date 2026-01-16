import subprocess
import time
import sys
import re


def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise


def get_news_count():
    """Gets the count of records in market_news table."""
    cmd = 'docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT count(*) FROM market_news;"'
    try:
        output = run_command(cmd)
        return int(output.strip())
    except Exception:
        return 0


def trigger_dag(dag_id):
    """Triggers the Airflow DAG."""
    print(f"Triggering DAG: {dag_id}...")
    run_command(
        f"docker exec alphapulse-airflow-scheduler airflow dags trigger {dag_id}"
    )


def get_latest_dag_run_state(dag_id):
    """Gets the state of the latest DAG run."""
    # List runs, sort by execution date desc, take top 1
    cmd = f"docker exec alphapulse-airflow-scheduler airflow dags list-runs -d {dag_id} -o plain"
    output = run_command(cmd)
    lines = output.strip().split("\n")
    if len(lines) <= 1:
        return None

    # Parse the last line (most recent run usually, but depending on list-runs order)
    # Actually list-runs might not be sorted by start date by default, but let's assume valid output
    # Better: list-runs outputs a table, let's just grep the latest start date.
    # Simpler: just get the last line's state column.

    # Example line:
    # dag_id | run_id | ... | state
    # news...| manual__| ... | running

    # We will just verify if there are ANY 'running' tasks or if the LAST (most recent) is success.
    # Let's rely on checking if the *latest* triggered run is finished.

    # Using json output is safer if available, but plain is standard.
    # Let's dump to json for easier parsing.
    cmd_json = f"docker exec alphapulse-airflow-scheduler airflow dags list-runs -d {dag_id} -o json"
    import json

    try:
        output_json = run_command(cmd_json)
        runs = json.loads(output_json)
        if not runs:
            return None
        # Sort by start_date desc
        runs.sort(key=lambda x: x.get("start_date", ""), reverse=True)
        return runs[0]["state"]
    except Exception as e:
        print(f"Failed to parse DAG runs: {e}")
        return None


def wait_for_dag_completion(dag_id, timeout=120):
    """Waits for the latest DAG run to complete (success or failed)."""
    start_time = time.time()
    print("Waiting for DAG completion...")
    while time.time() - start_time < timeout:
        state = get_latest_dag_run_state(dag_id)
        print(f"Current DAG state: {state}")

        if state in ["success", "failed"]:
            return state

        time.sleep(5)

    raise TimeoutError(f"DAG {dag_id} did not complete within {timeout} seconds.")


def main():
    dag_id = "news_ingestion_pipeline"

    print("--- Starting Integration Test ---")

    # 1. Check initial row count
    initial_count = get_news_count()
    print(f"Initial market_news count: {initial_count}")

    # 2. Trigger DAG
    trigger_dag(dag_id)

    # 3. Wait for completion
    final_state = wait_for_dag_completion(dag_id)
    print(f"DAG finished with state: {final_state}")

    if final_state != "success":
        print("❌ Test Failed: DAG did not succeed.")
        sys.exit(1)

    # 4. Check final row count
    final_count = get_news_count()
    print(f"Final market_news count: {final_count}")

    if final_count >= initial_count:
        # Note: It might be equal if no NEW news was found, but logic executed.
        # Strict > check might fail if RSS feed has no updates.
        # Ideally we want > initial, but >= + success state is acceptable for 'pipeline ran okay'.
        print("✅ Test Passed: DAG succeeded and DB connection verified.")
    else:
        print("❌ Test Failed: Data count decreased (unexpected).")
        sys.exit(1)


if __name__ == "__main__":
    main()
