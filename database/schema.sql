-- ============================================================
-- FraudShield AI — MySQL Schema Setup Script
-- Run this ONCE to initialize the database.
-- ============================================================

-- Create database
CREATE DATABASE IF NOT EXISTS fraudshield
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE fraudshield;

-- ----------------------------------------------------------------
-- Table: transactions
-- Stores raw transaction data submitted for analysis
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_type      ENUM('CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER') NOT NULL,
    amount                DECIMAL(18, 2) NOT NULL,
    origin_account        VARCHAR(50) NOT NULL,
    destination_account   VARCHAR(50) NOT NULL,
    origin_balance_before DECIMAL(18, 2) DEFAULT NULL COMMENT 'Origin account balance before transaction',
    origin_balance_after  DECIMAL(18, 2) DEFAULT NULL COMMENT 'Origin account balance after transaction',
    dest_balance_before   DECIMAL(18, 2) DEFAULT NULL COMMENT 'Destination account balance before transaction',
    dest_balance_after    DECIMAL(18, 2) DEFAULT NULL COMMENT 'Destination account balance after transaction',
    transaction_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_origin_account (origin_account),
    INDEX idx_transaction_timestamp (transaction_timestamp)
) ENGINE=InnoDB COMMENT='Raw financial transaction records';

-- ----------------------------------------------------------------
-- Table: predictions
-- Stores model prediction results for each transaction
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id                   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_id       BIGINT UNSIGNED NOT NULL,
    predicted_class      TINYINT NOT NULL COMMENT '0=Legitimate, 1=Fraudulent',
    fraud_probability    FLOAT NOT NULL COMMENT 'Model confidence score (0.0 - 1.0)',
    risk_category        ENUM('Low', 'Medium', 'High') NOT NULL,
    model_version        VARCHAR(20) NOT NULL,
    top_features         JSON DEFAULT NULL COMMENT 'SHAP feature importance for this prediction',
    prediction_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    INDEX idx_risk_category (risk_category),
    INDEX idx_predicted_class (predicted_class),
    INDEX idx_prediction_timestamp (prediction_timestamp)
) ENGINE=InnoDB COMMENT='ML model prediction results';

-- ----------------------------------------------------------------
-- Table: investigations
-- Case management for suspicious transactions
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigations (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    prediction_id       BIGINT UNSIGNED NOT NULL,
    case_status         ENUM('Open', 'Under Review', 'Escalated', 'Resolved', 'False Positive') NOT NULL DEFAULT 'Open',
    assigned_to         VARCHAR(100) DEFAULT NULL,
    investigation_notes TEXT DEFAULT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE,
    INDEX idx_case_status (case_status),
    INDEX idx_assigned_to (assigned_to)
) ENGINE=InnoDB COMMENT='Fraud investigation case management';

-- ----------------------------------------------------------------
-- Table: model_versions
-- Registry of trained model versions and their metrics
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_versions (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_name       VARCHAR(100) NOT NULL COMMENT 'e.g., XGBoost, RandomForest, LogisticRegression',
    model_version    VARCHAR(20) NOT NULL,
    training_date    DATETIME NOT NULL,
    is_active        TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 = currently deployed model',
    precision_score  FLOAT DEFAULT NULL,
    recall_score     FLOAT DEFAULT NULL,
    f1_score         FLOAT DEFAULT NULL,
    roc_auc_score    FLOAT DEFAULT NULL,
    pr_auc_score     FLOAT DEFAULT NULL,
    training_samples BIGINT UNSIGNED DEFAULT NULL,
    test_samples     BIGINT UNSIGNED DEFAULT NULL,
    threshold        FLOAT DEFAULT 0.5 COMMENT 'Decision threshold used for classification',
    model_params     JSON DEFAULT NULL COMMENT 'Hyperparameters used during training',
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_model_version (model_name, model_version),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB COMMENT='Registry of trained ML model versions';

-- ============================================================
-- Create a dedicated user (replace password before running)
-- ============================================================
-- CREATE USER IF NOT EXISTS 'fraudshield_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
-- GRANT ALL PRIVILEGES ON fraudshield.* TO 'fraudshield_user'@'localhost';
-- FLUSH PRIVILEGES;

SELECT 'FraudShield AI database schema created successfully.' AS status;
