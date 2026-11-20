export type UserRole = 'admin' | 'compliance_officer' | 'reviewer' | 'management';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: number;
  full_name: string;
  email: string;
}

export interface DocumentItem {
  id: number;
  title: string;
  circular_number?: string;
  regulator: string;
  publication_date?: string;
  effective_date?: string;
  category: string;
  description?: string;
  file_path?: string | null;
  file_hash: string;
  file_size: number;
  status: 'uploaded' | 'queued' | 'processing' | 'processed' | 'requires_ocr' | 'failed' | 'requires_review';
  page_count: number;
  created_at: string;
  created_by?: number;
  obligation_count?: number;
}

export interface DocumentPage {
  id: number;
  page_number: number;
  char_count: number;
  word_count: number;
  has_selectable_text: boolean;
  extracted_text: string;
  bounding_boxes: WordBox[];
  layout_blocks: LayoutBlock[];
}

export interface WordBox {
  text: string;
  x0: number;
  top: number;
  x1: number;
  bottom: number;
}

export interface LayoutBlock {
  text: string;
  char_start: number;
  char_end: number;
}

export interface EvidenceSpan {
  id: number;
  page_number: number;
  exact_text: string;
  char_start: number;
  char_end: number;
  bounding_box: {
    x0?: number;
    top?: number;
    x1?: number;
    bottom?: number;
    page?: number;
  };
  confidence: number;
}

export interface ObligationItem {
  id: number;
  obligation_code: string;
  document_id: number;
  source_page: number;
  obligation_text: string;
  responsible_entity?: string;
  required_action: string;
  deadline?: string;
  conditions: string[];
  exceptions: string[];
  confidence_score: number;
  evidence_status: 'anchored' | 'unverified' | 'mismatched';
  review_status: 'pending' | 'approved' | 'corrected' | 'rejected' | 'requires_investigation';
  extraction_method: string;
  created_at: string;
  document_title?: string;
  circular_number?: string;
  evidence_span?: EvidenceSpan;
}

export interface ReviewRecord {
  id: number;
  action: string;
  reviewer_name: string;
  reviewer_email: string;
  comments?: string;
  created_at: string;
  previous_values: Record<string, any>;
  updated_values: Record<string, any>;
}

export interface ObligationChange {
  id: number;
  comparison_id: number;
  previous_obligation_id?: number;
  current_obligation_id?: number;
  change_type: 'new' | 'modified' | 'retired' | 'unchanged' | 'requires_review';
  change_explanation: string;
  diff_details: {
    similarity?: number;
    previous_deadline?: string;
    current_deadline?: string;
    previous_entity?: string;
    current_entity?: string;
    previous_text?: string;
    current_text?: string;
    [key: string]: any;
  };
  human_verified: boolean;
  previous_obligation?: ObligationItem;
  current_obligation?: ObligationItem;
}

export interface ComparisonItem {
  id: number;
  title: string;
  base_document_id: number;
  target_document_id: number;
  base_document_title?: string;
  base_circular_number?: string;
  target_document_title?: string;
  target_circular_number?: string;
  status: string;
  created_at: string;
  changes: ObligationChange[];
}

export interface ControlCategory {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface ObligationControlMapping {
  id: number;
  obligation_id: number;
  control_category_id: number;
  category_code: string;
  category_name: string;
  rationale: string;
  mapping_method: 'nlp_suggested' | 'reviewer_assigned';
  review_status: 'suggested' | 'approved' | 'rejected';
  obligation_code?: string;
  obligation_text?: string;
}

export interface ImpactReportItem {
  id: number;
  title: string;
  document_id?: number;
  comparison_id?: number;
  executive_summary: string;
  metrics: {
    total_obligations: number;
    approved_obligations: number;
    pending_reviews: number;
    corrected_obligations: number;
    rejected_candidates: number;
    impacted_control_count: number;
    identified_entities_count: number;
  };
  report_data: {
    title: string;
    circular_number?: string;
    regulator: string;
    publication_date?: string;
    generated_at: string;
    generated_by: string;
    executive_summary: string;
    metrics: Record<string, any>;
    control_distribution: Record<string, number>;
    entity_distribution: Record<string, number>;
    high_priority_action_items: Array<{
      obligation_code: string;
      responsible_entity: string;
      action: string;
      deadline: string;
      page: number;
      review_status: string;
    }>;
    all_obligations: any[];
    legal_limitations_notice: string;
    comparison_title?: string;
    changes_breakdown?: any[];
  };
  created_at: string;
  generated_by?: number;
}

export interface AuditLogItem {
  id: number;
  user_id?: number;
  user_email?: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

export interface DashboardMetrics {
  total_documents: number;
  processed_documents: number;
  total_obligations: number;
  pending_reviews: number;
  approved_obligations: number;
  new_obligations: number;
  modified_obligations: number;
  retired_obligations: number;
  impacted_controls_count: number;
  recent_documents: any[];
  recent_obligations: any[];
  recent_changes: any[];
  pending_review_items: any[];
}
