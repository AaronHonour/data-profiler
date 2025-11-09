"""Schema inference for database creation."""

from typing import Any, Dict, List

import pandas as pd

from data_profiler.models.profile import ColumnProfile, ColumnType, SchemaInference


class SchemaInferenceEngine:
    """Infer database schema from profiled data."""

    # Map column types to SQL types
    TYPE_MAPPING = {
        ColumnType.NUMERIC: {
            "has_decimals": "DECIMAL",
            "small_int": "SMALLINT",
            "int": "INTEGER",
            "big_int": "BIGINT",
            "default": "NUMERIC",
        },
        ColumnType.TEXT: {
            "short": "VARCHAR(255)",
            "medium": "VARCHAR(1000)",
            "long": "TEXT",
        },
        ColumnType.BOOLEAN: "BOOLEAN",
        ColumnType.DATETIME: "TIMESTAMP",
        ColumnType.CATEGORICAL: "VARCHAR(255)",
    }

    @classmethod
    def infer_schema(cls, column_profiles: List[ColumnProfile], row_count: int) -> SchemaInference:
        """
        Infer database schema from column profiles.

        Args:
            column_profiles: List of column profiles
            row_count: Total number of rows

        Returns:
            SchemaInference object with DDL recommendations
        """
        columns = []
        primary_key_candidates = []
        indexes_recommended = []

        for profile in column_profiles:
            col_def = cls._infer_column_definition(profile, row_count)
            columns.append(col_def)

            # Primary key candidates (unique, non-null)
            if profile.quality.uniqueness == 100.0 and profile.quality.completeness == 100.0:
                primary_key_candidates.append(profile.name)

            # Index recommendations (high cardinality, frequently used for filtering)
            if profile.quality.uniqueness > 50.0 and profile.quality.completeness > 90.0:
                indexes_recommended.append(profile.name)

        return SchemaInference(
            columns=columns,
            primary_key_candidates=primary_key_candidates,
            indexes_recommended=indexes_recommended,
        )

    @classmethod
    def _infer_column_definition(cls, profile: ColumnProfile, row_count: int) -> Dict[str, Any]:
        """
        Infer column definition for a single column.

        Args:
            profile: Column profile
            row_count: Total row count

        Returns:
            Dictionary with column definition
        """
        # Determine SQL type
        sql_type = cls._map_to_sql_type(profile)

        # Determine nullability
        nullable = profile.quality.completeness < 100.0

        # Determine uniqueness constraint
        unique = profile.quality.uniqueness == 100.0

        return {
            "name": profile.name,
            "type": sql_type,
            "nullable": nullable,
            "unique": unique,
            "inferred_from": profile.type.value,
        }

    @classmethod
    def _map_to_sql_type(cls, profile: ColumnProfile) -> str:
        """
        Map profile column type to SQL type.

        Args:
            profile: Column profile

        Returns:
            SQL type string
        """
        if profile.type == ColumnType.NUMERIC:
            if profile.numeric_stats:
                # Check if it has decimals
                has_decimals = (
                    profile.numeric_stats.std is not None and profile.numeric_stats.std % 1 != 0
                )

                if has_decimals:
                    return "DECIMAL"

                # Check range for integer types
                if profile.numeric_stats.min is not None and profile.numeric_stats.max is not None:
                    min_val = profile.numeric_stats.min
                    max_val = profile.numeric_stats.max

                    if min_val >= -32768 and max_val <= 32767:
                        return "SMALLINT"
                    elif min_val >= -2147483648 and max_val <= 2147483647:
                        return "INTEGER"
                    else:
                        return "BIGINT"

            return "NUMERIC"

        elif profile.type == ColumnType.TEXT:
            if profile.text_stats:
                max_len = profile.text_stats.max_length or 0

                if max_len <= 255:
                    return f"VARCHAR({max_len})" if max_len > 0 else "VARCHAR(255)"
                elif max_len <= 1000:
                    return "VARCHAR(1000)"
                else:
                    return "TEXT"

            return "VARCHAR(255)"

        elif profile.type == ColumnType.BOOLEAN:
            return "BOOLEAN"

        elif profile.type == ColumnType.DATETIME:
            return "TIMESTAMP"

        elif profile.type == ColumnType.CATEGORICAL:
            # Use ENUM for low cardinality, VARCHAR otherwise
            if profile.categorical_stats and profile.categorical_stats.unique_count <= 10:
                return f"VARCHAR(255)"  # Could use ENUM in some databases
            return "VARCHAR(255)"

        else:
            return "VARCHAR(255)"

    @classmethod
    def generate_ddl(cls, schema: SchemaInference, table_name: str = "data_table") -> str:
        """
        Generate SQL DDL from schema inference.

        Args:
            schema: Inferred schema
            table_name: Name for the table

        Returns:
            SQL CREATE TABLE statement
        """
        lines = [f"CREATE TABLE {table_name} ("]

        # Add column definitions
        col_defs = []
        for col in schema.columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            unique = "UNIQUE" if col.get("unique", False) else ""
            col_def = f"    {col['name']} {col['type']} {nullable} {unique}".strip()
            col_defs.append(col_def)

        # Add primary key if exists
        if schema.primary_key_candidates:
            pk_col = schema.primary_key_candidates[0]  # Use first candidate
            col_defs.append(f"    PRIMARY KEY ({pk_col})")

        lines.append(",\n".join(col_defs))
        lines.append(");")

        # Add index recommendations
        index_statements = []
        for idx_col in schema.indexes_recommended:
            if idx_col not in schema.primary_key_candidates:  # Don't index PK
                index_statements.append(
                    f"CREATE INDEX idx_{table_name}_{idx_col} ON {table_name}({idx_col});"
                )

        ddl = "\n".join(lines)
        if index_statements:
            ddl += "\n\n-- Recommended indexes\n" + "\n".join(index_statements)

        return ddl
