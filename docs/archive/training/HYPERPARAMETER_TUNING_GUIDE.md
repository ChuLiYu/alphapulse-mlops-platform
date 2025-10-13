# 🛠️ Hyperparameter Optimization (HPO) Core Guide

In Machine Learning, a model is like a complex machine. **Parameters** are internal parts adjusted automatically during operation, while **Hyperparameters** are external knobs you tune manually before it starts.

---

## 1. 5W1H Analysis of Hyperparameters

### What?
*   **Definition**: Parameters set before training that the model cannot learn automatically.
*   **Examples (CatBoost)**:
    *   `depth`: How deep the tree grows.
    *   `learning_rate`: Step size for each update.
    *   `l2_leaf_reg`: Penalty for complex weights.

### Why?
*   **Performance**: Default parameters are rarely optimal.
*   **Generalization**: Proper regularization prevents overfitting.
*   **Efficiency**: Optimized models often reach better results with fewer iterations.

### Who & Where?
*   **Executor**: Automatically handled by the **Optuna** framework in AlphaPulse.
*   **Location**: Executes within the `trainer` container; results logged to **MLflow**.

### When?
*   **Periodic**: Triggered when major data distribution changes occur.
*   **On Drift**: When **Data Drift** is detected by monitoring tools.

### How?
*   **Historical**: Manual Search or Grid Search.
*   **Modern**: **Bayesian Optimization** (using past trials to predict better future parameters).

---

## 2. Evolution of HPO Strategies

### Gen 1: Manual Search
*   Trial and error based on intuition. Highly inefficient.

### Gen 2: Grid Search
*   Brute-force testing of all combinations. Suffers from the **Curse of Dimensionality**.

### Gen 3: Random Search
*   Sampling random points in the space. Mathematically proven to be more effective than Grid Search.

### Gen 4: Bayesian Optimization (Optuna's Core)
*   **Search with Memory**. It builds a probabilistic model of the results and focuses resources on promising regions. 
*   **AlphaPulse Implementation**: We use Optuna's **TPE (Tree-structured Parzen Estimator)**, the industry standard for efficient HPO.

---

## 3. Real-world Scenario in AlphaPulse

### Scenario: Tuning CatBoost for BTC Returns
We instruct Optuna to:
1.  Try `depth` between 3 and 10.
2.  Try `learning_rate` between 0.01 and 0.3.
3.  **Objective**: Minimize Validation **MAE** while ensuring **R² Gap < 0.30**.

**Optuna Workflow**:
*   **Trial**: A single training run.
*   **Study**: A collection of trials.
*   **Pruning**: Automatically stopping "bad" trials early to save CPU/RAM.

---

## 4. Interview Gold Nuggets

> "In AlphaPulse, I integrated **Optuna** for Bayesian-based HPO instead of using inefficient Grid Search. 
> 
> This approach reduced tuning time by over 70% while incorporating **automated Pruning** to intelligently discard low-potential trials. 
> 
> This robust tuning process helped us identify the optimal regularization for CatBoost, reducing generalization error by approximately 15% on unseen data."
