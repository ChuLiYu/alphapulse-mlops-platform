"""
Promote the best model from MLflow experiments to the Model Registry.
This script automates the transition from raw experiment to a versioned model.
"""

import os
import mlflow
from mlflow.tracking import MlflowClient


def promote_best_model():
    # 1. Configuration from environment variables
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5002")
    experiment_name = "ultra_fast_production"
    model_name = "AlphaPulse_BTC_Model"

    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()

    print(f"Searching for the best run in experiment: {experiment_name}...")

    # 2. Find the experiment ID
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        print(f"Error: Experiment '{experiment_name}' not found.")
        return

    # 3. Search for the best run based on test_r2 (Descending)
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="",
        run_view_type=mlflow.entities.ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.test_r2 DESC"],
    )

    if not runs:
        print("No successful runs found.")
        return

    best_run = runs[0]
    run_id = best_run.info.run_id
    r2_score = best_run.data.metrics.get("test_r2", 0)

    print(f"Best Run Found: {run_id}")
    print(f"Metric (Test R2): {r2_score:.4f}")

    # 4. Register the model in the Registry
    print(f"Registering model as '{model_name}'...")
    source_uri = f"s3://alphapulse/mlflow-artifacts/{experiment.experiment_id}/{run_id}/artifacts/model"

    # Ensure the registered model exists
    try:
        client.create_registered_model(model_name)
    except Exception:
        print("Model already exists in registry.")

    model_version = client.create_model_version(
        name=model_name, source=source_uri, run_id=run_id
    )

    # 5. Transition to 'Staging' stage
    import time

    time.sleep(2)  # Give it a moment to stabilize
    print(f"Transitioning version {model_version.version} to 'Staging'...")
    client.transition_model_version_stage(
        name=model_name,
        version=model_version.version,
        stage="Staging",
        archive_existing_versions=True,  # Archive old staging models
    )

    print(f"SUCCESS: Model version {model_version.version} is now in STAGING.")


if __name__ == "__main__":
    promote_best_model()
