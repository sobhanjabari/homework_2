@echo off
setlocal

echo ==========================================
echo HW03 FastAPI Model Serving - Local Runner
echo ==========================================

REM Move to the directory of this script
cd /d "%~dp0"

REM ------------------------------------------
REM Create virtual environment if it does not exist
REM ------------------------------------------
if not exist ".venv_hw03\Scripts\activate.bat" (
    echo Creating virtual environment .venv_hw03 ...
    python -m venv .venv_hw03
)

REM ------------------------------------------
REM Activate virtual environment
REM ------------------------------------------
echo Activating virtual environment ...
call ".venv_hw03\Scripts\activate.bat"

REM ------------------------------------------
REM Upgrade pip and install requirements
REM ------------------------------------------
echo Upgrading pip ...
python -m pip install --upgrade pip

echo Installing requirements ...
pip install -r requirements.txt

REM ------------------------------------------
REM MLflow / HW03 environment variables
REM ------------------------------------------
set MLFLOW_TRACKING_URI=http://185.50.38.163:33014
set MLFLOW_TRACKING_USERNAME=
set MLFLOW_TRACKING_PASSWORD=
set STUDENT_USERNAME=
set MLFLOW_EXPERIMENT_NAME=qbc12_hw02_sobhan_jabari

REM Selected HW02 final run
set MLFLOW_RUN_ID=78b941ee9925435dbde9df7329d2a7cc

REM ------------------------------------------
REM Show configuration
REM ------------------------------------------
echo.
echo Configuration:
echo MLFLOW_TRACKING_URI=%MLFLOW_TRACKING_URI%
echo MLFLOW_TRACKING_USERNAME=%MLFLOW_TRACKING_USERNAME%
echo STUDENT_USERNAME=%STUDENT_USERNAME%
echo MLFLOW_EXPERIMENT_NAME=%MLFLOW_EXPERIMENT_NAME%
echo MLFLOW_RUN_ID=%MLFLOW_RUN_ID%
echo.

REM ------------------------------------------
REM Run FastAPI app
REM ------------------------------------------
echo Starting FastAPI server...
echo Swagger UI: http://127.0.0.1:8000/docs
echo.

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

endlocal
