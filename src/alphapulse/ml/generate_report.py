"""
Model performance report generator for AlphaPulse.

Generates a comprehensive Markdown report with:
- Training metrics from MLflow
- Backtest results
- Feature importance analysis
- Model configuration and metadata
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd


def load_backtest_results(results_path: str) -> Dict[str, Any]:
    """Load backtest results from JSON file."""
    with open(results_path, 'r') as f:
        return json.load(f)


def get_feature_importance(model, feature_names: list) -> pd.DataFrame:
    """Extract feature importance from model."""
    try:
        # XGBoost / sklearn compatible
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            df = pd.DataFrame({
                'feature': feature_names[:len(importance)],
                'importance': importance
            })
            return df.sort_values('importance', ascending=False).head(20)
    except Exception as e:
        print(f"Could not extract feature importance: {e}")
    return pd.DataFrame()


def generate_report(
    model_path: str,
    backtest_results_path: str,
    output_path: str,
    model_id: str = "btc_predictor_v1",
    training_metrics: Optional[Dict[str, float]] = None,
    data_dir: str = "/app/src/data/processed"
) -> str:
    """
    Generate comprehensive model performance report.
    
    Args:
        model_path: Path to trained model
        backtest_results_path: Path to backtest results JSON
        output_path: Output path for Markdown report
        model_id: Model identifier
        training_metrics: Optional training metrics (MAE, RMSE)
        data_dir: Directory containing training data
        
    Returns:
        Path to generated report
    """
    # Load model
    model = joblib.load(model_path)
    
    # Load backtest results
    backtest = load_backtest_results(backtest_results_path)
    
    # Try to load training data for feature names
    feature_names = []
    try:
        train_path = Path(data_dir) / "train.parquet"
        if train_path.exists():
            train_df = pd.read_parquet(train_path)
            drop_cols = ['timestamp', 'symbol', 'source', 'target', 'created_at', 'updated_at']
            feature_names = [c for c in train_df.columns if c not in drop_cols]
    except Exception:
        pass
    
    # Get feature importance
    importance_df = get_feature_importance(model, feature_names)
    
    # Generate report
    report = []
    report.append(f"# Model Performance Report: {model_id}")
    report.append("")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary Section
    report.append("## Executive Summary")
    report.append("")
    
    total_return = float(backtest.get('total_return', 0)) * 100
    sharpe = float(backtest.get('sharpe_ratio', 0))
    max_dd = float(backtest.get('max_drawdown', 0)) * 100
    win_rate = float(backtest.get('win_rate', 0)) * 100
    
    # Performance rating
    if sharpe > 1.0 and max_dd < 20:
        rating = "✅ **Production Ready**"
    elif sharpe > 0 and max_dd < 30:
        rating = "⚠️ **Needs Improvement**"
    else:
        rating = "❌ **Not Ready**"
    
    report.append(f"**Overall Rating**: {rating}")
    report.append("")
    report.append("| Metric | Value | Target | Status |")
    report.append("|--------|-------|--------|--------|")
    report.append(f"| Total Return | {total_return:.2f}% | > 0% | {'✅' if total_return > 0 else '❌'} |")
    report.append(f"| Sharpe Ratio | {sharpe:.4f} | > 1.0 | {'✅' if sharpe > 1.0 else '⚠️' if sharpe > 0 else '❌'} |")
    report.append(f"| Max Drawdown | {max_dd:.2f}% | < 20% | {'✅' if max_dd < 20 else '⚠️' if max_dd < 30 else '❌'} |")
    report.append(f"| Win Rate | {win_rate:.2f}% | > 50% | {'✅' if win_rate > 50 else '⚠️'} |")
    report.append("")
    
    # Training Metrics
    report.append("## Training Metrics")
    report.append("")
    if training_metrics:
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        for metric, value in training_metrics.items():
            report.append(f"| {metric} | {value:.6f} |")
    else:
        report.append("> Training metrics not available. Check MLflow UI for experiment details.")
    report.append("")
    
    # Backtest Results
    report.append("## Backtest Results")
    report.append("")
    report.append("### Portfolio Performance")
    report.append("")
    report.append(f"- **Initial Capital**: ${backtest.get('initial_capital', 'N/A')}")
    report.append(f"- **Final Portfolio**: ${backtest.get('final_portfolio_value', 'N/A')}")
    report.append(f"- **Total Return**: {total_return:.2f}%")
    report.append("")
    
    report.append("### Trading Statistics")
    report.append("")
    report.append(f"- **Total Trades**: {backtest.get('total_trades', 0)}")
    report.append(f"- **Winning Trades**: {backtest.get('winning_trades', 0)}")
    report.append(f"- **Losing Trades**: {backtest.get('losing_trades', 0)}")
    report.append(f"- **Win Rate**: {win_rate:.2f}%")
    report.append("")
    
    report.append("### Risk Metrics")
    report.append("")
    report.append(f"- **Sharpe Ratio**: {sharpe:.4f}")
    report.append(f"- **Max Drawdown**: {max_dd:.2f}%")
    report.append("")
    
    # Feature Importance
    report.append("## Feature Importance")
    report.append("")
    if not importance_df.empty:
        report.append("Top 10 features by importance:")
        report.append("")
        report.append("| Rank | Feature | Importance |")
        report.append("|------|---------|------------|")
        for i, row in importance_df.head(10).iterrows():
            report.append(f"| {i+1} | `{row['feature']}` | {row['importance']:.4f} |")
    else:
        report.append("> Feature importance not available for this model type.")
    report.append("")
    
    # Model Configuration
    report.append("## Model Configuration")
    report.append("")
    report.append(f"- **Model Type**: {type(model).__name__}")
    report.append(f"- **Model Path**: `{model_path}`")
    
    # Try to get hyperparameters
    if hasattr(model, 'get_params'):
        params = model.get_params()
        report.append("")
        report.append("### Hyperparameters")
        report.append("")
        report.append("```json")
        # Only show key params
        key_params = {k: v for k, v in params.items() 
                     if k in ['n_estimators', 'max_depth', 'learning_rate', 'objective', 'eval_metric']}
        report.append(json.dumps(key_params, indent=2))
        report.append("```")
    report.append("")
    
    # Data Information
    report.append("## Data Information")
    report.append("")
    report.append(f"- **Data Directory**: `{data_dir}`")
    report.append(f"- **Number of Features**: {len(feature_names)}")
    report.append(f"- **Daily Returns Tracked**: {backtest.get('num_daily_returns', 'N/A')}")
    report.append("")
    
    # Recommendations
    report.append("## Recommendations")
    report.append("")
    
    recommendations = []
    if sharpe < 1.0:
        recommendations.append("- Consider feature engineering or hyperparameter tuning to improve Sharpe Ratio")
    if max_dd > 20:
        recommendations.append("- Implement stop-loss mechanisms to reduce maximum drawdown")
    if win_rate < 50:
        recommendations.append("- Review signal threshold to improve trade quality")
    if len(recommendations) == 0:
        recommendations.append("- Model meets production criteria. Consider A/B testing in staging environment.")
    
    for rec in recommendations:
        report.append(rec)
    report.append("")
    
    # Footer
    report.append("---")
    report.append("")
    report.append(f"*Report generated by AlphaPulse ML Pipeline*")
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report_content = "\n".join(report)
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    print(f"Report saved to {output_path}")
    return output_path


def main():
    """CLI entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate model performance report")
    parser.add_argument(
        "--model_path",
        type=str,
        default="/app/src/models/saved/btc_predictor_v1.pkl",
        help="Path to trained model"
    )
    parser.add_argument(
        "--backtest_results",
        type=str,
        default="/app/src/results/backtest_results.json",
        help="Path to backtest results JSON"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="/app/src/docs/models/MODEL_REPORT_v1.md",
        help="Output path for Markdown report"
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="btc_predictor_v1",
        help="Model identifier"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="/app/src/data/processed",
        help="Directory containing training data"
    )
    
    args = parser.parse_args()
    
    generate_report(
        model_path=args.model_path,
        backtest_results_path=args.backtest_results,
        output_path=args.output_path,
        model_id=args.model_id,
        data_dir=args.data_dir
    )


if __name__ == "__main__":
    main()
