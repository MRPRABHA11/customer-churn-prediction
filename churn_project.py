from pathlib import Path
import argparse
import json
import sqlite3
import warnings

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, roc_auc_score,
    balanced_accuracy_score
)
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import roc_curve


warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"customerID", "Churn", "tenure", "Contract", "MonthlyCharges", "TotalCharges"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing expected columns: {sorted(missing)}")
    df = df.drop_duplicates(subset=["customerID"]).copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["Churn"] = df["Churn"].astype(str).str.strip()
    df = df[df["Churn"].isin(["Yes", "No"])].copy()
    df["ChurnFlag"] = df["Churn"].map({"No": 0, "Yes": 1}).astype(int)
    return df

def run_eda(df: pd.DataFrame) -> None:
    sns.set_theme()
    plt.figure(figsize=(6, 4))
    sns.countplot(data=df, x="Churn")
    plt.title("Customer Churn Distribution")
    plt.tight_layout()
    plt.savefig(OUT / "churn_distribution.png", dpi=150)
    plt.close()

    if "Contract" in df.columns:
        churn_rate = df.groupby("Contract", observed=False)["ChurnFlag"].mean().sort_values(ascending=False)
        plt.figure(figsize=(8, 4))
        churn_rate.plot(kind="bar")
        plt.ylabel("Churn rate")
        plt.title("Churn Rate by Contract Type")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(OUT / "churn_by_contract.png", dpi=150)
        plt.close()

def build_pipeline(X: pd.DataFrame) -> Pipeline:
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = X.select_dtypes(exclude=["number"]).columns.tolist()

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])
    prep = ColumnTransformer([
        ("numeric", numeric_pipe, numeric_cols),
        ("categorical", categorical_pipe, categorical_cols)
    ])
    return Pipeline([
        ("preprocess", prep),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42))
    ])

def main():
    parser = argparse.ArgumentParser(description="Telco customer churn prediction workflow")
    parser.add_argument("--data", default=str(ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"))
    args = parser.parse_args()
    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Could not find {data_path}. Download the dataset and place it in data/, "
            "or pass --data with the correct CSV path."
        )

    df = load_data(data_path)
    print(f"Loaded {len(df):,} unique customers and {df.shape[1]} columns.")
    print("\nChurn distribution:")
    print(df["Churn"].value_counts())
    print(f"\nOverall churn rate: {df['ChurnFlag'].mean():.2%}")
    print("\nMissing values (top 10):")
    print(df.isna().sum().sort_values(ascending=False).head(10))

    run_eda(df)

    # Exclude target and customer ID from model inputs
    X = df.drop(columns=["Churn", "ChurnFlag", "customerID"])
    y = df["ChurnFlag"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Train evaluation model
    eval_model = build_pipeline(X_train)
    eval_model.fit(X_train, y_train)

    # Get churn probabilities
    prob = eval_model.predict_proba(X_test)[:, 1]

    # Compare different thresholds
    print("\nThreshold Comparison:")
    print("-" * 55)
    print(f"{'Threshold':<12}{'Recall':<15}{'Precision':<15}{'F1 Score':<10}")
    print("-" * 55)

    for threshold in [0.20,0.25, 0.30, 0.35, 0.40, 0.45]:
        pred_temp = (prob >= threshold).astype(int)

        recall = recall_score(y_test, pred_temp, zero_division=0)
        precision = precision_score(y_test, pred_temp, zero_division=0)
        f1 = f1_score(y_test, pred_temp, zero_division=0)

        print(
            f"{threshold:<12.2f}{recall:<15.4f}"
            f"{precision:<15.4f}{f1:<10.4f}"
        )

    # Use 0.35 for the main evaluation
    threshold = 0.35
    pred = (prob >= threshold).astype(int)

    metrics = {
        "test_rows": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "precision_churn_class": float(precision_score(y_test, pred, zero_division=0)),
        "recall_churn_class": float(recall_score(y_test, pred, zero_division=0)),
        "f1_churn_class": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, prob)),
        "baseline_accuracy_predict_no_churn": float((y_test == 0).mean()),
        "classification_report": classification_report(
            y_test, pred,
            target_names=["No churn", "Churn"],
            output_dict=True,
            zero_division=0
        )
    }

    with open(OUT / "model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\nHeld-out test metrics:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")

    print("\nClassification report:")
    print(classification_report(
        y_test, pred,
        target_names=["No churn", "Churn"],
        zero_division=0
    ))

    cm = confusion_matrix(y_test, pred)
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Predicted No", "Predicted Yes"],
                yticklabels=["Actual No", "Actual Yes"])
    plt.title("Confusion Matrix (Held-out Test Set)")
    plt.tight_layout()
    plt.savefig(OUT / "confusion_matrix.png", dpi=150)
    plt.close()
    
    # ROC Curve
    fpr, tpr, roc_thresholds = roc_curve(y_test, prob)
    roc_auc_value = roc_auc_score(y_test, prob)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {roc_auc_value:.4f})")
    plt.plot([0, 1], [0, 1], linestyle="--", label="Random Model")

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Customer Churn Prediction")
    plt.legend()
    plt.tight_layout()

    plt.savefig(OUT / "roc_curve.png", dpi=150)
    plt.close()

    # Feature Importance Analysis
    print("\nCalculating Feature Importance...")

    importance_result = permutation_importance(
        eval_model,
        X_test,
        y_test,
        n_repeats=10,
        random_state=42,
        scoring="roc_auc"
    )

    importance_df = pd.DataFrame({
        "Feature": X_test.columns,
        "Importance": importance_result.importances_mean
    }).sort_values("Importance", ascending=False)

    print("\nTop 15 Important Features:")
    print(importance_df.head(15).to_string(index=False))

    # Plot top 15 features
    top_features = importance_df.head(15).sort_values("Importance")

    plt.figure(figsize=(9, 6))
    plt.barh(top_features["Feature"], top_features["Importance"])
    plt.xlabel("Decrease in ROC-AUC when feature is shuffled")
    plt.title("Top 15 Feature Importance - Churn Prediction")
    plt.tight_layout()
    plt.savefig(OUT / "feature_importance.png", dpi=150)
    plt.close()

    importance_df.to_csv(OUT / "feature_importance.csv", index=False)

    print("Feature importance saved successfully!")


    print("ROC Curve saved successfully!")


    # Fit a separate final model on all labeled rows for a dashboard demo.
    # These scores are not held-out test predictions and should not be used to report metrics.
    # Fit final model for dashboard predictions
    
    # Feature Importance Analysis
  

    final_model = build_pipeline(X)
    final_model.fit(X, y)
    joblib.dump(final_model, OUT / "churn_model.joblib")

    all_prob = final_model.predict_proba(X)[:, 1]

    scored = df[["customerID", "Churn", "ChurnFlag"]].copy()
    scored["ChurnProbability"] = all_prob

    scored["RiskBand"] = pd.cut(
        scored["ChurnProbability"],
        bins=[-0.001, 0.35, 0.65, 1.001],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    ).astype(str)

    clean_export = df.copy()
    clean_export.to_csv(OUT / "cleaned_customers.csv", index=False)
    scored.to_csv(OUT / "churn_predictions.csv", index=False)

    db_path = OUT / "customer_churn.db"
    with sqlite3.connect(db_path) as conn:
        clean_export.to_sql("customers", conn, if_exists="replace", index=False)
        scored.to_sql("predictions", conn, if_exists="replace", index=False)

    print(f"\nOutputs saved to: {OUT}")
    print("Reminder: risk-band cutoffs are demonstration thresholds, not calibrated business decisions.")
if __name__ == "__main__":
    main()