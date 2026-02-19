import type {
  Session,
  CreateSessionResponse,
  UploadResponse,
  AnalysisResult,
  ProgressEvent,
  PassportDetails,
  FinancialSummary,
  EducationSummary,
  CrossValidation,
  ProcessingMetadata,
  BatchUploadResponse,
  BatchStatusResponse,
  DocumentListResponse,
} from './types';

const API_BASE = '/api';

// Backend response types (different from frontend types)
interface BackendPassportDetails {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  sex?: string;
  passport_number?: string;
  issuing_country?: string;
  issue_date?: string;
  expiry_date?: string;
  mrz_data?: {
    document_type?: string;
    raw_line1?: string;
    raw_line2?: string;
    checksum_valid?: boolean | null;
  };
  accuracy_score?: number;
  confidence_level?: string;
  remarks?: string;
  french_equivalence?: string | null;
}

interface BackendFinancialSummary {
  document_type?: string;
  account_holder_name?: string;
  bank_name?: string;
  base_currency?: string;
  amount_original?: number;
  amount_eur?: number;
  financial_threshold_eur?: number;
  worthiness_status?: string;
  remarks?: string;
  french_equivalence?: string | null;
}

interface BackendEducationSummary {
  highest_qualification?: string;
  institution?: string;
  country?: string;
  student_name?: string;
  final_grade_original?: string;
  french_equivalent_grade_0_20?: number | null;
  validation_status?: string;
  remarks?: string;
  french_equivalence?: string | null;
}

interface BackendCrossValidation {
  name_match?: boolean | null;
  name_match_score?: number;
  dob_match?: boolean | null;
  remarks?: string;
}

interface BackendAnalysisResult {
  passport_details?: BackendPassportDetails;
  financial_summary?: BackendFinancialSummary;
  education_summary?: BackendEducationSummary;
  cross_validation?: BackendCrossValidation;
  metadata?: ProcessingMetadata;
}

