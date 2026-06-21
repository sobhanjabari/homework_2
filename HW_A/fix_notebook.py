import json
from pathlib import Path


NOTEBOOK = Path("01_etl_pipeline_student.ipynb")


def lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

# These are incomplete starter/TODO cells or duplicate setup cells that execute before
# the completed solution cells and break a clean top-to-bottom notebook run.
remove_ids = {
    "94f4573f",  # old DB connection using empty PG* defaults
    "f45fd380-e2a3-4ab8-8131-02db0b724437",  # notebook-only pip install cell
    "604bf948-538f-4730-9a88-2ec57e745e34",  # duplicate dotenv import
    "7ed2251f-ec27-44a1-9422-7e45c3cca6de",  # duplicate env debug cell
    "234e4211",  # incomplete cutoff logic
    "ef4b3405",  # incomplete static table SQL
    "b03529d1",  # incomplete cleaning/parser
    "332235c8",  # incomplete static feature join
    "51bd9198",  # incomplete review SQL
    "4b02f64d",  # incomplete calendar SQL
    "eba47eba",  # incomplete target SQL
    "66dab3bb",  # incomplete final join
    "9d1db3b8",  # placeholder drop-unusable-columns cell
}

new_cells = []
for cell in nb["cells"]:
    if cell.get("id") in remove_ids:
        continue
    cell["execution_count"] = None
    cell["outputs"] = [] if cell.get("cell_type") == "code" else cell.get("outputs", [])
    new_cells.append(cell)
nb["cells"] = new_cells

