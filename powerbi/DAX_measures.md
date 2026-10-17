# Power BI dashboard measures

Import:
- `outputs/cleaned_customers.csv` as `customers`
- `outputs/churn_predictions.csv` as `predictions`

Create a relationship: `customers[customerID]` (one) → `predictions[customerID]` (one).
If Power BI detects a different cardinality, verify that customer IDs are unique in both files.

Create these measures (Modeling > New measure). DAX formulas are written for tables named `customers` and `predictions`.

```DAX
Total Customers = DISTINCTCOUNT(customers[customerID])

Churned Customers =
CALCULATE(
    DISTINCTCOUNT(customers[customerID]),
    customers[Churn] = "Yes"
)

Churn Rate % =
DIVIDE([Churned Customers], [Total Customers], 0)

Average Monthly Charges =
AVERAGE(customers[MonthlyCharges])

High Risk Customers =
CALCULATE(
    DISTINCTCOUNT(predictions[customerID]),
    predictions[RiskBand] = "High"
)

Average Churn Probability =
AVERAGE(predictions[ChurnProbability])

High Risk Monthly Charges =
CALCULATE(
    SUM(customers[MonthlyCharges]),
    TREATAS(
        CALCULATETABLE(
            VALUES(predictions[customerID]),
            predictions[RiskBand] = "High"
        ),
        customers[customerID]
    )
)
```

Format `Churn Rate %` as Percentage. Format probability as Percentage if desired.

## Page 1: Executive Overview
- Cards: Total Customers, Churned Customers, Churn Rate %, High Risk Customers
- Bar chart: Churn rate by Contract
- Bar chart: Churn rate by InternetService
- Donut chart: Churn vs No churn
- Slicers: Contract, InternetService, PaymentMethod

## Page 2: Risk & Retention
- Table: customerID, ChurnProbability, RiskBand, Contract, tenure, MonthlyCharges
- Bar chart: count of customers by RiskBand
- Scatter plot: tenure vs MonthlyCharges, legend = RiskBand
- Card: High Risk Monthly Charges

## Important interpretation
`High Risk Monthly Charges` is monthly charges associated with customers in the demo high-risk band; it is not guaranteed revenue loss. Churn probability thresholds (35% and 65%) are illustrative. Choose thresholds using validation data, retention capacity, intervention costs, and business value.
