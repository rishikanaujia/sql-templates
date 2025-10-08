"""
Config-Driven SQL Metadata Extractor
------------------------------------
✅ Removes all hardcoding (template, joins, columns)
✅ Template loaded externally for flexibility
✅ Easily reused across schema types or environments
"""

import pandas as pd
from typing import Callable, List, Optional


# ----------------------------------------------------------------------
# 🔹 External Default SQL Template
# ----------------------------------------------------------------------
DEFAULT_SQL_TEMPLATE = """
SELECT DISTINCT
    '{table_name}' AS source_table,
    {select_columns}
FROM {table_name} AS ta
JOIN {join_table} AS jt
    ON ta.{join_key_local} = jt.{join_key_remote}
"""

ID_COLUMN=""
NAME_COLUMN=""
# ----------------------------------------------------------------------
# 🔹 Configurable, Optimized Metadata Extractor
# ----------------------------------------------------------------------
class SQLMetadataExtractor:
    """
    Generic SQL Metadata Extractor
    ------------------------------
    Generates and executes combined SQL queries to retrieve
    metadata relationships between tables and a lookup table.
    """

    def __init__(
        self,
        tables: List[str],
        run_query_fn: Callable[[str], pd.DataFrame],
        join_table: str,
        join_key_local: str,
        join_key_remote: str,
        select_columns: Optional[List[str]] = None,
        sql_template: Optional[str] = None,
    ):
        """
        Args:
            tables: List of source table names
            run_query_fn: Function that executes SQL and returns a DataFrame
            join_table: The lookup/join table name
            join_key_local: Column name in source tables (foreign key)
            join_key_remote: Column name in join table (primary key)
            select_columns: Columns to fetch from join table
            sql_template: Custom SQL template (defaults to global DEFAULT_SQL_TEMPLATE)
        """
        self.tables = tables
        self.run_query_fn = run_query_fn
        self.join_table = join_table
        self.join_key_local = join_key_local
        self.join_key_remote = join_key_remote
        self.select_columns = select_columns or ["*"]
        self.sql_template = sql_template or DEFAULT_SQL_TEMPLATE

    # ------------------------------------------------------------------
    def generate_combined_query(self) -> str:
        """Generate one combined SQL query using the template."""
        column_str = ", ".join(f"jt.{col}" for col in self.select_columns)
        parts = [
            self.sql_template.format(
                table_name=tbl,
                select_columns=column_str,
                join_table=self.join_table,
                join_key_local=self.join_key_local,
                join_key_remote=self.join_key_remote,
            )
            for tbl in self.tables
        ]
        return "\nUNION ALL\n".join(parts)

    # ------------------------------------------------------------------
    def fetch_all_metadata(self) -> pd.DataFrame:
        """Execute the combined SQL query."""
        query = self.generate_combined_query()
        return self.run_query_fn(query)

    # ------------------------------------------------------------------
    def format_output(self, df: pd.DataFrame) -> str:
        """Format combined results into compact readable text."""
        if df.empty:
            return "⚠️ No data found."

        output = []
        for table, group in df.groupby("source_table"):
            lines = [f"{table}:"]
            # Handle standard id/name schema
            if {ID_COLUMN, NAME_COLUMN}.issubset(group.columns):
                lines.extend(
                    group.apply(
                        lambda r: f"{r[ID_COLUMN]}: {r[NAME_COLUMN]}", axis=1
                    )
                )
            else:
                # Generic fallback for other schemas
                for _, row in group.iterrows():
                    kv_pairs = ", ".join(
                        f"{col}={row[col]}"
                        for col in group.columns
                        if col not in {"source_table"}
                    )
                    lines.append(kv_pairs)
            output.append("\n".join(lines))

        return "\n\n".join(output)

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Execute extractor and print formatted metadata."""
        df = self.fetch_all_metadata()
        formatted = self.format_output(df)
        print(formatted)