replacements = {
    "b4436293-39cb-4580-ae49-31361c902b2a": r'''# -----------------------------
# Database Connection
# -----------------------------
import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pandas as pd

# Load .env file from the current project folder if present.
load_dotenv(find_dotenv(usecwd=True))

def load_windows_bat_env(path="enviroment.bat"):
    """Load simple `set KEY=value` assignments from the homework batch file."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line.lower().startswith("set ") or "=" not in line:
                continue
            key, value = line[4:].split("=", 1)
            key, value = key.strip(), value.strip()
            if key and value and not os.getenv(key):
                os.environ[key] = value

load_windows_bat_env()

# Support both DB_* names from enviroment.bat/.env and standard PG* names.
DB_HOST = os.getenv("DB_HOST") or os.getenv("PGHOST") or "185.50.38.163"
DB_PORT = int(os.getenv("DB_PORT") or os.getenv("PGPORT") or "32112")
DB_NAME = os.getenv("DB_NAME") or os.getenv("PGDATABASE") or "qbc12_airbnb"
DB_USER = os.getenv("DB_USER") or os.getenv("PGUSER")
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("PGPASSWORD")

if not DB_USER or not DB_PASSWORD:
    raise ValueError(
        "Database credentials are missing. Set DB_USER and DB_PASSWORD in .env, "
        "enviroment.bat, or environment variables before running this notebook."
    )

print("Connecting to:")
print("HOST:", DB_HOST)
print("PORT:", DB_PORT)
print("DB:", DB_NAME)
print("USER:", DB_USER)
print("PASSWORD loaded:", bool(DB_PASSWORD))

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query={"sslmode": "disable"},
)

engine = create_engine(db_url)

def read_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SQL query through SQLAlchemy and return a Pandas DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)

with engine.connect() as conn:
    connection_check = conn.execute(
        text("""
        SELECT
            current_database() AS database,
            current_user AS user_name,
            inet_server_addr() AS server_ip,
            inet_server_port() AS server_port,
            now() AS checked_at;
        """)
    ).mappings().first()

dict(connection_check)
''',
    "5a7ef4b2": r'''duplicate_count = feature_df.duplicated(subset=["listing_id", "cutoff_date"]).sum()
missing_target_count = feature_df["high_demand_proxy"].isna().sum()
unique_target_values = sorted(feature_df["high_demand_proxy"].dropna().unique().tolist())

forbidden_columns = {
    "host_id",
    "host_pseudo_id",
    "reviewer_id",
    "reviewer_pseudo_id",
    "review_id",
    "license",
    "bathrooms_text",
}

present_forbidden_columns = sorted(forbidden_columns.intersection(feature_df.columns))

label_only_columns = [
    "future_calendar_days_observed_30d",
    "future_available_days_30d",
    "future_available_rate_30d",
    "high_demand_proxy",
]

model_input_columns = [
    col for col in feature_df.columns
    if col not in label_only_columns
    and col not in ["listing_id", "cutoff_date", "dataset_version"]
]

future_leakage_columns = [
    col for col in model_input_columns
    if col.startswith("future_")
]

assert duplicate_count == 0, "Duplicate listing_id + cutoff_date rows found."
assert missing_target_count == 0, "Missing target values found."
assert set(unique_target_values).issubset({0, 1}), "Target must be binary 0/1."
assert not present_forbidden_columns, f"Forbidden PII columns present: {present_forbidden_columns}"
assert not future_leakage_columns, f"Future leakage columns in model inputs: {future_leakage_columns}"

print("duplicate_count:", duplicate_count)
print("missing_target_count:", missing_target_count)
print("unique_target_values:", unique_target_values)
print("present_forbidden_columns:", present_forbidden_columns)
print("future_leakage_columns:", future_leakage_columns)
print("model_input_column_count:", len(model_input_columns))
''',
    "6ca93b0b": r'''csv_path = FEATURE_DIR / f"listing_availability_features_{DATASET_VERSION}.csv"
parquet_path = FEATURE_DIR / f"listing_availability_features_{DATASET_VERSION}.parquet"
metadata_path = FEATURE_DIR / f"listing_availability_features_{DATASET_VERSION}_metadata.json"
validation_path = FEATURE_DIR / f"listing_availability_features_{DATASET_VERSION}_validation_report.json"
pii_audit_path = FEATURE_DIR / f"pii_audit_{DATASET_VERSION}.csv"

feature_df.to_csv(csv_path, index=False)
print("Saved CSV:", csv_path)

feature_df.to_parquet(parquet_path, index=False)
print("Saved Parquet:", parquet_path)

metadata = {
    "dataset_version": DATASET_VERSION,
    "entity_column": ENTITY_COLUMN,
    "cutoff_date": str(cutoff_date),
    "history_start_date": str(history_start_date),
    "label_end_date": str(label_end_date),
    "past_window_days": PAST_WINDOW_DAYS,
    "future_window_days": FUTURE_WINDOW_DAYS,
    "high_demand_available_rate_threshold": HIGH_DEMAND_AVAILABLE_RATE_THRESHOLD,
    "source_tables": ["core.listing", "core.host", "core.neighbourhood", "core.review", "core.calendar_day"],
    "target_definition": "high_demand_proxy = 1 if future_available_rate_30d <= threshold, else 0",
    "excluded_pii_columns": sorted([
        "host_id", "host_pseudo_id", "review_id", "reviewer_id",
        "reviewer_pseudo_id", "license", "bathrooms_text",
    ]),
    "row_count": int(len(feature_df)),
    "column_count": int(feature_df.shape[1]),
    "model_input_columns": model_input_columns,
}

with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

validation_report = {
    "duplicate_listing_cutoff_rows": int(duplicate_count),
    "missing_target_count": int(missing_target_count),
    "target_values": [int(v) for v in unique_target_values],
    "present_forbidden_columns": present_forbidden_columns,
    "future_leakage_columns_in_model_inputs": future_leakage_columns,
    "missing_report": missing_report.to_dict(orient="records"),
    "label_distribution": label_distribution.to_dict(orient="records"),
    "calendar_coverage_summary": calendar_coverage_summary.to_dict(orient="records"),
}

with open(validation_path, "w", encoding="utf-8") as f:
    json.dump(validation_report, f, indent=2, ensure_ascii=False)

pii_audit.to_csv(pii_audit_path, index=False)

print("Saved metadata:", metadata_path)
print("Saved validation report:", validation_path)
print("Saved PII audit:", pii_audit_path)
''',
}

for cell in nb["cells"]:
    cell_id = cell.get("id")
    if cell_id in replacements:
        cell["source"] = lines(replacements[cell_id])

NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Patched {NOTEBOOK}: removed {len(remove_ids)} incomplete/duplicate cells and updated runtime cells.")