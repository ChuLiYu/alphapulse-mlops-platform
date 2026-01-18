import mlflow
import os
import sys
import time


def verify_mlflow():
    print("========================================")
    print("🔍 Verifying MLflow Connection")
    print("========================================")

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    print(f"🔹 MLFLOW_TRACKING_URI: {tracking_uri}")

    if not tracking_uri:
        print("❌ Error: MLFLOW_TRACKING_URI is not set.")
        return False

    try:
        # Set tracking URI
        mlflow.set_tracking_uri(tracking_uri)
        print("✅ Tracking URI set.")

        # Create or get experiment
        experiment_name = "manual_verification"
        print(f"🔹 Setting experiment: {experiment_name}")
        mlflow.set_experiment(experiment_name)
        experiment = mlflow.get_experiment_by_name(experiment_name)
        print(f"✅ Experiment ID: {experiment.experiment_id}")

        # Start run
        run_name = f"verify_{int(time.time())}"
        print(f"🔹 Starting run: {run_name}")
        with mlflow.start_run(run_name=run_name) as run:
            print(f"✅ Run started with ID: {run.info.run_id}")

            # Log param
            print("🔹 Logging parameter...")
            mlflow.log_param("test_param", "manual_test")
            print("✅ Parameter logged.")

            # Log metric
            print("🔹 Logging metric...")
            mlflow.log_metric("test_metric", 123.45)
            print("✅ Metric logged.")

            # Log artifact (create a dummy file)
            print("🔹 Logging artifact...")
            with open("test_artifact.txt", "w") as f:
                f.write("This is a test artifact.")
            mlflow.log_artifact("test_artifact.txt")
            print("✅ Artifact logged.")

        print("\n🎉 MLflow verification SUCCESSFUL!")
        return True

    except Exception as e:
        print(f"\n❌ MLflow verification FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if not verify_mlflow():
        sys.exit(1)
