# MLflow Visualization Guide

This guide explains how to monitor and compare model training results using the MLflow UI.

## 🌐 Accessing the MLflow UI

```bash
# Ensure services are running
docker-compose up -d mlflow

# Open in browser
open http://localhost:5001
```

*Note: The port might be 5001 depending on your `docker-compose.yml` configuration.*

---

## 📊 Key Metric Interpretation

| Metric | Description | Good Range |
|------|------|---------|
| **sharpe_ratio** | Risk-adjusted return | > 1.0 Good, > 2.0 Excellent |
| **total_return** | Total return rate (0.1 = 10%) | Higher is better |
| **win_rate** | Win rate (Directional accuracy) | > 55% |
| **max_drawdown** | Maximum drawdown | < 20% |
| **total_trades** | Total number of trades | > 10 for statistical significance |

### Walk-Forward CV Specific Metrics

| Metric | Description |
|------|------|
| **cv_mean_sharpe** | Mean Sharpe ratio across folds (Robustness) |
| **cv_std_sharpe** | Standard deviation of Sharpe (Lower is more stable) |
| **stability_score** | mean_sharpe / std_sharpe (Higher is better) |

---

## 🔍 Using the MLflow UI

### 1. View Experiments

Locate in the left panel:
- **`auto_training`** - Best model records
- **`auto_training_runs`** - Comparison of all training runs
- **`btc_price_optimization`** - Optuna optimization results

### 2. Compare Runs

1. Select the runs you want to compare.
2. Click **Compare**.
3. Use the **Parallel Coordinates Plot** to identify the best parameter combinations.

### 3. Filter Best Models

Use the Search Filter:
```
metrics.sharpe_ratio > 1.0 AND metrics.total_trades > 5
```

### 4. Analyze Parameter Impact

In the comparison view:
- **Scatter Plot**: Set X-axis to `param_threshold`, Y-axis to `metrics.sharpe_ratio`.
- Observe how the threshold affects the Sharpe ratio.

---

## 🚀 Execution and Results

### Fast Training (Single Backtest)
```bash
docker exec -it mage python -m alphapulse.ml.auto_train \
  --data_dir /home/src/src/data/processed \
  --output_dir /home/src/src/models/saved
```

### Robust Training (Walk-Forward CV)
```bash
docker exec -it mage python -m alphapulse.ml.auto_train \
  --data_dir /home/src/src/data/processed \
  --output_dir /home/src/src/models/saved \
  --walk-forward --wf-splits 5
```

### Optuna Optimization (Auto Tuning)
```bash
docker exec -it mage python -m alphapulse.ml.optimize \
  --data_dir /home/src/src/data/processed \
  --n_trials 100 \
  --walk-forward
```

---

## 📈 Best Practices

1. **Prioritize Walk-Forward CV results** - More reflective of real-world performance.
2. **Beware of Overfitting** - A high `cv_std_sharpe` indicates the model might be overfitted.
3. **Focus on stability_score** - Consistently high Sharpe is more reliable than occasional spikes.
4. **Monitor trade counts** - Too few trades might indicate luck rather than edge.