"""Data lineage tracking for data transformations and dependencies."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, Enum):
    """Type of data operation."""

    SOURCE = "source"  # Data source (file, database, API)
    TRANSFORM = "transform"  # Transformation (filter, aggregate, join)
    PROFILE = "profile"  # Profiling operation
    EXPORT = "export"  # Export to file/database
    VALIDATION = "validation"  # Data validation
    CLEANING = "cleaning"  # Data cleaning


class DataSource(BaseModel):
    """Data source information."""

    source_id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: str = Field(description="Type: file, database, api, dataframe")
    location: str = Field(description="File path, URL, or connection string")
    format: Optional[str] = Field(None, description="Data format (csv, parquet, json, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class DataOperation(BaseModel):
    """Record of a data operation."""

    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    operation_type: OperationType
    name: str = Field(description="Operation name/description")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    input_ids: List[str] = Field(default_factory=list, description="Input dataset IDs")
    output_id: str = Field(description="Output dataset ID")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Operation parameters"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Operation metrics (rows affected, duration, etc.)"
    )

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class DatasetNode(BaseModel):
    """Node representing a dataset in the lineage graph."""

    dataset_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(description="Dataset name")
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    source: Optional[DataSource] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list, description="Custom tags")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class LineageGraph(BaseModel):
    """Complete lineage graph with datasets and operations."""

    datasets: Dict[str, DatasetNode] = Field(default_factory=dict)
    operations: List[DataOperation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class LineageTracker:
    """Track data lineage across operations."""

    def __init__(self):
        """Initialize lineage tracker."""
        self.graph = LineageGraph()
        self._active_dataset: Optional[str] = None

    def register_source(
        self,
        name: str,
        source_type: str,
        location: str,
        format: Optional[str] = None,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a data source.

        Args:
            name: Dataset name
            source_type: Type of source (file, database, api, dataframe)
            location: Source location
            format: Data format
            row_count: Number of rows
            column_count: Number of columns
            metadata: Additional metadata

        Returns:
            Dataset ID
        """
        # Create source
        source = DataSource(
            source_type=source_type,
            location=location,
            format=format,
            metadata=metadata or {},
        )

        # Create dataset node
        dataset = DatasetNode(
            name=name,
            source=source,
            row_count=row_count,
            column_count=column_count,
            metadata=metadata or {},
        )

        # Add to graph
        self.graph.datasets[dataset.dataset_id] = dataset
        self._active_dataset = dataset.dataset_id

        # Record operation
        operation = DataOperation(
            operation_type=OperationType.SOURCE,
            name=f"Load from {source_type}",
            output_id=dataset.dataset_id,
            parameters={
                "source_type": source_type,
                "location": location,
                "format": format,
            },
            metrics={
                "row_count": row_count,
                "column_count": column_count,
            },
        )
        self.graph.operations.append(operation)

        return dataset.dataset_id

    def register_transformation(
        self,
        name: str,
        input_ids: List[str],
        output_name: str,
        operation_type: OperationType = OperationType.TRANSFORM,
        parameters: Optional[Dict[str, Any]] = None,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a data transformation.

        Args:
            name: Transformation name
            input_ids: Input dataset IDs
            output_name: Output dataset name
            operation_type: Type of operation
            parameters: Transformation parameters
            row_count: Output row count
            column_count: Output column count
            metrics: Operation metrics

        Returns:
            Output dataset ID
        """
        # Create output dataset
        output_dataset = DatasetNode(
            name=output_name,
            row_count=row_count,
            column_count=column_count,
        )

        # Add to graph
        self.graph.datasets[output_dataset.dataset_id] = output_dataset
        self._active_dataset = output_dataset.dataset_id

        # Record operation
        operation = DataOperation(
            operation_type=operation_type,
            name=name,
            input_ids=input_ids,
            output_id=output_dataset.dataset_id,
            parameters=parameters or {},
            metrics=metrics or {},
        )
        self.graph.operations.append(operation)

        return output_dataset.dataset_id

    def register_profile(
        self,
        dataset_id: str,
        profile_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a profiling operation.

        Args:
            dataset_id: Dataset being profiled
            profile_results: Profiling results summary

        Returns:
            Operation ID
        """
        operation = DataOperation(
            operation_type=OperationType.PROFILE,
            name="Profile dataset",
            input_ids=[dataset_id],
            output_id=dataset_id,
            metrics=profile_results or {},
        )
        self.graph.operations.append(operation)

        return operation.operation_id

    def get_upstream_datasets(self, dataset_id: str) -> List[DatasetNode]:
        """
        Get all upstream datasets (ancestors) for a given dataset.

        Args:
            dataset_id: Target dataset ID

        Returns:
            List of upstream datasets
        """
        upstream_ids = self._get_upstream_ids(dataset_id)
        return [self.graph.datasets[did] for did in upstream_ids if did in self.graph.datasets]

    def get_downstream_datasets(self, dataset_id: str) -> List[DatasetNode]:
        """
        Get all downstream datasets (descendants) for a given dataset.

        Args:
            dataset_id: Target dataset ID

        Returns:
            List of downstream datasets
        """
        downstream_ids = self._get_downstream_ids(dataset_id)
        return [self.graph.datasets[did] for did in downstream_ids if did in self.graph.datasets]

    def _get_upstream_ids(self, dataset_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Recursively get upstream dataset IDs."""
        if visited is None:
            visited = set()

        if dataset_id in visited:
            return visited

        visited.add(dataset_id)

        # Find operations that produce this dataset
        for operation in self.graph.operations:
            if operation.output_id == dataset_id:
                # Add input datasets
                for input_id in operation.input_ids:
                    self._get_upstream_ids(input_id, visited)

        return visited

    def _get_downstream_ids(self, dataset_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Recursively get downstream dataset IDs."""
        if visited is None:
            visited = set()

        if dataset_id in visited:
            return visited

        visited.add(dataset_id)

        # Find operations that use this dataset as input
        for operation in self.graph.operations:
            if dataset_id in operation.input_ids:
                # Add output dataset
                self._get_downstream_ids(operation.output_id, visited)

        return visited

    def get_lineage_summary(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get lineage summary for a dataset.

        Args:
            dataset_id: Target dataset ID

        Returns:
            Summary dictionary
        """
        if dataset_id not in self.graph.datasets:
            return {"error": "Dataset not found"}

        dataset = self.graph.datasets[dataset_id]
        upstream = self.get_upstream_datasets(dataset_id)
        downstream = self.get_downstream_datasets(dataset_id)

        # Get operations involving this dataset
        operations = [
            op
            for op in self.graph.operations
            if dataset_id in op.input_ids or op.output_id == dataset_id
        ]

        return {
            "dataset": {
                "id": dataset.dataset_id,
                "name": dataset.name,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "created_at": dataset.created_at,
            },
            "upstream_count": len(upstream) - 1,  # Exclude self
            "downstream_count": len(downstream) - 1,  # Exclude self
            "operations_count": len(operations),
            "source": dataset.source.dict() if dataset.source else None,
        }

    def generate_lineage_diagram(self, dataset_id: Optional[str] = None) -> str:
        """
        Generate ASCII lineage diagram.

        Args:
            dataset_id: Optional dataset ID to focus on (shows full graph if None)

        Returns:
            ASCII diagram
        """
        lines = []
        lines.append("=" * 70)
        lines.append("DATA LINEAGE DIAGRAM")
        lines.append("=" * 70)

        if dataset_id:
            # Focus on specific dataset
            if dataset_id not in self.graph.datasets:
                return "Dataset not found"

            dataset = self.graph.datasets[dataset_id]
            lines.append(f"\nFocused on: {dataset.name} ({dataset.dataset_id[:8]}...)")

            # Get upstream
            upstream = self.get_upstream_datasets(dataset_id)
            if len(upstream) > 1:
                lines.append(f"\n{'UPSTREAM DATASETS':-^70}")
                for ds in upstream:
                    if ds.dataset_id != dataset_id:
                        lines.append(f"  ↑ {ds.name} ({ds.dataset_id[:8]}...)")

            # Show current
            lines.append(f"\n{'CURRENT DATASET':-^70}")
            lines.append(f"  • {dataset.name}")
            lines.append(f"    ID: {dataset.dataset_id}")
            if dataset.row_count:
                lines.append(f"    Rows: {dataset.row_count:,}")
            if dataset.column_count:
                lines.append(f"    Columns: {dataset.column_count}")

            # Get downstream
            downstream = self.get_downstream_datasets(dataset_id)
            if len(downstream) > 1:
                lines.append(f"\n{'DOWNSTREAM DATASETS':-^70}")
                for ds in downstream:
                    if ds.dataset_id != dataset_id:
                        lines.append(f"  ↓ {ds.name} ({ds.dataset_id[:8]}...)")

        else:
            # Show full graph
            lines.append(f"\nTotal Datasets: {len(self.graph.datasets)}")
            lines.append(f"Total Operations: {len(self.graph.operations)}")

            lines.append(f"\n{'DATASETS':-^70}")
            for dataset in self.graph.datasets.values():
                source_info = f" [from {dataset.source.source_type}]" if dataset.source else ""
                lines.append(f"  • {dataset.name}{source_info}")
                lines.append(f"    ID: {dataset.dataset_id}")

            if self.graph.operations:
                lines.append(f"\n{'OPERATIONS':-^70}")
                for i, op in enumerate(self.graph.operations, 1):
                    lines.append(f"\n{i}. {op.name} ({op.operation_type.value})")
                    if op.input_ids:
                        input_names = [
                            self.graph.datasets[did].name
                            for did in op.input_ids
                            if did in self.graph.datasets
                        ]
                        lines.append(f"   Inputs: {', '.join(input_names)}")
                    output_name = self.graph.datasets[op.output_id].name
                    lines.append(f"   Output: {output_name}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def export_lineage(self) -> Dict[str, Any]:
        """
        Export complete lineage graph as dictionary.

        Returns:
            Lineage graph dictionary
        """
        return self.graph.dict()

    def import_lineage(self, lineage_data: Dict[str, Any]) -> None:
        """
        Import lineage graph from dictionary.

        Args:
            lineage_data: Lineage graph dictionary
        """
        self.graph = LineageGraph(**lineage_data)