// Transform backend response to frontend format
export function transformResult(backend: BackendAnalysisResult): AnalysisResult {
  const passport: PassportDetails | null = backend.passport_details ? {
    first_name: backend.passport_details.first_name || null,
    last_name: backend.passport_details.last_name || null,
    date_of_birth: backend.passport_details.date_of_birth || null,
    passport_number: backend.passport_details.passport_number || null,
    issuing_country: backend.passport_details.issuing_country || null,
    issue_date: backend.passport_details.issue_date || null,
    expiry_date: backend.passport_details.expiry_date || null,
    mrz_line1: backend.passport_details.mrz_data?.raw_line1 || null,
    mrz_line2: backend.passport_details.mrz_data?.raw_line2 || null,
    accuracy_score: backend.passport_details.accuracy_score ?? 0,
    confidence_level: backend.passport_details.confidence_level || null,
    remarks: backend.passport_details.remarks || null,
    french_equivalence: backend.passport_details.french_equivalence || null,
  } : null;

  const financial: FinancialSummary | null = backend.financial_summary ? {
    document_type: backend.financial_summary.document_type || null,
    account_holder_name: backend.financial_summary.account_holder_name || null,
    bank_name: backend.financial_summary.bank_name || null,
    base_currency: backend.financial_summary.base_currency || null,
    amount_original: backend.financial_summary.amount_original || null,
    amount_eur: backend.financial_summary.amount_eur || null,
    worthiness_status: backend.financial_summary.worthiness_status || null,
    remarks: backend.financial_summary.remarks || null,
    french_equivalence: backend.financial_summary.french_equivalence || null,
  } : null;

  const education: EducationSummary | null = backend.education_summary ? {
    highest_qualification: backend.education_summary.highest_qualification || null,
    institution: backend.education_summary.institution || null,
    country: backend.education_summary.country || null,
    student_name: backend.education_summary.student_name || null,
    final_grade_original: backend.education_summary.final_grade_original || null,
    french_equivalent_grade_0_20: backend.education_summary.french_equivalent_grade_0_20 ?? null,
    validation_status: backend.education_summary.validation_status || null,
    remarks: backend.education_summary.remarks || null,
    french_equivalence: backend.education_summary.french_equivalence || null,
  } : null;

  const crossValidation: CrossValidation | null = backend.cross_validation ? {
    name_match: backend.cross_validation.name_match ?? null,
    name_match_score: backend.cross_validation.name_match_score || null,
    dob_match: backend.cross_validation.dob_match ?? null,
    remarks: backend.cross_validation.remarks || null,
  } : null;

  const metadata: ProcessingMetadata = backend.metadata || {
    total_documents_scanned: 0,
    documents_by_category: {},
    processing_errors: [],
    processing_warnings: [],
    processing_time_seconds: 0,
  };

  return {
    passport,
    financial,
    education,
    cross_validation: crossValidation,
    metadata,
  };
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Session endpoints
  async createSession(financialThreshold: number = 15000, bankStatementPeriod: number = 3): Promise<CreateSessionResponse> {
    return this.request<CreateSessionResponse>('/sessions', {
      method: 'POST',
      body: JSON.stringify({
        financial_threshold: financialThreshold,
        bank_statement_period: bankStatementPeriod
      }),
    });
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.request<Session>(`/sessions/${sessionId}`);
  }

  async listSessions(): Promise<Session[]> {
    return this.request<Session[]>('/sessions');
  }

  async deleteSession(sessionId: string): Promise<void> {
    await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
  }

  // Document endpoints
  async uploadDocuments(sessionId: string, files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const response = await fetch(`${API_BASE}/sessions/${sessionId}/documents`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async listDocuments(sessionId: string): Promise<{ files: string[]; total: number }> {
    return this.request<{ files: string[]; total: number }>(
      `/sessions/${sessionId}/documents`
    );
  }

  async deleteDocument(sessionId: string, filename: string): Promise<void> {
    await fetch(`${API_BASE}/sessions/${sessionId}/documents/${filename}`, {
      method: 'DELETE',
    });
  }

  // Processing endpoints
  async startProcessing(sessionId: string): Promise<{ message: string; progress_url: string }> {
    return this.request<{ message: string; progress_url: string }>(
      `/sessions/${sessionId}/process`,
      { method: 'POST' }
    );
  }

  async cancelProcessing(sessionId: string): Promise<{ message: string; session_id: string }> {
    return this.request<{ message: string; session_id: string }>(
      `/sessions/${sessionId}/cancel`,
      { method: 'POST' }
    );
  }

  subscribeToProgress(
    sessionId: string,
    onProgress: (event: ProgressEvent) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): () => void {
    const eventSource = new EventSource(`${API_BASE}/sessions/${sessionId}/progress`);

    eventSource.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse(event.data) as ProgressEvent;
        onProgress(data);

        if (data.completed || data.error) {
          eventSource.close();
          if (data.error) {
            onError(new Error(data.error));
          } else {
            onComplete();
          }
        }
      } catch (e) {
        console.error('Failed to parse progress event:', e);
      }
    });

    eventSource.onerror = () => {
      eventSource.close();
      onError(new Error('Connection lost'));
    };

    return () => eventSource.close();
  }

  async getResult(sessionId: string): Promise<AnalysisResult> {
    const backendResult = await this.request<BackendAnalysisResult>(`/sessions/${sessionId}/result`);
    return transformResult(backendResult);
  }

  async generateManualLetter(
    sessionId: string,
    studentName?: string,
    date?: string
  ): Promise<{ message: string; download_url: string }> {
    return this.request<{ message: string; download_url: string }>(
      `/sessions/${sessionId}/generate-letter`,
      {
        method: 'POST',
        body: JSON.stringify({ student_name: studentName, date }),
      }
    );
  }

  // Download URLs
  getJsonDownloadUrl(sessionId: string): string {
    return `${API_BASE}/sessions/${sessionId}/download/json`;
  }

  getExcelDownloadUrl(sessionId: string): string {
    return `${API_BASE}/sessions/${sessionId}/download/excel`;
  }

  getLetterDownloadUrl(sessionId: string): string {
    return `${API_BASE}/sessions/${sessionId}/download/letter`;
  }

  // Batch upload endpoints
  async uploadBatchFolders(
    files: File[],
    financialThreshold: number = 15000,
    bankStatementPeriod: number = 3
  ): Promise<BatchUploadResponse> {
    const formData = new FormData();
    files.forEach(file => {
      // Preserve folder structure in file path
      const webkitPath = (file as any).webkitRelativePath || file.name;
      formData.append('files', file, webkitPath);
    });

    const response = await fetch(
      `${API_BASE}/batches/upload?financial_threshold=${financialThreshold}&bank_statement_period=${bankStatementPeriod}`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Batch upload failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getBatchStatus(batchId: string): Promise<BatchStatusResponse> {
    return this.request<BatchStatusResponse>(`/sessions/batches/${batchId}`);
  }

  async getBatchSessions(batchId: string): Promise<Session[]> {
    return this.request<Session[]>(`/sessions/batches/${batchId}/sessions`);
  }

  // Document viewing endpoints
  getDocumentViewUrl(sessionId: string, filename: string): string {
    return `${API_BASE}/sessions/${sessionId}/documents/${encodeURIComponent(filename)}/view`;
  }

  async listSessionDocuments(sessionId: string): Promise<DocumentListResponse> {
    return this.request<DocumentListResponse>(`/sessions/${sessionId}/documents/list`);
  }
}

export const api = new ApiClient();
