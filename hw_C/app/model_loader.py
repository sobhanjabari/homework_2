import mlflow
import mlflow.sklearn

from app import config


def setup_mlflow():
    mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)


def resolve_run_id() -> str:
    """
    Decide which run to load.
    Priority:
    1. MLFLOW_RUN_ID env var (if set)
    2. Best run from the experiment by test_auc
    """
    if config.MLFLOW_RUN_ID:
        return config.MLFLOW_RUN_ID

    return _auto_select_best_run()


def _auto_select_best_run() -> str:
    experiment = mlflow.get_experiment_by_name(config.MLFLOW_EXPERIMENT_NAME)
    if experiment is None:
        raise RuntimeError(
            f"Experiment '{config.MLFLOW_EXPERIMENT_NAME}' not found and no MLFLOW_RUN_ID provided."
        )

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.test_auc DESC"],
    )

    if runs.empty:
        raise RuntimeError("No runs found in experiment and no MLFLOW_RUN_ID provided.")

    # Prefer valid, non-leaky models if those tags exist
    if "tags.valid_model" in runs.columns:
        valid = runs[runs["tags.valid_model"] == "true"]
        if not valid.empty:
            runs = valid

    if "tags.leakage_status" in runs.columns:
        clean = runs[runs["tags.leakage_status"] == "clean"]
        if not clean.empty:
            runs = clean

    return runs.iloc[0]["run_id"]


def load_model():
    """Load the sklearn model from MLflow and return (model, run_id)."""
    setup_mlflow()
    run_id = resolve_run_id()

    model_uri = f"runs:/{run_id}/model"
    try:
        model = mlflow.sklearn.load_model(model_uri)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load model from {model_uri}. Error: {e}"
        )

    return model, run_id