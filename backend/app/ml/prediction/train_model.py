"""
FindMyPark: train the 60-minute parking occupancy forecasting model.

Usage from the repository root:
    python backend/app/ml/prediction/train_model.py --data "C:\path\to\dataset.csv"

The script saves the model and matching preprocessor beside this file.
It follows the final 60-minute forecasting workflow in the Colab notebook.
"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        required=True,
        help="Path to the Birmingham parking CSV dataset on your computer.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.data).expanduser()
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}\n"
            "Pass the correct local CSV path using --data."
        )

    df = pd.read_csv(dataset_path)

    required_columns = {"SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")

    print("Original dataset shape:", df.shape)

    # Match the notebook's cleaning steps.
    df["LastUpdated"] = pd.to_datetime(df["LastUpdated"], errors="coerce")
    df = df.dropna(
        subset=["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"]
    ).copy()
    df = df.drop_duplicates()
    df = df[df["Occupancy"] >= 0].copy()

    print("Rows after cleaning:", len(df))
    print("Parking locations:", df["SystemCodeNumber"].nunique())

    # Build a 60-minute future target by matching a later reading at the same lot.
    forecast_df = df.sort_values(
        ["SystemCodeNumber", "LastUpdated"]
    ).copy()

    future = forecast_df[   
["SystemCodeNumber", "LastUpdated", "Occupancy"]
    ].copy().rename(
        columns={
            "LastUpdated": "FutureTime",
            "Occupancy": "FutureOccupancy",
        }
    )

    forecast_df["TargetTime"] = (
        forecast_df["LastUpdated"] + pd.Timedelta(minutes=60)
    )

    # merge_asof requires the merge keys to be sorted.
    forecast_df = forecast_df.sort_values("TargetTime")
    future = future.sort_values("FutureTime")

    forecast_df = pd.merge_asof(
        forecast_df,
        future,
        left_on="TargetTime",
        right_on="FutureTime",
        by="SystemCodeNumber",
        direction="forward",
        tolerance=pd.Timedelta(minutes=2),
    )

    forecast_df = forecast_df.dropna(subset=["FutureOccupancy"]).copy()
    if len(forecast_df) < 10:
        raise ValueError(
            "Too few rows have a matching future observation about 60 minutes later. "
            "Check the dataset and its timestamps."
        )

    forecast_df["Hour"] = forecast_df["LastUpdated"].dt.hour
    forecast_df["DayOfWeek"] = forecast_df["LastUpdated"].dt.dayofweek
    forecast_df["Month"] = forecast_df["LastUpdated"].dt.month
    forecast_df["IsWeekend"] = (
        forecast_df["DayOfWeek"] >= 5
    ).astype(int)

    feature_columns = [
        "SystemCodeNumber",
        "Capacity",
        "Hour",
        "DayOfWeek",
        "Month",
        "IsWeekend",
        "Occupancy",
    ]

    X = forecast_df[feature_columns].copy()
    y = forecast_df["FutureOccupancy"].astype(float)

    # Chronological 80/20 split, matching the notebook.
    forecast_df = forecast_df.sort_values("LastUpdated").copy()
    X = forecast_df[feature_columns].copy()
    y = forecast_df["FutureOccupancy"].astype(float)
    split_index = int(len(forecast_df) * 0.8)

    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    if len(X_train) == 0 or len(X_test) == 0:
        raise ValueError("Not enough matched rows for an 80/20 train/test split.")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "location",
                OneHotEncoder(handle_unknown="ignore"),
                ["SystemCodeNumber"],
            ),
            (
                "numeric",
                "passthrough",
                [c for c in feature_columns if c != "SystemCodeNumber"],
            ),
        ]
    )

    X_train_encoded = preprocessor.fit_transform(X_train)
    X_test_encoded = preprocessor.transform(X_test)

    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_encoded, y_train)

    predictions = model.predict(X_test_encoded)
    predictions = np.clip(predictions, 0, X_test["Capacity"].to_numpy())
    baseline = X_test["Occupancy"].to_numpy()

    print("\n60-MINUTE FORECAST RESULTS")
    print("Training observations:", len(X_train))
    print("Testing observations:", len(X_test))
    print(f"XGBoost MAE: {mean_absolute_error(y_test, predictions):.2f} spaces")
    print(
        f"XGBoost RMSE: "
        f"{np.sqrt(mean_squared_error(y_test, predictions)):.2f} spaces"
    )
    print(f"Baseline MAE: {mean_absolute_error(y_test, baseline):.2f} spaces")
    print(
        f"Baseline RMSE: "
        f"{np.sqrt(mean_squared_error(y_test, baseline)):.2f} spaces"
    )

    # Save beside this script so the backend can load the files from a stable path.
    output_dir = Path(__file__).resolve().parent
    model_path = output_dir / "findmypark_xgboost_60min.pkl"
    preprocessor_path = output_dir / "findmypark_preprocessor_60min.pkl"

    joblib.dump(model, model_path)
    joblib.dump(preprocessor, preprocessor_path)

    print("\nSaved model:", model_path)
    print("Saved preprocessor:", preprocessor_path)
    print("Training completed successfully.")


if __name__ == "__main__":
    main()