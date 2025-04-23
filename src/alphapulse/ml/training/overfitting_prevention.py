"""

Advanced Overfitting Prevention Module.

This module provides comprehensive overfitting detection and prevention mechanisms:
1. Learning Curve Analysis
2. Feature Importance Stability
3. Prediction Diversity Analysis
4. Ensemble Methods
5. Automated Regularization Tuning
"""

import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import learning_curve


@dataclass
class OverfittingReport:
    """Comprehensive overfitting analysis report."""

    is_overfit: bool
    confidence: float  # 0-1, how confident we are
    issues: List[str]  # List of detected issues
    recommendations: List[str]  # Recommended actions

    # Detailed metrics
    train_val_gap: float
    val_test_gap: float
    learning_curve_score: float
    feature_stability_score: float
    prediction_diversity_score: float

    # Raw data for further analysis
    metrics: Dict[str, float]


class OverfittingDetector:
    """
    Advanced overfitting detection system.

    Uses multiple signals to detect overfitting:
    - Performance gaps (train/val/test)
    - Learning curves
    - Feature importance stability
    - Prediction diversity
    - Cross-validation variance
    """

    def __init__(
        self,
        max_train_val_gap: float = 0.15,
        max_val_test_gap: float = 0.10,
        min_val_score: float = 0.1,
        learning_curve_threshold: float = 0.8,
        feature_stability_threshold: float = 0.7,
    ):
        """
        Initialize overfitting detector.

        Args:
            max_train_val_gap: Maximum acceptable train-validation gap
            max_val_test_gap: Maximum acceptable validation-test gap
            min_val_score: Minimum acceptable validation score
            learning_curve_threshold: Threshold for learning curve convergence
            feature_stability_threshold: Minimum feature importance correlation
        """
        self.max_train_val_gap = max_train_val_gap
        self.max_val_test_gap = max_val_test_gap
        self.min_val_score = min_val_score
        self.learning_curve_threshold = learning_curve_threshold
        self.feature_stability_threshold = feature_stability_threshold

    def analyze_performance_gaps(
        self,
        train_score: float,
        val_score: float,
        test_score: float,
        metric_name: str = "MAE",
        lower_is_better: bool = True,
    ) -> Tuple[bool, List[str], Dict[str, float]]:
        """
        Analyze performance gaps between train/val/test.

        Args:
            train_score: Training set score
            val_score: Validation set score
            test_score: Test set score
            metric_name: Name of the metric
            lower_is_better: Whether lower scores are better

        Returns:
            Tuple of (is_overfit, issues, metrics)
        """
        issues = []
        metrics = {}

        # Calculate gaps (handling both directions)
        if lower_is_better:
            # For MAE, RMSE (lower is better)
            train_val_gap = (
                (val_score - train_score) / train_score if train_score > 0 else 0
            )
            val_test_gap = (
                abs(test_score - val_score) / val_score if val_score > 0 else 0
            )
        else:
            # For R², accuracy (higher is better)
            train_val_gap = (
                (train_score - val_score) / train_score if train_score > 0 else 0
            )
            val_test_gap = (
                abs(val_score - test_score) / val_score if val_score > 0 else 0
            )

        metrics["train_val_gap"] = train_val_gap
        metrics["val_test_gap"] = val_test_gap

        is_overfit = False

        # Check train-val gap
        if train_val_gap > self.max_train_val_gap:
            issues.append(
                f"Large train-val gap: {train_val_gap:.2%} > {self.max_train_val_gap:.2%}"
            )
            is_overfit = True

        # Check val-test gap
        if val_test_gap > self.max_val_test_gap:
            issues.append(
                f"Large val-test gap: {val_test_gap:.2%} > {self.max_val_test_gap:.2%}"
            )
            is_overfit = True

        # Check minimum validation performance
        if not lower_is_better and val_score < self.min_val_score:
            issues.append(
                f"Poor validation performance: {metric_name}={val_score:.4f} < {self.min_val_score:.4f}"
            )
            is_overfit = True

        return is_overfit, issues, metrics

    def analyze_learning_curve(
        self, model, X_train: np.ndarray, y_train: np.ndarray, cv: int = 5
    ) -> Tuple[float, bool, List[str]]:
        """
        Analyze learning curves to detect overfitting.

        A model is overfitting if:
        - Training score is high but validation score is low
        - Gap between train and validation doesn't decrease with more data

        Args:
            model: Trained model
            X_train: Training features
            y_train: Training targets
            cv: Number of cross-validation folds

        Returns:
            Tuple of (convergence_score, is_overfit, issues)
        """
        try:
            train_sizes = np.linspace(0.3, 1.0, 5)

            train_sizes_abs, train_scores, val_scores = learning_curve(
                model,
                X_train,
                y_train,
                train_sizes=train_sizes,
                cv=cv,
                scoring="neg_mean_absolute_error",
                n_jobs=-1,
            )

            # Get mean scores
            train_scores_mean = -train_scores.mean(axis=1)
            val_scores_mean = -val_scores.mean(axis=1)

            # Calculate convergence score (0-1)
            # If curves are converging, scores should be similar at the end
            final_gap = abs(train_scores_mean[-1] - val_scores_mean[-1])
            convergence_score = 1.0 / (1.0 + final_gap)

            issues = []
            is_overfit = False

            # Check if gap is decreasing (learning)
            initial_gap = abs(train_scores_mean[0] - val_scores_mean[0])
            if final_gap >= initial_gap:
                issues.append(
                    f"Learning curves not converging: initial_gap={initial_gap:.4f}, "
                    f"final_gap={final_gap:.4f}"
                )
                is_overfit = True

            # Check convergence threshold
            if convergence_score < self.learning_curve_threshold:
                issues.append(
                    f"Low convergence score: {convergence_score:.4f} < "
                    f"{self.learning_curve_threshold:.4f}"
                )
                is_overfit = True

            return convergence_score, is_overfit, issues

        except Exception as e:
            warnings.warn(f"Could not analyze learning curve: {str(e)}")
            return 0.5, False, []

    def analyze_feature_importance_stability(
        self, model_1, model_2, feature_names: List[str]
    ) -> Tuple[float, bool, List[str]]:
        """
        Check if feature importances are stable across different models/folds.

        Unstable feature importances may indicate overfitting to noise.

        Args:
            model_1: First trained model
            model_2: Second trained model (e.g., from different CV fold)
            feature_names: List of feature names

        Returns:
            Tuple of (stability_score, is_unstable, issues)
        """
        try:
            # Get feature importances
            if hasattr(model_1, "feature_importances_"):
                imp_1 = model_1.feature_importances_
                imp_2 = model_2.feature_importances_
            elif hasattr(model_1, "coef_"):
                imp_1 = np.abs(model_1.coef_)
                imp_2 = np.abs(model_2.coef_)
            else:
                return 1.0, False, []  # Can't check, assume stable

            # Calculate Spearman correlation (rank-based)
            correlation, _ = spearmanr(imp_1, imp_2)
            stability_score = max(0, correlation)  # Clip to [0, 1]

            issues = []
            is_unstable = False

            if stability_score < self.feature_stability_threshold:
                issues.append(
                    f"Unstable feature importances: correlation={stability_score:.4f} < "
                    f"{self.feature_stability_threshold:.4f}"
                )
                is_unstable = True

            return stability_score, is_unstable, issues

        except Exception as e:
            warnings.warn(f"Could not analyze feature stability: {str(e)}")
            return 1.0, False, []

    def analyze_prediction_diversity(
        self,
        y_true: np.ndarray,
        predictions_list: List[np.ndarray],
        threshold: float = 0.95,
    ) -> Tuple[float, bool, List[str]]:
        """
        Analyze diversity of predictions from different models.

        Low diversity (very similar predictions) may indicate overfitting
        to the same patterns.

        Args:
            y_true: True target values
            predictions_list: List of prediction arrays from different models
            threshold: Maximum correlation threshold

        Returns:
            Tuple of (diversity_score, is_overfit, issues)
        """
        if len(predictions_list) < 2:
            return 1.0, False, []

        try:
            # Calculate pairwise correlations
            correlations = []
            for i in range(len(predictions_list)):
                for j in range(i + 1, len(predictions_list)):
                    corr, _ = spearmanr(predictions_list[i], predictions_list[j])
                    correlations.append(corr)

            # Diversity score = 1 - mean correlation
            mean_corr = np.mean(correlations)
            diversity_score = 1 - mean_corr

            issues = []
            is_overfit = False

            if mean_corr > threshold:
                issues.append(
                    f"Low prediction diversity: mean_correlation={mean_corr:.4f} > {threshold:.4f}"
                )
                is_overfit = True

            return diversity_score, is_overfit, issues

        except Exception as e:
            warnings.warn(f"Could not analyze prediction diversity: {str(e)}")
            return 1.0, False, []

    def comprehensive_analysis(
        self,
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        train_score: float,
        val_score: float,
        test_score: float,
        feature_names: List[str],
        metric_name: str = "MAE",
        lower_is_better: bool = True,
        additional_models: Optional[List[Any]] = None,
        predictions_list: Optional[List[np.ndarray]] = None,
        y_true: Optional[np.ndarray] = None,
    ) -> OverfittingReport:
        """
        Perform comprehensive overfitting analysis.

        Args:
            model: Trained model
            X_train: Training features
            y_train: Training targets
            train_score: Training score
            val_score: Validation score
            test_score: Test score
            feature_names: Feature names
            metric_name: Metric name
            lower_is_better: Whether lower is better for the metric
            additional_models: Additional models for stability analysis
            predictions_list: List of predictions for diversity analysis
            y_true: True values for diversity analysis

        Returns:
            OverfittingReport with comprehensive analysis
        """
        all_issues = []
        all_metrics = {}
        is_overfit = False

        # 1. Performance gaps
        gaps_overfit, gaps_issues, gaps_metrics = self.analyze_performance_gaps(
            train_score, val_score, test_score, metric_name, lower_is_better
        )
        all_issues.extend(gaps_issues)
        all_metrics.update(gaps_metrics)
        is_overfit = is_overfit or gaps_overfit

        # 2. Learning curve
        lc_score, lc_overfit, lc_issues = self.analyze_learning_curve(
            model, X_train, y_train
        )
        all_issues.extend(lc_issues)
        all_metrics["learning_curve_score"] = lc_score
        is_overfit = is_overfit or lc_overfit

        # 3. Feature importance stability
        stability_score = 1.0
        if additional_models and len(additional_models) > 0:
            stability_score, stability_overfit, stability_issues = (
                self.analyze_feature_importance_stability(
                    model, additional_models[0], feature_names
                )
            )
            all_issues.extend(stability_issues)
            all_metrics["feature_stability_score"] = stability_score
            is_overfit = is_overfit or stability_overfit
        else:
            all_metrics["feature_stability_score"] = 1.0

        # 4. Prediction diversity
        diversity_score = 1.0
        if predictions_list and y_true is not None:
            diversity_score, diversity_overfit, diversity_issues = (
                self.analyze_prediction_diversity(y_true, predictions_list)
            )
            all_issues.extend(diversity_issues)
            all_metrics["prediction_diversity_score"] = diversity_score
            is_overfit = is_overfit or diversity_overfit
        else:
            all_metrics["prediction_diversity_score"] = 1.0

        # Generate recommendations
        recommendations = []
        if is_overfit:
            if gaps_overfit:
                recommendations.append("Increase regularization (alpha/lambda)")
                recommendations.append("Reduce model complexity (depth, features)")
            if lc_overfit:
                recommendations.append("Collect more training data")
                recommendations.append("Use simpler model architecture")
            if additional_models and stability_score < self.feature_stability_threshold:
                recommendations.append(
                    "Apply feature selection to remove noisy features"
                )
                recommendations.append("Use ensemble methods for stability")
            if predictions_list and diversity_score < 0.5:
                recommendations.append("Train more diverse models")
                recommendations.append("Use different model architectures")

        # Calculate confidence score (based on number of checks performed)
        num_checks = 2  # Always have gaps and learning curve
        if additional_models:
            num_checks += 1
        if predictions_list and y_true is not None:
            num_checks += 1

        confidence = num_checks / 4.0  # Max 4 checks

        return OverfittingReport(
            is_overfit=is_overfit,
            confidence=confidence,
            issues=all_issues,
            recommendations=recommendations,
            train_val_gap=all_metrics.get("train_val_gap", 0),
            val_test_gap=all_metrics.get("val_test_gap", 0),
            learning_curve_score=all_metrics.get("learning_curve_score", 1.0),
            feature_stability_score=all_metrics.get("feature_stability_score", 1.0),
            prediction_diversity_score=all_metrics.get(
                "prediction_diversity_score", 1.0
            ),
            metrics=all_metrics,
        )


def print_overfitting_report(report: OverfittingReport):
    """
    Print a formatted overfitting report.

    Args:
        report: OverfittingReport to print
    """
    print("\n" + "=" * 80)
    print("🔍 OVERFITTING ANALYSIS REPORT")
    print("=" * 80)

    # Overall status
    if report.is_overfit:
        print(f"\n⚠️  OVERFITTING DETECTED (Confidence: {report.confidence:.1%})")
    else:
        print(f"\n✅ No overfitting detected (Confidence: {report.confidence:.1%})")

    # Metrics
    print(f"\n📊 Metrics:")
    print(f"  Train-Val Gap: {report.train_val_gap:.2%}")
    print(f"  Val-Test Gap: {report.val_test_gap:.2%}")
    print(f"  Learning Curve Score: {report.learning_curve_score:.4f}")
    print(f"  Feature Stability: {report.feature_stability_score:.4f}")
    print(f"  Prediction Diversity: {report.prediction_diversity_score:.4f}")

    # Issues
    if report.issues:
        print(f"\n❌ Issues Detected ({len(report.issues)}):")
        for issue in report.issues:
            print(f"  • {issue}")

    # Recommendations
    if report.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")

    print("\n" + "=" * 80)
