import json
import sys
import traceback
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

NOTEBOOK = Path("01_etl_pipeline_student.ipynb")


def is_shell_or_magic(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("!") or stripped.startswith("%")


def transform_source(source_lines: list[str]) -> str:
    """Convert notebook code to executable Python for this simple ETL notebook."""
    kept = []
    for line in source_lines:
        if is_shell_or_magic(line):
            continue
        kept.append(line)
    return "".join(kept)


def display(*args, **kwargs):
    """Small replacement for IPython.display.display when running as a script."""
    for obj in args:
        try:
            print(obj)
        except Exception:
            print(repr(obj))


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    ns = {"__name__": "__main__", "display": display}

    code_cells = [(i, c) for i, c in enumerate(nb["cells"], start=1) if c.get("cell_type") == "code"]
    print(f"Executing {NOTEBOOK} ({len(code_cells)} code cells)\n")

    for exec_no, (cell_index, cell) in enumerate(code_cells, start=1):
        src = transform_source(cell.get("source", []))
        if not src.strip():
            continue

        print(f"\n--- Executing code cell {exec_no} (notebook cell {cell_index}, id={cell.get('id')}) ---")
        try:
            exec(compile(src, f"{NOTEBOOK}:cell-{cell_index}", "exec"), ns)
        except Exception as exc:
            print(f"\nERROR in cell {exec_no} (notebook cell {cell_index}, id={cell.get('id')}): {exc}", file=sys.stderr)
            traceback.print_exc()
            return 1

    print("\nNotebook execution completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())