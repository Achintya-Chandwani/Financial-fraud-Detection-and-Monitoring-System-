<div align="center">

# 🛡️ FraudShield AI

### End-to-End Intelligent Financial Fraud Detection & Monitoring Platform

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online%20Dashboard-brightgreen?style=for-the-badge&logo=googlechrome&logoColor=white)](https://achintya-chandwani.github.io/Financial-fraud-Detection-and-Monitoring-System-/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Achintya-Chandwani/Financial-fraud-Detection-and-Monitoring-System-)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML_Model-FF6600?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-FF4B4B?style=for-the-badge)](https://shap.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**A production-grade machine learning platform that detects financial transaction fraud in real-time using XGBoost with SHAP explainability, served through an asynchronous FastAPI backend and a dark-mode SaaS dashboard.**

---

### 🌐 [Click Here to View the Live Deployed Platform](https://achintya-chandwani.github.io/Financial-fraud-Detection-and-Monitoring-System-/)
*No installation required — launch the interactive dashboard, run transactions through the analyzer, and explore SHAP explanations directly in your browser.*

</div>

---

## 📸 Screenshots & Live UI

### Real-Time Monitoring Dashboard
![FraudShield AI Dashboard](docs/screenshots/dashboard.png)
*Live monitoring dashboard with fraud distribution analytics, risk category breakdowns, and 7-day transaction trend tracking.*

### Transaction Analyzer with SHAP Explainability
![Transaction Analyzer with SHAP Results](docs/screenshots/analyzer.png)
*A suspicious TRANSFER of $350,000 flagged at **99.92% fraud probability** with SHAP feature importance breaking down the risk drivers.*

### Model Performance Metrics
![Model Performance Page](docs/screenshots/model.png)
*XGBoost metrics: Precision, Recall, F1-Score, ROC-AUC, PR-AUC with confusion matrix and feature rankings.*

---

## ⚡ Key Features

| Feature | Description |
|---|---|
| **XGBoost Classifier** | Trained on financial transaction logs with SMOTE class balancing for extreme imbalance |
| **SHAP Explainability** | Every individual prediction provides TreeExplainer feature attribution for auditability |
| **Real-Time Scoring** | Sub-second risk scoring with categorization (High, Medium, Low Risk) |
| **Live Interactive Dashboard** | Dark glassmorphism SaaS UI with Chart.js analytics and responsive layout |
| **Interactive Analyzer** | Form to submit custom transactions and see instant risk metrics and SHAP bars |
| **Batch CSV Processing** | Bulk CSV transaction upload with vectorized prediction pipelines |
| **Case Management** | Investigation workflow with status tracking (Open, Under Review, Escalated, Resolved) |
| **Database Persistence** | Relational history and transaction logging via SQLAlchemy + MySQL |
| **RESTful API** | 12+ FastAPI endpoints with auto-generated OpenAPI/Swagger documentation |
| **Comprehensive Test Suite** | 33 unit and integration tests covering the API routes and ML service |

---

## 🏛️ System Architecture

```
Frontend (Vanilla JS SPA)  <───>  Backend (FastAPI REST)  <───>  ML Pipeline (Python)
├── Live Monitoring Dashboard      ├── Pydantic Validation         ├── XGBoost Classifier
├── Transaction Analyzer (SHAP)    ├── SQLAlchemy ORM              ├── SMOTE Balancing
├── Batch CSV Processor            ├── CORS & Async Handlers       ├── SHAP TreeExplainer
├── Investigation Management       └── MySQL 8.0 Persistence       └── Joblib Artifacts
└── Model Evaluation Suite
```

---

## 🛠️ Technology Stack

### Machine Learning & Data Science
* **XGBoost**: Primary gradient boosted classifier optimized for tabular fraud patterns.
* **scikit-learn**: Feature scaling (`StandardScaler`), metric evaluations, and pipeline assembly.
* **imbalanced-learn**: SMOTE oversampling to counter severe fraud label imbalance (~1%).
* **SHAP**: Game-theoretic feature attribution explanations (TreeExplainer).
* **Pandas & NumPy**: High-performance vectorized data manipulation.
* **Joblib**: Efficient serialization of trained model pipelines.

### Backend Infrastructure
* **FastAPI**: Modern, high-performance async Python web framework.
* **Uvicorn**: Lightning-fast ASGI production web server.
* **SQLAlchemy & PyMySQL**: Production ORM and connector for MySQL relational storage.
* **Pydantic v2**: Type-safe input and output data validation.
* **Loguru**: Structured, formatted logging.

### Frontend
* **Vanilla JavaScript (ES6+)**: Zero-framework, lightweight SPA client.
* **Chart.js**: Dynamic doughnut, line, and bar chart visualizations.
* **Modern CSS3**: Dark-mode glassmorphism design system with responsive layouts.

---

## 🚀 Quickstart & Setup

### Option 1: Live Web Demo (Zero Install)
You can test the frontend immediately via GitHub Pages:
👉 **[Open Live Demo](https://achintya-chandwani.github.io/Financial-fraud-Detection-and-Monitoring-System-/)**

---

### Option 2: Run Locally (Full Stack with Backend & DB)

#### 1. Clone the Repository
```bash
git clone https://github.com/Achintya-Chandwani/Financial-fraud-Detection-and-Monitoring-System-.git
cd Financial-fraud-Detection-and-Monitoring-System-
```

#### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 3. Environment Configuration
Copy the example environment file and update your MySQL settings:
```bash
cp .env.example .env
```
Default configuration (`.env`):
```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fraudshield
DB_USER=root
DB_PASSWORD=your_mysql_password
```

#### 4. Train the Machine Learning Model
```bash
# Standalone training script (trains XGBoost, runs evaluation, exports artifacts)
python train_model.py
```

#### 5. Launch Application Services

* **Windows 1-Click Startup:**
  Simply run:
  ```cmd
  start_project.bat
  ```

* **Manual Startup (Terminal 1 - FastAPI Backend):**
  ```bash
  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
  ```

* **Manual Startup (Terminal 2 - Frontend Server):**
  ```bash
  python -m http.server 5500 --directory frontend
  ```

#### 6. Open in Browser

| Interface | URL |
|---|---|
| **Monitoring Dashboard** | [http://localhost:5500](http://localhost:5500) |
| **Transaction Analyzer** | [http://localhost:5500/pages/analyzer.html](http://localhost:5500/pages/analyzer.html) |
| **Model Performance** | [http://localhost:5500/pages/model.html](http://localhost:5500/pages/model.html) |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 📊 Dataset & Feature Engineering

* **Dataset:** Based on the **PaySim** mobile money financial dataset (synthetic financial logs modeling real mobile money transactions).
* **Key Engineered Features:**
  - `amount`: Raw transaction volume in USD.
  - `balance_diff_origin`: Difference between old and new sender balance.
  - `balance_diff_dest`: Difference between new and old recipient balance.
  - `amount_to_origin_ratio`: Amount divided by origin balance (detects total account draining).
  - `is_large_transfer`: Indicator for transfers exceeding typical daily limits ($200,000+).
  - `transaction_type_encoded`: Categorical encoding (`TRANSFER`, `CASH_OUT`, `DEBIT`, `PAYMENT`, `CASH_IN`).

---

## 📡 API Reference Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, DB connectivity & model status |
| `POST` | `/api/predict` | Single transaction fraud evaluation with SHAP breakdown |
| `POST` | `/api/predict/batch` | Bulk transaction CSV scoring |
| `GET` | `/api/dashboard/stats` | High-level fraud rates and volume summaries |
| `GET` | `/api/dashboard/trend` | Multi-day transaction volume and flag trends |
| `GET` | `/api/transactions` | Filterable, paginated transaction history |
| `GET` | `/api/investigations` | Active investigation cases |
| `PATCH`| `/api/investigations/{id}` | Update case status (`Under Review`, `Resolved`, etc.) |

---

## 🧪 Unit & Integration Tests

Run the test suite using pytest:
```bash
# Run all tests (utilizes SQLite in-memory, no external database needed)
pytest

# Run with coverage report
pytest --cov=backend --cov-report=term-missing
```

---

## 👤 Author

**Achintya Chandwani**
* GitHub: [@Achintya-Chandwani](https://github.com/Achintya-Chandwani)
* Email: chandwaniachintya@gmail.com

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
