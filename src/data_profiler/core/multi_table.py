"""Multi-table analysis for relational data."""

from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
from pydantic import BaseModel, Field

from data_profiler.core.profiler import DataProfiler
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import DataProfile


class ForeignKeyCandidate(BaseModel):
    """Potential foreign key relationship."""

    source_table: str
    source_column: str
    target_table: str
    target_column: str
    match_percentage: float = Field(description="Percentage of source values found in target")
    confidence_score: float = Field(description="Confidence in FK relationship (0-1)")
    relationship_type: str = Field(description="one-to-one, one-to-many, many-to-many")
    is_valid: bool = Field(description="Whether this is a valid FK")


class TableRelationship(BaseModel):
    """Relationship between two tables."""

    table1: str
    table2: str
    foreign_keys: List[ForeignKeyCandidate] = Field(default_factory=list)
    relationship_strength: float = Field(description="Overall relationship strength (0-1)")


class DatasetSchema(BaseModel):
    """Schema for multiple related tables."""

    tables: List[str]
    relationships: List[TableRelationship]
    primary_keys: Dict[str, List[str]] = Field(
        default_factory=dict, description="Primary key candidates per table"
    )
    foreign_keys: List[ForeignKeyCandidate] = Field(
        default_factory=list, description="All detected foreign keys"
    )


