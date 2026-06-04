from typing import Any, Dict, List
from pydantic import BaseModel, Field, model_validator

from app.config import FORBIDDEN_FIELDS, EXPECTED_FEATURE_COLUMNS


def _check_forbidden(features: Dict[str, Any], where: str = "request"):
    forbidden_found = set(FORBIDDEN_FIELDS).intersection(set(features.keys()))
    if forbidden_found:
        raise ValueError(
            f"Forbidden leakage/audit/target fields found in {where}: {sorted(forbidden_found)}"
        )


class PredictRequest(BaseModel):
    features: Dict[str, Any] = Field(
        ...,
        description="Dictionary of model input features. Forbidden leakage fields are rejected."
    )

    @model_validator(mode="after")
    def validate_features(self):
        _check_forbidden(self.features, "features")
        return self


class BatchPredictRequest(BaseModel):
    instances: List[Dict[str, Any]] = Field(
        ...,
        description="List of feature dictionaries."
    )

    @model_validator(mode="after")
    def validate_instances(self):
        for i, item in enumerate(self.instances):
            _check_forbidden(item, f"instance[{i}]")
        return self


class PredictResponse(BaseModel):
    prediction: int
    probability: float
    label: str


class BatchPredictResponse(BaseModel):
    predictions: List[PredictResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    app_title: str
    app_version: str
    model_run_id: str
    model_type: str
    dataset_version: str
    target_name: str
    positive_label: str
    negative_label: str
    prediction_threshold: float
    expected_features_count: int
    expected_feature_columns: List[str]
    forbidden_fields: List[str]