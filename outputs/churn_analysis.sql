
-- 1. Total customers
SELECT COUNT(*) AS total_customers
FROM cleaned_customers;

-- 2. Churn count
SELECT Churn, COUNT(*) AS customer_count
FROM cleaned_customers
GROUP BY Churn;

-- 3. Churn rate by contract
SELECT
    Contract,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(
        100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS churn_rate_pct
FROM cleaned_customers
GROUP BY Contract
ORDER BY churn_rate_pct DESC;

-- 4. Churn rate by payment method
SELECT
    PaymentMethod,
    COUNT(*) AS total_customers,
    ROUND(
        100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS churn_rate_pct
FROM cleaned_customers
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;
