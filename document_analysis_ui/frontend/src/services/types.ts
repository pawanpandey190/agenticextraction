// Session types
export type SessionStatus = 'created' | 'uploading' | 'processing' | 'completed' | 'failed';

export interface Session {
  id: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  uploaded_files: string[];
  total_files: number;
  financial_threshold: number;
  result_available: boolean;
  letter_available: boolean;
  error_message: string | null;
  // Batch support
  batch_id: string | null;
  student_name: string | null;
}

export interface CreateSessionResponse {
  session_id: string;
  status: SessionStatus;
  upload_url: string;
}

export interface UploadResponse {
  uploaded_files: string[];
  total_files: number;
}

// Progress types
export interface ProgressEvent {
  stage_name: string;
  stage_index: number;
  total_stages: number;
  message: string;
  percentage: number;
  sub_agent: string | null;
  completed: boolean;
  error: string | null;
  // Document-level tracking
  current_document?: string | null;
  processed_documents?: number;
  total_documents?: number;
}

// Result types
export interface PassportDetails {
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  passport_number: string | null;
  issuing_country: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  mrz_line1: string | null;
  mrz_line2: string | null;
  accuracy_score: number | null;
}

export interface FinancialSummary {
  document_type: string | null;
  account_holder_name: string | null;
  bank_name: string | null;
  base_currency: string | null;
  amount_original: number | null;
  amount_eur: number | null;
  worthiness_status: string | null;
  remarks: string[] | null;
}

export interface EducationSummary {
  highest_qualification: string | null;
  institution: string | null;
  country: string | null;
  student_name: string | null;
  final_grade_original: string | null;
  french_equivalent_grade_0_20: number | null;
  validation_status: string | null;
  remarks: string[] | null;
}

export interface CrossValidation {
  name_match: boolean | null;
  name_match_score: number | null;
  dob_match: boolean | null;
  remarks: string[] | null;
}

export interface ProcessingMetadata {
  total_documents_scanned: number;
  documents_by_category: Record<string, number>;
  processing_errors: string[];
  processing_warnings: string[];
  processing_time_seconds: number;
}

export interface AnalysisResult {
  passport: PassportDetails | null;
  financial: FinancialSummary | null;
  education: EducationSummary | null;
  cross_validation: CrossValidation | null;
  metadata: ProcessingMetadata;
}

// API error type
export interface ApiError {
  detail: string;
  error_code?: string;
}

// Batch upload types
export type BatchStatus = 'created' | 'processing' | 'completed' | 'partial_failure' | 'failed';

export interface BatchSessionInfo {
  session_id: string;
  student_name: string;
  status: SessionStatus;
  total_files: number;
  result_available: boolean;
  letter_available: boolean;
}

export interface BatchUploadResponse {
  batch_id: string;
  total_students: number;
  sessions: BatchSessionInfo[];
  message: string;
}

export interface BatchStatusResponse {
  batch_id: string;
  status: BatchStatus;
  total_students: number;
  completed: number;
  processing: number;
  failed: number;
  created: number;
  sessions: BatchSessionInfo[];
}

export interface DocumentMetadata {
  filename: string;
  size: number;
  type: string;
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total: number;
}
