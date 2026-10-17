-- Optional reference schema for PostgreSQL if you want a server database.
-- For the starter kit, the Python script creates a SQLite database automatically.

CREATE TABLE customers (
    customerID VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(20),
    SeniorCitizen INTEGER,
    Partner VARCHAR(5),
    Dependents VARCHAR(5),
    tenure INTEGER,
    PhoneService VARCHAR(5),
    MultipleLines VARCHAR(30),
    InternetService VARCHAR(30),
    OnlineSecurity VARCHAR(30),
    OnlineBackup VARCHAR(30),
    DeviceProtection VARCHAR(30),
    TechSupport VARCHAR(30),
    StreamingTV VARCHAR(30),
    StreamingMovies VARCHAR(30),
    Contract VARCHAR(30),
    PaperlessBilling VARCHAR(5),
    PaymentMethod VARCHAR(50),
    MonthlyCharges NUMERIC,
    TotalCharges NUMERIC,
    Churn VARCHAR(5),
    ChurnFlag INTEGER
);
