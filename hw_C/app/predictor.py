from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np

from app import config


class ModelPredictor:
    def __init__(self, model, run_id: str):
        self.model = model
        self.run_id = run_id
        self.expected_input_columns = list(config.EXPECTED_FEATURE_COLUMNS)
        self.model_feature_names = self._get_model_feature_names()

    def _get_model_feature_names(self) -> List[str]:
        """Feature names the fitted model expects (after encoding)."""
        if hasattr(self.model, "feature_names_in_"):
            return list(self.model.feature_names_in_)

        if hasattr(self.model, "named_steps"):
            for step in reversed(list(self.model.named_steps.values())):
                if hasattr(step, "feature_names_in_"):
                    return list(step.feature_names_in_)

        # fallback: assume raw expected columns
        return list(self.expected_input_columns)

    def _validate_forbidden(self, features: Dict[str, Any]):
        forbidden = set(config.FORBIDDEN_FIELDS).intersection(set(features.keys()))
        if forbidden:
            raise ValueError(
                f"Forbidden leakage/audit/target fields found: {sorted(forbidden)}"
            )

    def _build_raw_dataframe(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        for item in records:
            self._validate_forbidden(item)

        df = pd.DataFrame(records)

        # keep only expected input columns; create missing ones as NaN
        for col in self.expected_input_columns:
            if col not in df.columns:
                df[col] = np.nan

        df = df[self.expected_input_columns]

        # normalize boolean-like fields
        for bool_col in ["instant_bookable", "host_is_superhost"]:
            if bool_col in df.columns:
                df[bool_col] = (
                    df[bool_col]
                    .astype(str)
                    .str.lower()
                    .map({
                        "t": 1, "true": 1, "1": 1, "yes": 1,
                        "f": 0, "false": 0, "0": 0, "no": 0,
                        "nan": 0, "none": 0,
                    })
                    .fillna(0)
                    .astype(int)
                )

        return df

    def _encode_and_align(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """One-hot encode categoricals and align to model's expected features."""
        df = df_raw.copy()

        cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if cat_cols:
            df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)

        # add any missing model features as 0, drop extras, order exactly
        for col in self.model_feature_names:
            if col not in df.columns:
                df[col] = 0

        df = df[self.model_feature_names]
        return df

    def _prepare(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        df_raw = self._build_raw_dataframe(records)
        X = self._encode_and_align(df_raw)
        return X

    def _label(self, pred: int) -> str:
        return config.POSITIVE_LABEL if pred == 1 else config.NEGATIVE_LABEL

    def predict_one(self, features: Dict[str, Any]) -> Tuple[int, float, str]:
        X = self._prepare([features])

        if hasattr(self.model, "predict_proba"):
            prob = float(self.model.predict_proba(X)[0][1])
            pred = int(prob >= config.PREDICTION_THRESHOLD)
        else:
            pred = int(self.model.predict(X)[0])
            prob = float(pred)

        return pred, prob, self._label(pred)

    def predict_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        X = self._prepare(records)

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)[:, 1]
            preds = (probs >= config.PREDICTION_THRESHOLD).astype(int)
        else:
            preds = self.model.predict(X).astype(int)
            probs = preds.astype(float)

        results = []
        for pred, prob in zip(preds, probs):
            results.append(
                {
                    "prediction": int(pred),
                    "probability": float(prob),
                    "label": self._label(int(pred)),
                }
            )
        return results