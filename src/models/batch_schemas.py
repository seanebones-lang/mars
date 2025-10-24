"""
Pydantic models for batch processing operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class BatchStatus(str, Enum):
    """Status of batch processing job."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchFileFormat(str, Enum):
    """Supported batch file formats."""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"


class BatchInputRow(BaseModel):
    """Single row in batch input file."""
    agent_output: str = Field(..., description="The agent's response to evaluate")
    ground_truth: Optional[str] = Field(None, description="Expected correct response (optional)")
    query: Optional[str] = Field(None, description="Original user query (optional)")
    agent_id: Optional[str] = Field(None, description="Identifier for the agent (optional)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class BatchResultRow(BaseModel):
    """Single result row from batch processing."""
    row_id: int = Field(..., description="Row number in original file")
    agent_output: str = Field(..., description="Original agent output")
    ground_truth: Optional[str] = Field(None, description="Ground truth if provided")
    query: Optional[str] = Field(None, description="Original query if provided")
    agent_id: Optional[str] = Field(None, description="Agent ID if provided")
    
    # Detection results
    hallucination_risk: float = Field(..., description="Risk score (0-1)")
    flagged: bool = Field(..., description="Whether response was flagged as hallucination")
    confidence: float = Field(..., description="Confidence in the detection")
    uncertainty: float = Field(..., description="Uncertainty in the detection")
    
    # Detailed analysis
    claude_score: Optional[float] = Field(None, description="Claude judge score")
    statistical_score: Optional[float] = Field(None, description="Statistical judge score")
    claude_explanation: Optional[str] = Field(None, description="Claude's explanation")
    flagged_segments: List[str] = Field(default_factory=list, description="Specific problematic segments")
    
    # Processing metadata
    processing_time_ms: float = Field(..., description="Time taken to process this row")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    
    # Original metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Original metadata")


class BatchJob(BaseModel):
    """Batch processing job information."""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_format: BatchFileFormat = Field(..., description="File format")
    status: BatchStatus = Field(..., description="Current job status")
    
    # Progress tracking
    total_rows: int = Field(..., description="Total number of rows to process")
    processed_rows: int = Field(default=0, description="Number of rows processed")
    successful_rows: int = Field(default=0, description="Number of successfully processed rows")
    failed_rows: int = Field(default=0, description="Number of failed rows")
    
    # Timing
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    # Results summary
    average_risk_score: Optional[float] = Field(None, description="Average hallucination risk")
    flagged_percentage: Optional[float] = Field(None, description="Percentage of flagged responses")
    average_processing_time: Optional[float] = Field(None, description="Average processing time per row")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    
    # File paths (internal)
    input_file_path: Optional[str] = Field(None, description="Path to uploaded input file")
    output_file_path: Optional[str] = Field(None, description="Path to generated output file")


class BatchUploadRequest(BaseModel):
    """Request to upload a batch file."""
    filename: str = Field(..., description="Original filename")
    file_format: BatchFileFormat = Field(..., description="File format")
    has_headers: bool = Field(default=True, description="Whether CSV has header row")
    
    # Column mappings for CSV
    agent_output_column: str = Field(default="agent_output", description="Column name for agent output")
    ground_truth_column: Optional[str] = Field(None, description="Column name for ground truth")
    query_column: Optional[str] = Field(None, description="Column name for query")
    agent_id_column: Optional[str] = Field(None, description="Column name for agent ID")


class BatchJobResponse(BaseModel):
    """Response containing batch job information."""
    job: BatchJob
    message: str = Field(..., description="Status message")


class BatchJobListResponse(BaseModel):
    """Response containing list of batch jobs."""
    jobs: List[BatchJob]
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Number of jobs per page")


class BatchProgressUpdate(BaseModel):
    """Real-time progress update for batch job."""
    job_id: str
    status: BatchStatus
    processed_rows: int
    total_rows: int
    progress_percentage: float
    current_row_data: Optional[BatchResultRow] = None
    estimated_time_remaining: Optional[int] = None  # seconds
    error_message: Optional[str] = None


class BatchExportRequest(BaseModel):
    """Request to export batch results."""
    job_id: str = Field(..., description="Job ID to export")
    format: Literal["csv", "json", "xlsx"] = Field(default="csv", description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    include_explanations: bool = Field(default=True, description="Include Claude explanations")
    filter_flagged_only: bool = Field(default=False, description="Export only flagged results")
