import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface BatchJob {
  job_id: string;
  filename: string;
  file_format: 'csv' | 'json' | 'jsonl';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  total_rows: number;
  processed_rows: number;
  successful_rows: number;
  failed_rows: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  average_risk_score?: number;
  flagged_percentage?: number;
  average_processing_time?: number;
  error_message?: string;
}

export interface BatchJobResponse {
  job: BatchJob;
  message: string;
}

export interface BatchJobListResponse {
  jobs: BatchJob[];
  total: number;
  page: number;
  page_size: number;
}

export interface BatchProgressUpdate {
  job_id: string;
  status: string;
  processed_rows: number;
  total_rows: number;
  progress_percentage: number;
  current_row_data?: any;
  estimated_time_remaining?: number;
  error_message?: string;
}

export interface BatchUploadOptions {
  has_headers?: boolean;
  agent_output_column?: string;
  ground_truth_column?: string;
  query_column?: string;
  agent_id_column?: string;
}

export interface BatchExportOptions {
  format: 'csv' | 'json' | 'xlsx';
  include_metadata?: boolean;
  include_explanations?: boolean;
  filter_flagged_only?: boolean;
}

class BatchAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async uploadFile(file: File, options: BatchUploadOptions = {}): Promise<BatchJobResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.has_headers !== undefined) {
      formData.append('has_headers', options.has_headers.toString());
    }
    if (options.agent_output_column) {
      formData.append('agent_output_column', options.agent_output_column);
    }
    if (options.ground_truth_column) {
      formData.append('ground_truth_column', options.ground_truth_column);
    }
    if (options.query_column) {
      formData.append('query_column', options.query_column);
    }
    if (options.agent_id_column) {
      formData.append('agent_id_column', options.agent_id_column);
    }

    const response = await axios.post(`${this.baseURL}/batch/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async startProcessing(jobId: string): Promise<BatchJobResponse> {
    const response = await axios.post(`${this.baseURL}/batch/${jobId}/start`);
    return response.data;
  }

  async getJob(jobId: string): Promise<BatchJobResponse> {
    const response = await axios.get(`${this.baseURL}/batch/${jobId}`);
    return response.data;
  }

  async listJobs(page: number = 1, pageSize: number = 20): Promise<BatchJobListResponse> {
    const response = await axios.get(`${this.baseURL}/batch/jobs`, {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }

  async cancelJob(jobId: string): Promise<BatchJobResponse> {
    const response = await axios.post(`${this.baseURL}/batch/${jobId}/cancel`);
    return response.data;
  }

  async exportResults(jobId: string, options: BatchExportOptions): Promise<Blob> {
    const response = await axios.post(`${this.baseURL}/batch/${jobId}/export`, options, {
      responseType: 'blob'
    });
    return response.data;
  }

  createProgressWebSocket(jobId: string): WebSocket {
    const wsUrl = `${this.baseURL.replace('http', 'ws')}/batch/progress/${jobId}`;
    return new WebSocket(wsUrl);
  }

  // Helper method to download exported file
  downloadFile(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Helper method to format file size
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Helper method to format duration
  formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }

  // Helper method to get status color
  getStatusColor(status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' {
    switch (status) {
      case 'pending': return 'default';
      case 'processing': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  }

  // Helper method to get status icon
  getStatusIcon(status: string): string {
    switch (status) {
      case 'pending': return 'PENDING';
      case 'processing': return 'PROCESSING';
      case 'completed': return 'COMPLETED';
      case 'failed': return 'FAILED';
      case 'cancelled': return 'CANCELLED';
      default: return 'UNKNOWN';
    }
  }
}

export const batchAPI = new BatchAPI();
