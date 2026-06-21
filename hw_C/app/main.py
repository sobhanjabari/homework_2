from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app import config
from app.schemas import (
    PredictRequest,
    BatchPredictRequest,
    PredictResponse,
    BatchPredictResponse,
    HealthResponse,
    ModelInfoResponse,
)
from app.model_loader import load_model
from app.predictor import ModelPredictor


app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    description="FastAPI service serving the selected HW02 MLflow model for listing availability prediction.",
)

predictor: ModelPredictor | None = None
model_run_id: str = ""


@app.on_event("startup")
def startup_event():
    global predictor, model_run_id
    try:
        model, run_id = load_model()
        predictor = ModelPredictor(model=model, run_id=run_id)
        model_run_id = run_id
        print(f"[startup] Model loaded successfully. run_id={run_id}")
    except Exception as e:
        print(f"[startup] Model failed to load: {e}")
        predictor = None
        model_run_id = ""


@app.get("/")
def root():
    return {
        "message": f"{config.APP_TITLE} is running.",
        "version": config.APP_VERSION,
        "docs": "/docs",
        "docs_url": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok" if predictor is not None else "model_not_loaded",
        model_loaded=predictor is not None,
    )


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    return ModelInfoResponse(
        app_title=config.APP_TITLE,
        app_version=config.APP_VERSION,
        model_run_id=model_run_id,
        model_type=type(predictor.model).__name__,
        dataset_version=config.DATASET_VERSION,
        target_name=config.TARGET_NAME,
        positive_label=config.POSITIVE_LABEL,
        negative_label=config.NEGATIVE_LABEL,
        prediction_threshold=config.PREDICTION_THRESHOLD,
        expected_features_count=len(config.EXPECTED_FEATURE_COLUMNS),
        expected_feature_columns=list(config.EXPECTED_FEATURE_COLUMNS),
        forbidden_fields=list(config.FORBIDDEN_FIELDS),
    )


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    try:
        pred, prob, label = predictor.predict_one(request.features)
        return PredictResponse(prediction=pred, probability=prob, label=label)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@app.post("/predict-batch", response_model=BatchPredictResponse)
def predict_batch(request: BatchPredictRequest):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    try:
        results = predictor.predict_batch(request.instances)
        return BatchPredictResponse(predictions=results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")