class MultiTableAnalyzer:
    """Analyze relationships between multiple tables."""

    def __init__(self, config: Optional[ProfileConfig] = None):
        """
        Initialize multi-table analyzer.

        Args:
            config: Profiling configuration
        """
        self.config = config or ProfileConfig()
        self.profiler = DataProfiler(config=self.config)

    def analyze_relationships(
        self,
        tables: Dict[str, pd.DataFrame],
        min_confidence: float = 0.7,
    ) -> DatasetSchema:
        """
        Analyze relationships between multiple tables.

        Args:
            tables: Dictionary mapping table names to DataFrames
            min_confidence: Minimum confidence score for FK detection

        Returns:
            DatasetSchema with detected relationships
        """
        # Profile all tables
        profiles = {name: self.profiler.profile(df) for name, df in tables.items()}

        # Detect primary keys
        primary_keys = self._detect_primary_keys(profiles)

        # Detect foreign key relationships
        foreign_keys = []
        for source_name, source_df in tables.items():
            for target_name, target_df in tables.items():
                if source_name == target_name:
                    continue

                fks = self._detect_foreign_keys(
                    source_name, source_df,
                    target_name, target_df,
                    min_confidence
                )
                foreign_keys.extend(fks)

        # Group foreign keys into relationships
        relationships = self._group_relationships(foreign_keys)

        return DatasetSchema(
            tables=list(tables.keys()),
            relationships=relationships,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
        )

    def _detect_primary_keys(self, profiles: Dict[str, DataProfile]) -> Dict[str, List[str]]:
        """Detect primary key candidates in each table."""
        primary_keys = {}

        for table_name, profile in profiles.items():
            candidates = []
            for col in profile.columns:
                # Primary key: unique and complete
                if col.quality.uniqueness == 100.0 and col.quality.completeness == 100.0:
                    candidates.append(col.name)

            primary_keys[table_name] = candidates

        return primary_keys

    def _detect_foreign_keys(
        self,
        source_name: str,
        source_df: pd.DataFrame,
        target_name: str,
        target_df: pd.DataFrame,
        min_confidence: float,
    ) -> List[ForeignKeyCandidate]:
        """
        Detect foreign key relationships between two tables.

        Args:
            source_name: Source table name
            source_df: Source DataFrame
            target_name: Target table name
            target_df: Target DataFrame
            min_confidence: Minimum confidence threshold

        Returns:
            List of foreign key candidates
        """
        candidates = []

        # Get common column names (potential FK candidates)
        common_cols = set(source_df.columns) & set(target_df.columns)

        # Also check for naming patterns (e.g., user_id in orders -> id in users)
        potential_fks = self._find_potential_fk_pairs(source_df.columns, target_df.columns, target_name)

        all_pairs = set((col, col) for col in common_cols) | potential_fks

        for source_col, target_col in all_pairs:
            if source_col not in source_df.columns or target_col not in target_df.columns:
                continue

            # Analyze the relationship
            match_pct, rel_type = self._analyze_column_relationship(
                source_df[source_col],
                target_df[target_col]
            )

            # Calculate confidence score
            confidence = self._calculate_confidence(
                match_pct, rel_type, source_col, target_col, target_name
            )

            if confidence >= min_confidence:
                candidates.append(ForeignKeyCandidate(
                    source_table=source_name,
                    source_column=source_col,
                    target_table=target_name,
                    target_column=target_col,
                    match_percentage=match_pct,
                    confidence_score=confidence,
                    relationship_type=rel_type,
                    is_valid=match_pct >= 90.0,  # 90%+ match for valid FK
                ))

        return candidates

    def _find_potential_fk_pairs(
        self, source_cols: pd.Index, target_cols: pd.Index, target_table: str
    ) -> Set[Tuple[str, str]]:
        """
        Find potential FK column pairs based on naming conventions.

        E.g., 'user_id' in source might reference 'id' in 'users' table.
        """
        pairs = set()

        for source_col in source_cols:
            source_lower = source_col.lower()

            # Pattern 1: {table_name}_id -> id
            if source_lower == f"{target_table.lower()}_id":
                if "id" in target_cols:
                    pairs.add((source_col, "id"))

            # Pattern 2: {table_name}_{col} -> {col}
            if source_lower.startswith(f"{target_table.lower()}_"):
                suffix = source_col[len(target_table) + 1:]
                if suffix in target_cols:
                    pairs.add((source_col, suffix))

            # Pattern 3: FK_{table_name}_{col} -> {col}
            if source_lower.startswith("fk_"):
                parts = source_col.split("_")
                if len(parts) >= 3 and parts[1].lower() == target_table.lower():
                    target_col_candidate = "_".join(parts[2:])
                    if target_col_candidate in target_cols:
                        pairs.add((source_col, target_col_candidate))

        return pairs

    def _analyze_column_relationship(
        self, source_series: pd.Series, target_series: pd.Series
    ) -> Tuple[float, str]:
        """
        Analyze the relationship between two columns.

        Returns:
            Tuple of (match_percentage, relationship_type)
        """
        # Drop nulls
        source_clean = source_series.dropna()
        target_clean = target_series.dropna()

        if len(source_clean) == 0 or len(target_clean) == 0:
            return 0.0, "unknown"

        # Get unique values
        source_unique = set(source_clean.unique())
        target_unique = set(target_clean.unique())

        # Calculate match percentage
        matches = source_unique & target_unique
        match_pct = (len(matches) / len(source_unique)) * 100 if source_unique else 0.0

        # Determine relationship type
        source_value_counts = source_clean.value_counts()
        target_value_counts = target_clean.value_counts()

        source_has_duplicates = (source_value_counts > 1).any()
        target_has_duplicates = (target_value_counts > 1).any()

        if not source_has_duplicates and not target_has_duplicates:
            rel_type = "one-to-one"
        elif not source_has_duplicates and target_has_duplicates:
            rel_type = "one-to-many"
        elif source_has_duplicates and target_has_duplicates:
            rel_type = "many-to-many"
        else:
            rel_type = "many-to-one"

        return match_pct, rel_type

    def _calculate_confidence(
        self,
        match_pct: float,
        rel_type: str,
        source_col: str,
        target_col: str,
        target_table: str,
    ) -> float:
        """Calculate confidence score for FK relationship."""
        confidence = 0.0

        # Base confidence from match percentage
        confidence += (match_pct / 100) * 0.6

        # Relationship type bonus
        if rel_type in ["one-to-one", "many-to-one"]:
            confidence += 0.2
        elif rel_type == "one-to-many":
            confidence += 0.1

        # Naming convention bonus
        source_lower = source_col.lower()
        target_lower = target_col.lower()

        if source_lower == f"{target_table.lower()}_id" and target_lower == "id":
            confidence += 0.2
        elif source_lower == target_lower:
            confidence += 0.1
        elif source_lower.endswith("_id") and target_lower == "id":
            confidence += 0.1

        return min(confidence, 1.0)

    def _group_relationships(
        self, foreign_keys: List[ForeignKeyCandidate]
    ) -> List[TableRelationship]:
        """Group foreign keys into table relationships."""
        relationships_dict: Dict[Tuple[str, str], List[ForeignKeyCandidate]] = {}

        for fk in foreign_keys:
            # Create normalized table pair (alphabetically sorted)
            table_pair = tuple(sorted([fk.source_table, fk.target_table]))

            if table_pair not in relationships_dict:
                relationships_dict[table_pair] = []

            relationships_dict[table_pair].append(fk)

        # Convert to TableRelationship objects
        relationships = []
        for (table1, table2), fks in relationships_dict.items():
            # Calculate overall relationship strength
            if fks:
                strength = sum(fk.confidence_score for fk in fks) / len(fks)
            else:
                strength = 0.0

            relationships.append(TableRelationship(
                table1=table1,
                table2=table2,
                foreign_keys=fks,
                relationship_strength=strength,
            ))

        return relationships

    @staticmethod
    def generate_relationship_diagram(schema: DatasetSchema) -> str:
        """
        Generate a text-based relationship diagram.

        Args:
            schema: Dataset schema with relationships

        Returns:
            ASCII diagram of table relationships
        """
        lines = []
        lines.append("=" * 70)
        lines.append("TABLE RELATIONSHIP DIAGRAM")
        lines.append("=" * 70)

        lines.append(f"\nTables: {len(schema.tables)}")
        lines.append(f"Relationships: {len(schema.relationships)}")
        lines.append(f"Foreign Keys: {len(schema.foreign_keys)}")

        # Primary keys
        lines.append(f"\n{'PRIMARY KEY CANDIDATES':-^70}")
        for table, pk_candidates in schema.primary_keys.items():
            if pk_candidates:
                lines.append(f"{table}:")
                for pk in pk_candidates:
                    lines.append(f"  🔑 {pk}")

        # Relationships
        if schema.relationships:
            lines.append(f"\n{'RELATIONSHIPS':-^70}")
            for rel in schema.relationships:
                lines.append(f"\n{rel.table1} ↔ {rel.table2}")
                lines.append(f"Strength: {rel.relationship_strength:.2f}")

                for fk in rel.foreign_keys:
                    arrow = "→" if fk.source_table == rel.table1 else "←"
                    valid_icon = "✓" if fk.is_valid else "?"
                    lines.append(
                        f"  {valid_icon} {fk.source_table}.{fk.source_column} {arrow} "
                        f"{fk.target_table}.{fk.target_column} "
                        f"({fk.relationship_type}, {fk.match_percentage:.1f}% match)"
                    )

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
