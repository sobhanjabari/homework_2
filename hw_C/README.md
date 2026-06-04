# HW03 - Serving HW02 Model with FastAPI and Swagger

This project serves the model selected and tracked in HW02 as a FastAPI service,
tested through Swagger.

## Selected HW02 Model

- Run name: `run5_tree_based_random_forest_clean`
- Run ID: `78b941ee9925435dbde9df7329d2a7cc`
- Model type: `RandomForestClassifier`
- Experiment: `qbc12_hw02_sobhan_jabari`

This model was selected because it achieved the best valid performance among the
non-future-leaky HW02 runs (highest test AUC and F1 with a small train-test gap).

## What is the artifact folder?

In MLflow, when a model is logged, its serialized files (such as `MLmodel`,
`model.pkl`, environment files) are stored as **artifacts** of the run.
This API loads the model from the MLflow artifact path:

```text
runs:/78b941ee9925435dbde9df7329d2a7cc/model