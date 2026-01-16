# AlphaPulse Frontend Specification

**Version**: 2.1
**Date**: 2026-01-15
**Status**: Implementation Verified (Core MLOps & Trading)

## 1. Overview

The AlphaPulse frontend is a React-based Single Page Application (SPA) serving as a high-fidelity **MLOps Fintech Portfolio**. It provides a professional "Command Center" that integrates real-time quantitative trading with automated machine learning lifecycle management.

The key design pillars are:
1.  **Interactivity**: "Strategy Playground" for real-time risk/reward simulation.
2.  **Observability (MLOps)**: "Pipeline Health HUD" and "Drift Monitoring" for system transparency.
3.  **Explainability (XAI)**: "Signal X-Ray" to demystify ML decisions (Visual placeholder implemented).
4.  **Security (SecOps)**: Role-based access control and threat monitoring (Planned).
5.  **Aesthetics**: "Cyber-Fintech" design system (Dark Mode, Neon Blue/Green accents, Glassmorphism).

**Tech Stack**:
- **Framework**: React 18 (Vite)
- **UI Library**: Material UI (MUI) v7
- **Animations**: Framer Motion
- **Charts**: Recharts
- **State Management**: Redux Toolkit + React Query

---

## 2. Page Structure & Features

### 2.1. Dashboard (Command Center) - [Implemented]
The primary entry point combining trading performance with MLOps health.
- **MLOps Metrics (Top Row)**: 
  - **Inference Latency**: P99 response time (e.g., 112ms).
  - **Data Drift (PSI)**: Current population stability index.
  - **Training Efficiency**: GPU cluster utilization.
  - **Model Version**: Active production version tag.
- **Hero Section: Strategy Playground**: 
  - Interactive sliders for Risk, Confidence, and Stop-Loss.
  - Real-time generated Equity Curve vs BTC Benchmark.
- **MLOps Pipeline Pulse**:
  - Condensed view of the live DAG execution flow.
- **Market Performance & Signal Stream**:
  - Technical price trends and a real-time feed of ML-generated signals.

### 2.2. MLOps Console - [Implemented]
A dedicated deep-dive into the machine learning lifecycle.
- **Pipeline Flow (Automation)**: Full-width animated DAG showing `Ingestion -> Validation -> Training -> Evaluation -> Deployment`.
- **Drift Monitor (Monitoring)**: Detailed PSI analysis by feature with automated threshold alerts (e.g., Sentiment Score drift).
- **Model Registry (Deployment)**: Versioned table of models showing stage (Prod/Staging), accuracy, and deployment age.

### 2.3. Market Data & Signals - [Placeholder]
- Advanced candlestick charting and deep historical signal logs.

---

## 3. Visual Identity

- **Theme**: Cyber-Fintech Dark Mode.
  - **Primary**: Cyber Blue (`#00d2ff`).
  - **Secondary/Success**: Neon Green (`#00ff9f`).
  - **Background**: Deep Navy/Black (`#050a14`).
- **Components**: Glassmorphism cards with `backdrop-filter: blur(10px)` and subtle glowing borders.
- **Motion**: 
  - Layout transitions via `framer-motion`.
  - Pulsing animations for active pipeline nodes.
  - Counter animations for financial metrics.

---

## 4. Implementation Progress

| Feature | Status | Priority |
| :--- | :--- | :--- |
| Cyber-Fintech Design System | ✅ Completed | High |
| Strategy Playground (Hero) | ✅ Completed | High |
| MLOps Pipeline Flow | ✅ Completed | High |
| Data Drift Monitoring | ✅ Completed | Medium |
| Model Registry | ✅ Completed | Medium |
| Dashboard Integration | ✅ Completed | High |
| Signal X-Ray (XAI) | ⏳ Planned | Medium |
| SecOps War Room | ⏳ Planned | Low |
