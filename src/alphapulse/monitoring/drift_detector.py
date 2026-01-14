import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
import mlflow
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DriftDetector:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse")
        self.engine = create_engine(self.db_url)
        self.mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(self.mlflow_uri)

    def run_drift_analysis(self):
        """Compare recent data with historical baseline to detect drift"""
        logger.info("⏳ Loading data for drift analysis...")
        
        # Load all features
        df = pd.read_sql("SELECT * FROM model_features ORDER BY date", self.engine)
        
        if df.empty or len(df) < 1000:
            logger.warning("Insufficient data for drift analysis.")
            return

        # Prepare features (Numeric only)
        X = df.select_dtypes(include=[np.number]).copy()
        # Drop internal columns
        bad = ["id", "loaded_at", "processed_at", "price_change_1d", "price_change_3d", "price_change_7d"]
        X = X.drop(columns=[c for c in bad if c in X.columns])

        # Define Baseline (e.g., older data) and Current (last 7 days)
        # We'll use 80% as reference and the most recent 20% as current
        split_idx = int(len(X) * 0.8)
        reference_data = X.iloc[:split_idx]
        current_data = X.iloc[split_idx:]

        logger.info(f"📊 Analyzing drift: Reference({len(reference_data)}) vs Current({len(current_data)})")

        # Create Evidently Report
        drift_report = Report(metrics=[
            DataDriftPreset(),
            TargetDriftPreset(),
        ])

        drift_report.run(reference_data=reference_data, current_data=current_data)
        
        # Save Report
        report_path = "/app/storage/reports/drift_report.html"
        os.makedirs("/app/storage/reports", exist_ok=True)
        drift_report.save_html(report_path)
        logger.info(f"✅ Drift report generated at {report_path}")

        # Log to MLflow
        with mlflow.start_run(run_name=f"drift_analysis_{datetime.now().strftime('%Y%m%d')}"):
            mlflow.log_artifact(report_path)
            # Log summary metrics
            result = drift_report.as_dict()
            drift_share = result["metrics"][0]["result"]["drift_share"]
            mlflow.log_metric("drift_share", drift_share)
            logger.info(f"📈 Drift Share: {drift_share:.2%}")

        return report_path

if __name__ == "__main__":
    detector = DriftDetector()
    detector.run_drift_analysis()
