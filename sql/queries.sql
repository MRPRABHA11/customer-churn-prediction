-- Run these against outputs/customer_churn.db (SQLite syntax)

-- 1. Total customers
SELECT COUNT(*) AS total_customers
FROM customers;

-- 2. Churn count and churn rate
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM customers;

-- 3. Churn rate by contract
SELECT
    Contract,
    COUNT(*) AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0.0 END), 2) AS churn_rate_pct
FROM customers
GROUP BY Contract
ORDER BY churn_rate_pct DESC;

-- 4. Churn rate by internet service
SELECT
    InternetService,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0.0 END), 2) AS churn_rate_pct
FROM customers
GROUP BY InternetService
ORDER BY churn_rate_pct DESC;

-- 5. Average monthly charges: churned vs retained
SELECT
    Churn,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months
FROM customers
GROUP BY Churn;

-- 6. Payment method churn comparison
SELECT
    PaymentMethod,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0.0 END), 2) AS churn_rate_pct
FROM customers
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;

-- 7. High-risk predicted customers for retention review
SELECT
    p.customerID,
    p.ChurnProbability,
    p.RiskBand,
    c.Contract,
    c.tenure,
    c.MonthlyCharges
FROM predictions p
JOIN customers c ON c.customerID = p.customerID
WHERE p.RiskBand = 'High'
ORDER BY p.ChurnProbability DESC
LIMIT 100;

-- 8. Monthly charges at risk among high-risk customers (rough prioritization proxy)
SELECT
    COUNT(*) AS high_risk_customers,
    ROUND(SUM(c.MonthlyCharges), 2) AS monthly_charges_exposed
FROM predictions p
JOIN customers c ON c.customerID = p.customerID
WHERE p.RiskBand = 'High';
