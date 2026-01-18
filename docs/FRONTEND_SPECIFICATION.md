# AlphaPulse Frontend Specification

**Version**: 2.6
**Date**: 2026-01-17
**Status**: Implementation Refined (Docker Orchestration Enabled)

## 1. Overview

The AlphaPulse frontend is a high-precision **MLOps Terminal** serving as a professional "Command Center" for quantitative trading and machine learning lifecycle management. It bridges the gap between financial trading density and developer-centric aesthetics (Cyber-Terminal style).

The design pillars are:
1.  **Interactivity**: Real-time price tracking and dynamic system feedback.
2.  **Observability**: Transparent MLOps metrics (Latency, Drift, Memory) and pipeline status.
3.  **Aesthetics**: "Cyber-Fintech" design system using deep blacks, emerald accents, and glassmorphism.
4.  **Precision**: Financial-grade UI reflecting underlying `Decimal` precision logic.

---

## 2. Technical Stack

- **Core Framework**: React 18 (Vite)
- **Language**: TypeScript (Strict Mode)
- **UI Library**: Material UI (MUI) v6/v7 (using modern `Grid` patterns)
- **Styling**: Tailwind CSS + Emotion (CSS-in-JS)
- **Animations**: Framer Motion (v12+)
- **Charts**: Recharts & Custom Animated SVGs
- **State Management**: Redux Toolkit & React Hooks
- **Data Ingestion**: Axios / Fetch API (Polling strategy)
- **Deployment**: Dockerized with Nginx reverse proxy to FastAPI

---

## 3. Page Structure & Features

### 3.1 Dashboard (Command Center) - [Implemented]
The primary entry point combining trading performance with MLOps health.
- **KPI Section**: 
  - **FinOps**: Oracle Cloud cost tracking ($0.00/mo target).
  - **Architecture**: Compute platform status (ARM64 / A1).
  - **Social Sentiment**: Real-time NLP consensus (Fear/Greed).
  - **Memory Load**: Data ingestion RAM usage monitoring.
  - **Model Health**: Population Stability Index (PSI) tracking.
- **BTC/USD Terminal**:
  - **High-Precision Price**: Integrated "Market Live" status indicator (Emerald Pulse).
  - **Animated Waveform**: Custom SVG-based trend visualization with Gaussian blur filters.
  - **Tech Specs**: Real-time latency (P99) and node telemetry.
- **System Logs**:
  - **Pipeline Stdout**: Real-time terminal log stream with level-based color coding (INFO, SUCCESS, WARN, SYSTEM).

### 3.2 MLOps Console - [Implemented]
A dedicated deep-dive into the machine learning lifecycle.
- **Pipeline Pulse**: Animated DAG/Stage visualization (`Ingestion -> Training -> Deployment`).
- **Signal Stream**: Live ML-generated signals (BUY/SELL) with confidence scores and timestamps.

### 3.3 Admin "Commander Mode" - [Implemented]
- **Access**: Hidden authentication toggle (SSO/OIDC-Proxy simulation).
- **Subsystem Integration**: Deep links to Airflow, MLflow, FastAPI Docs, and Grafana.

---

## 4. Visual Identity

- **Theme**: **Cyber-Terminal Dark Mode**.
  - **Background**: Deep Space Black (`#0a0a0c`), Panel Surface (`#0f1115`).
  - **Primary (Success)**: Emerald Green (`#10b981`).
  - **Accent (Info)**: Electric Blue (`#60a5fa`).
  - **Alert (Warning)**: Rose Red (`#fb7185`).
- **Components**: Glassmorphism cards with `backdrop-filter: blur(10px)` and glowing borders (`shadow-glow`).
- **Typography**:
  - **Data**: `JetBrains Mono` / `font-mono` for technical precision.
  - **Interface**: `Inter` / `font-sans` for professional readability.

---

## 5. Implementation Progress

| Feature | Status | Detail |
| :--- | :--- | :--- |
| Cyber-Fintech Design System | ✅ Completed | Tailwind + Framer Motion |
| BTC/USD Terminal | ✅ Refined | Fixed layout & price scaling |
| MLOps Pipeline Flow | ✅ Completed | Animated stage visualization |
| Real-time Jitter Simulation | ✅ Completed | UI vibrancy for metrics |
| Commander Mode (Admin) | ✅ Completed | Subsystem navigation grid |
| Data Drift Monitoring | ✅ Completed | PSI metric integration |
| Docker Interoperability | ✅ Completed | Nginx Proxy to FastAPI (Port 3000 -> 8000) |
| Signal X-Ray (XAI) | ⏳ Planned | Deep weights visualization |
| Multi-Node Cluster View | ⏳ Planned | Multi-region telemetry |