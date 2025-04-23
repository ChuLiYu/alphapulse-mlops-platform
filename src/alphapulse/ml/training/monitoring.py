"""
Training Monitoring and Alert System.

This module provides comprehensive monitoring for model training:
1. Real-time metric tracking
2. Performance degradation detection
3. Data drift monitoring
4. Model health checks
5. Automated alerting
"""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

import mlflow


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Training alert."""

    timestamp: str
    severity: AlertSeverity
    category: str
    message: str
    details: Dict[str, Any]

    def __str__(self):
        emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }
        return f"{emoji[self.severity]} [{self.category}] {self.message}"


@dataclass
class TrainingMetrics:
    """Training metrics snapshot."""

    timestamp: str
    iteration: int

    # Performance metrics
    train_mae: float
    val_mae: float
    test_mae: float
    train_r2: float
    val_r2: float
    test_r2: float

    # Overfitting indicators
    train_val_gap: float
    val_test_gap: float
    cv_std: float

    # Resource metrics
    training_time: float
    memory_usage_mb: Optional[float] = None

    # Data metrics
    n_train_samples: int = 0
    n_val_samples: int = 0
    n_features: int = 0


class TrainingMonitor:
    """
    Monitors training process and generates alerts.
    """

    def __init__(
        self,
        output_dir: str = "/app/src/models/saved",
        alert_file: str = "training_alerts.jsonl",
        metrics_file: str = "training_metrics.jsonl",
    ):
        """
        Initialize training monitor.

        Args:
            output_dir: Directory for output files
            alert_file: Filename for alerts log
            metrics_file: Filename for metrics log
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.alert_file = self.output_dir / alert_file
        self.metrics_file = self.output_dir / metrics_file

        self.alerts: List[Alert] = []
        self.metrics_history: List[TrainingMetrics] = []

        # Alert thresholds
        self.thresholds = {
            "max_train_val_gap": 0.15,
            "max_val_test_gap": 0.10,
            "max_cv_std": 0.05,
            "min_val_r2": 0.1,
            "max_training_time": 3600,  # 1 hour
            "max_memory_mb": 8192,  # 8 GB
            "performance_degradation_threshold": 0.10,  # 10% worse
        }

    def log_metrics(self, metrics: TrainingMetrics):
        """
        Log training metrics.

        Args:
            metrics: TrainingMetrics to log
        """
        self.metrics_history.append(metrics)

        # Append to file
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(asdict(metrics), default=str) + "\n")

        print(f"📊 Logged metrics for iteration {metrics.iteration}")

    def add_alert(self, alert: Alert):
        """
        Add an alert.

        Args:
            alert: Alert to add
        """
        self.alerts.append(alert)

        # Append to file
        with open(self.alert_file, "a") as f:
            alert_dict = asdict(alert)
            alert_dict["severity"] = alert.severity.value
            f.write(json.dumps(alert_dict, default=str) + "\n")

        # Print alert
        print(f"\n{alert}")

    def check_overfitting(self, metrics: TrainingMetrics):
        """
        Check for overfitting indicators.

        Args:
            metrics: Current training metrics
        """
        # Check train-val gap
        if metrics.train_val_gap > self.thresholds["max_train_val_gap"]:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Overfitting",
                    message=f"High train-val gap detected: {metrics.train_val_gap:.2%}",
                    details={
                        "iteration": metrics.iteration,
                        "train_val_gap": metrics.train_val_gap,
                        "threshold": self.thresholds["max_train_val_gap"],
                    },
                )
            )

        # Check val-test gap
        if metrics.val_test_gap > self.thresholds["max_val_test_gap"]:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Overfitting",
                    message=f"High val-test gap detected: {metrics.val_test_gap:.2%}",
                    details={
                        "iteration": metrics.iteration,
                        "val_test_gap": metrics.val_test_gap,
                        "threshold": self.thresholds["max_val_test_gap"],
                    },
                )
            )

        # Check CV std
        if metrics.cv_std > self.thresholds["max_cv_std"]:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Instability",
                    message=f"High cross-validation variance: {metrics.cv_std:.6f}",
                    details={
                        "iteration": metrics.iteration,
                        "cv_std": metrics.cv_std,
                        "threshold": self.thresholds["max_cv_std"],
                    },
                )
            )

    def check_performance_degradation(self, metrics: TrainingMetrics):
        """
        Check for performance degradation compared to previous iterations.

        Args:
            metrics: Current training metrics
        """
        if len(self.metrics_history) < 2:
            return

        # Compare with best previous performance
        previous_metrics = [m for m in self.metrics_history[:-1] if not m.val_mae > 1e6]
        if not previous_metrics:
            return

        best_prev_val_mae = min(m.val_mae for m in previous_metrics)

        # Calculate degradation
        degradation = (metrics.val_mae - best_prev_val_mae) / best_prev_val_mae

        if degradation > self.thresholds["performance_degradation_threshold"]:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.INFO,
                    category="Performance",
                    message=f"Performance worse than best: {degradation:.1%}",
                    details={
                        "iteration": metrics.iteration,
                        "current_val_mae": metrics.val_mae,
                        "best_val_mae": best_prev_val_mae,
                        "degradation": degradation,
                    },
                )
            )

    def check_resource_usage(self, metrics: TrainingMetrics):
        """
        Check resource usage.

        Args:
            metrics: Current training metrics
        """
        # Check training time
        if metrics.training_time > self.thresholds["max_training_time"]:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Resources",
                    message=f"Training time exceeded: {metrics.training_time:.0f}s",
                    details={
                        "iteration": metrics.iteration,
                        "training_time": metrics.training_time,
                        "threshold": self.thresholds["max_training_time"],
                    },
                )
            )

        # Check memory usage
        if (
            metrics.memory_usage_mb
            and metrics.memory_usage_mb > self.thresholds["max_memory_mb"]
        ):
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Resources",
                    message=f"High memory usage: {metrics.memory_usage_mb:.0f} MB",
                    details={
                        "iteration": metrics.iteration,
                        "memory_mb": metrics.memory_usage_mb,
                        "threshold": self.thresholds["max_memory_mb"],
                    },
                )
            )

    def check_data_quality(self, metrics: TrainingMetrics):
        """
        Check data quality indicators.

        Args:
            metrics: Current training metrics
        """
        # Check for insufficient data
        if metrics.n_train_samples < 500:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Data Quality",
                    message=f"Low training sample count: {metrics.n_train_samples}",
                    details={
                        "iteration": metrics.iteration,
                        "n_train_samples": metrics.n_train_samples,
                    },
                )
            )

        # Check validation performance
        if metrics.val_r2 < self.thresholds["min_val_r2"]:
            self.add_alert(
                Alert(
                    timestamp=datetime.now().isoformat(),
                    severity=AlertSeverity.WARNING,
                    category="Performance",
                    message=f"Low validation R²: {metrics.val_r2:.4f}",
                    details={
                        "iteration": metrics.iteration,
                        "val_r2": metrics.val_r2,
                        "threshold": self.thresholds["min_val_r2"],
                    },
                )
            )

    def monitor_iteration(self, metrics: TrainingMetrics):
        """
        Monitor a single training iteration.

        Args:
            metrics: Metrics from the iteration
        """
        print(f"\n🔍 Monitoring iteration {metrics.iteration}...")

        # Log metrics
        self.log_metrics(metrics)

        # Run all checks
        self.check_overfitting(metrics)
        self.check_performance_degradation(metrics)
        self.check_resource_usage(metrics)
        self.check_data_quality(metrics)

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary report of training session.

        Returns:
            Dictionary with summary statistics
        """
        if not self.metrics_history:
            return {"error": "No metrics collected"}

        # Alert summary
        alert_counts = {}
        for alert in self.alerts:
            severity = alert.severity.value
            alert_counts[severity] = alert_counts.get(severity, 0) + 1

        # Performance summary
        val_maes = [m.val_mae for m in self.metrics_history]
        best_iteration = self.metrics_history[np.argmin(val_maes)]

        summary = {
            "training_session": {
                "start_time": self.metrics_history[0].timestamp,
                "end_time": self.metrics_history[-1].timestamp,
                "total_iterations": len(self.metrics_history),
                "total_training_time": sum(
                    m.training_time for m in self.metrics_history
                ),
            },
            "alerts": {
                "total": len(self.alerts),
                "by_severity": alert_counts,
                "by_category": {},
            },
            "performance": {
                "best_iteration": best_iteration.iteration,
                "best_val_mae": best_iteration.val_mae,
                "best_test_mae": best_iteration.test_mae,
                "best_val_r2": best_iteration.val_r2,
                "best_test_r2": best_iteration.test_r2,
            },
            "overfitting_stats": {
                "mean_train_val_gap": np.mean(
                    [m.train_val_gap for m in self.metrics_history]
                ),
                "mean_val_test_gap": np.mean(
                    [m.val_test_gap for m in self.metrics_history]
                ),
                "mean_cv_std": np.mean([m.cv_std for m in self.metrics_history]),
            },
        }

        # Alert categories
        for alert in self.alerts:
            cat = alert.category
            summary["alerts"]["by_category"][cat] = (
                summary["alerts"]["by_category"].get(cat, 0) + 1
            )

        return summary

    def print_summary_report(self):
        """Print formatted summary report."""
        summary = self.generate_summary_report()

        print("\n" + "=" * 80)
        print("📋 TRAINING MONITORING SUMMARY")
        print("=" * 80)

        # Session info
        session = summary["training_session"]
        print(f"\n⏱️  Training Session:")
        print(f"  Duration: {session['start_time']} to {session['end_time']}")
        print(f"  Iterations: {session['total_iterations']}")
        print(f"  Total Time: {session['total_training_time']:.1f}s")

        # Alerts
        alerts = summary["alerts"]
        print(f"\n🚨 Alerts: {alerts['total']} total")
        if alerts["by_severity"]:
            for severity, count in alerts["by_severity"].items():
                print(f"  {severity.upper()}: {count}")
        if alerts["by_category"]:
            print(f"  By Category:")
            for category, count in alerts["by_category"].items():
                print(f"    {category}: {count}")

        # Performance
        perf = summary["performance"]
        print(f"\n🏆 Best Performance:")
        print(f"  Iteration: {perf['best_iteration']}")
        print(f"  Validation MAE: {perf['best_val_mae']:.6f}")
        print(f"  Test MAE: {perf['best_test_mae']:.6f}")
        print(f"  Test R²: {perf['best_test_r2']:.4f}")

        # Overfitting
        overfit = summary["overfitting_stats"]
        print(f"\n📊 Overfitting Statistics:")
        print(f"  Mean Train-Val Gap: {overfit['mean_train_val_gap']:.2%}")
        print(f"  Mean Val-Test Gap: {overfit['mean_val_test_gap']:.2%}")
        print(f"  Mean CV Std: {overfit['mean_cv_std']:.6f}")

        print("\n" + "=" * 80)

        # Save summary
        summary_path = self.output_dir / "monitoring_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n💾 Summary saved: {summary_path}")

    def get_critical_alerts(self) -> List[Alert]:
        """
        Get critical alerts that need immediate attention.

        Returns:
            List of critical alerts
        """
        return [
            alert
            for alert in self.alerts
            if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        ]

    def export_to_mlflow(self, experiment_name: str):
        """
        Export monitoring data to MLflow.

        Args:
            experiment_name: MLflow experiment name
        """
        try:
            mlflow.set_experiment(experiment_name)

            with mlflow.start_run(run_name="training_monitoring"):
                # Log summary metrics
                summary = self.generate_summary_report()

                mlflow.log_metrics(
                    {
                        "total_iterations": summary["training_session"][
                            "total_iterations"
                        ],
                        "total_alerts": summary["alerts"]["total"],
                        "best_val_mae": summary["performance"]["best_val_mae"],
                        "best_test_mae": summary["performance"]["best_test_mae"],
                        "mean_train_val_gap": summary["overfitting_stats"][
                            "mean_train_val_gap"
                        ],
                        "mean_val_test_gap": summary["overfitting_stats"][
                            "mean_val_test_gap"
                        ],
                    }
                )

                # Log alert files
                if self.alert_file.exists():
                    mlflow.log_artifact(str(self.alert_file))
                if self.metrics_file.exists():
                    mlflow.log_artifact(str(self.metrics_file))

                print(
                    f"✅ Exported monitoring data to MLflow experiment '{experiment_name}'"
                )

        except Exception as e:
            print(f"⚠️  Could not export to MLflow: {str(e)}")


def get_memory_usage_mb() -> float:
    """
    Get current process memory usage in MB.

    Returns:
        Memory usage in MB
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0
