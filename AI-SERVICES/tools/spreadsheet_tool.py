"""
Spreadsheet and tabular data tools for Sovereign AI Workbench.
Inspect, summarize, query, and write tabular CSV datasets.
"""

import csv
from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool
from tools.file_tool import _resolve_safe_path
from core.logging import logger


class SpreadsheetInspectTool(BaseTool):
    """Inspects a CSV file, computing row counts, columns, types, and numeric stats."""

    name = "inspect_spreadsheet"
    description = (
        "Inspect a CSV spreadsheet to get column names, total row count, inferred column types, "
        "basic summary statistics (min, max, average) for numeric columns, and preview sample rows."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to CSV file inside workspace (e.g. 'telemetry.csv')"
            },
            "sample_rows": {
                "type": "integer",
                "description": "Number of sample rows to preview (default 5)"
            }
        },
        "required": ["file_path"]
    }

    async def arun(self, file_path: str, sample_rows: int = 5, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            if not target.exists():
                return {"success": False, "error": f"CSV file not found: {file_path}"}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames or []
                rows = list(reader)

            total_rows = len(rows)
            preview_count = max(1, min(sample_rows, 20))
            sample = rows[:preview_count]

            col_stats = {}
            for col in columns:
                vals = [r[col].strip() for r in rows if r.get(col) is not None and r[col].strip() != ""]
                numeric_vals = []
                for v in vals:
                    try:
                        numeric_vals.append(float(v))
                    except ValueError:
                        pass

                if len(numeric_vals) == len(vals) and len(numeric_vals) > 0:
                    col_stats[col] = {
                        "type": "numeric",
                        "min": min(numeric_vals),
                        "max": max(numeric_vals),
                        "avg": round(sum(numeric_vals) / len(numeric_vals), 3),
                        "count": len(numeric_vals)
                    }
                else:
                    col_stats[col] = {
                        "type": "text/categorical",
                        "unique_count": len(set(vals)),
                        "count": len(vals)
                    }

            return {
                "success": True,
                "file_path": file_path,
                "total_rows": total_rows,
                "column_count": len(columns),
                "columns": columns,
                "column_analysis": col_stats,
                "sample_preview": sample
            }
        except Exception as e:
            logger.error(f"SpreadsheetInspectTool error on {file_path}: {e}")
            return {"success": False, "error": str(e)}


class SpreadsheetFilterTool(BaseTool):
    """Filters rows from a CSV based on column matching conditions."""

    name = "filter_spreadsheet"
    description = (
        "Filter rows from a CSV file matching a specific column condition "
        "(e.g. column 'status' equals 'FAIL', or numeric 'vibration' greater than 4.5)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to CSV file"
            },
            "column": {
                "type": "string",
                "description": "Column name to filter on"
            },
            "operator": {
                "type": "string",
                "enum": ["==", "!=", ">", "<", ">=", "<=", "contains"],
                "description": "Comparison operator (default '==')"
            },
            "value": {
                "type": "string",
                "description": "Value to compare against"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum matching rows to return (default 20)"
            }
        },
        "required": ["file_path", "column", "value"]
    }

    async def arun(self, file_path: str, column: str, value: str, operator: str = "==", limit: int = 20, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            if not target.exists():
                return {"success": False, "error": f"CSV file not found: {file_path}"}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            matched = []
            max_results = max(1, min(limit, 100))

            for row in rows:
                cell = row.get(column, "")
                is_match = False

                if operator == "contains":
                    is_match = str(value).lower() in str(cell).lower()
                else:
                    try:
                        n_cell = float(cell)
                        n_val = float(value)
                        if operator == "==": is_match = (n_cell == n_val)
                        elif operator == "!=": is_match = (n_cell != n_val)
                        elif operator == ">": is_match = (n_cell > n_val)
                        elif operator == "<": is_match = (n_cell < n_val)
                        elif operator == ">=": is_match = (n_cell >= n_val)
                        elif operator == "<=": is_match = (n_cell <= n_val)
                    except ValueError:
                        if operator == "==": is_match = (str(cell) == str(value))
                        elif operator == "!=": is_match = (str(cell) != str(value))

                if is_match:
                    matched.append(row)
                    if len(matched) >= max_results:
                        break

            return {
                "success": True,
                "file_path": file_path,
                "column": column,
                "operator": operator,
                "filter_value": value,
                "matches_found": len(matched),
                "rows": matched
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class SpreadsheetWriteTool(BaseTool):
    """Creates a new CSV file or appends rows to an existing spreadsheet."""

    name = "write_spreadsheet"
    description = (
        "Create a new CSV spreadsheet with specified columns and rows, or append rows to an existing CSV."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to target CSV file"
            },
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of header column names"
            },
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "description": "Row dictionary mapping column names to values"
                },
                "description": "List of rows to write"
            },
            "append": {
                "type": "boolean",
                "description": "If true, append to existing CSV instead of overwriting"
            }
        },
        "required": ["file_path", "columns", "rows"]
    }

    async def arun(self, file_path: str, columns: List[str], rows: List[Dict[str, Any]], append: bool = False, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            file_exists = target.exists()
            mode = "a" if append and file_exists else "w"

            with open(target, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                if not append or not file_exists:
                    writer.writeheader()
                for r in rows:
                    writer.writerow(r)

            return {
                "success": True,
                "file_path": file_path,
                "rows_written": len(rows),
                "mode": "appended" if append and file_exists else "created"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
