"""Profiling endpoints."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import ORJSONResponse

from data_profiler.core.profiler import DataProfiler
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import DataProfile

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/profile/upload", response_model=DataProfile)
async def profile_upload(
    file: UploadFile = File(..., description="CSV, Parquet, or JSON file to profile"),
    sample_size: Optional[int] = None,
    compute_correlations: bool = True,
    compute_percentiles: bool = True,
    detect_outliers: bool = True,
    detect_patterns: bool = True,
    parallel: bool = True,
) -> DataProfile:
    """
    Profile an uploaded file.

    Accepts CSV, Parquet, or JSON files and returns comprehensive profiling results.

    Args:
        file: Uploaded file
        sample_size: Optional sample size for large datasets
        compute_correlations: Compute correlation matrix
        compute_percentiles: Compute percentile statistics
        detect_outliers: Detect outliers in numeric columns
        detect_patterns: Detect patterns in text columns
        parallel: Enable parallel processing

    Returns:
        DataProfile with complete profiling results
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = {".csv", ".parquet", ".json"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}",
        )

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_ext
        ) as tmp_file:
            tmp_path = tmp_file.name
            content = await file.read()
            tmp_file.write(content)

        # Create config
        config = ProfileConfig(
            sample_size=sample_size,
            compute_correlations=compute_correlations,
            compute_percentiles=compute_percentiles,
            detect_outliers=detect_outliers,
            detect_patterns=detect_patterns,
            parallel=parallel,
        )

        # Profile in thread pool to avoid blocking
        profiler = DataProfiler(config=config)

        # Run CPU-intensive profiling in executor
        loop = asyncio.get_event_loop()
        profile_result = await loop.run_in_executor(
            None, profiler.profile, tmp_path
        )

        logger.info(
            "Profiled file '%s' (%d rows, %d columns) in %.2fs",
            file.filename,
            profile_result.row_count,
            profile_result.column_count,
            profile_result.profiling_duration_seconds,
        )

        return profile_result

    except Exception as e:
        logger.error("Error profiling file: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error profiling file: {str(e)}")

    finally:
        # Clean up temporary file
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass


@router.post("/profile/url")
async def profile_url(
    url: str,
    sample_size: Optional[int] = None,
    compute_correlations: bool = True,
    compute_percentiles: bool = True,
    detect_outliers: bool = True,
    detect_patterns: bool = True,
    parallel: bool = True,
) -> DataProfile:
    """
    Profile a dataset from a URL.

    Args:
        url: URL to CSV, Parquet, or JSON file
        sample_size: Optional sample size for large datasets
        compute_correlations: Compute correlation matrix
        compute_percentiles: Compute percentile statistics
        detect_outliers: Detect outliers in numeric columns
        detect_patterns: Detect patterns in text columns
        parallel: Enable parallel processing

    Returns:
        DataProfile with complete profiling results
    """
    try:
        # Create config
        config = ProfileConfig(
            sample_size=sample_size,
            compute_correlations=compute_correlations,
            compute_percentiles=compute_percentiles,
            detect_outliers=detect_outliers,
            detect_patterns=detect_patterns,
            parallel=parallel,
        )

        # Profile in thread pool
        profiler = DataProfiler(config=config)
        loop = asyncio.get_event_loop()
        profile_result = await loop.run_in_executor(None, profiler.profile, url)

        logger.info(
            "Profiled URL '%s' (%d rows, %d columns) in %.2fs",
            url,
            profile_result.row_count,
            profile_result.column_count,
            profile_result.profiling_duration_seconds,
        )

        return profile_result

    except Exception as e:
        logger.error("Error profiling URL: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error profiling URL: {str(e)}")
