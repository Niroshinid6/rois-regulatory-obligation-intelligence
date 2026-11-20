import {
  AuthResponse,
  User,
  DocumentItem,
  DocumentPage,
  ObligationItem,
  ComparisonItem,
  ControlCategory,
  ObligationControlMapping,
  ImpactReportItem,
  AuditLogItem,
  DashboardMetrics,
} from '../types';

const configuredApiBase = import.meta.env.VITE_API_URL?.replace(/\/$/, '');

if (!configuredApiBase) {
  throw new Error('VITE_API_URL is required.');
}

if (import.meta.env.PROD && (
  configuredApiBase.includes('localhost')
  || configuredApiBase.includes('127.0.0.1')
  || !configuredApiBase.startsWith('https://')
)) {
  throw new Error('Production VITE_API_URL must be an HTTPS URL.');
}

const API_BASE = configuredApiBase;

class ApiClient {
  private getHeaders(isFormData = false): HeadersInit {
    const token = localStorage.getItem('rois_token');
    const headers: Record<string, string> = {};

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isFormData = options.body instanceof FormData;
    const url = `${API_BASE}${endpoint}`;

    const headers = {
      ...this.getHeaders(isFormData),
      ...(options.headers as Record<string, string> || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      localStorage.removeItem('rois_token');
      localStorage.removeItem('rois_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      let errorMsg = `API Error (${response.status})`;
      try {
        const errJson = await response.json();
        errorMsg = errJson.detail || errorMsg;
      } catch {
        // use default error message
      }
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Authentication
  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem('rois_token');
      localStorage.removeItem('rois_user');
    }
  }

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>('/dashboard/metrics');
  }

  // Documents
  async getDocuments(params: { search?: string; regulator?: string; status?: string } = {}): Promise<{ total: number; items: DocumentItem[] }> {
    const q = new URLSearchParams();
    if (params.search) q.append('search', params.search);
    if (params.regulator) q.append('regulator', params.regulator);
    if (params.status) q.append('status', params.status);
    return this.request<{ total: number; items: DocumentItem[] }>(`/documents/?${q.toString()}`);
  }

  async getDocument(id: number): Promise<DocumentItem> {
    return this.request<DocumentItem>(`/documents/${id}`);
  }

  async getDocumentPages(id: number): Promise<DocumentPage[]> {
    return this.request<DocumentPage[]>(`/documents/${id}/pages`);
  }

  async uploadDocument(formData: FormData): Promise<DocumentItem> {
    return this.request<DocumentItem>('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async deleteDocument(id: number): Promise<void> {
    return this.request(`/documents/${id}`, { method: 'DELETE' });
  }

  getDocumentPdfUrl(id: number): string {
    return `${API_BASE}/documents/${id}/pdf`;
  }

  async downloadDocument(id: number): Promise<void> {
    const token = localStorage.getItem('rois_token');
    const response = await fetch(`${API_BASE}/documents/${id}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (response.status === 401) {
      throw new Error('Session expired. Please log in again.');
    }
    if (!response.ok) {
      throw new Error(`Document download failed (${response.status}).`);
    }
    const objectUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = `ROIS_Document_${id}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }

  // Obligations
  async getObligations(params: {
    document_id?: number;
    review_status?: string;
    entity?: string;
    search?: string;
    has_deadline?: boolean;
    skip?: number;
    limit?: number;
  } = {}): Promise<{ total: number; items: ObligationItem[] }> {
    const q = new URLSearchParams();
    if (params.document_id) q.append('document_id', params.document_id.toString());
    if (params.review_status) q.append('review_status', params.review_status);
    if (params.entity) q.append('entity', params.entity);
    if (params.search) q.append('search', params.search);
    if (params.has_deadline !== undefined) q.append('has_deadline', params.has_deadline.toString());
    if (params.skip) q.append('skip', params.skip.toString());
    if (params.limit) q.append('limit', params.limit.toString());
    return this.request<{ total: number; items: ObligationItem[] }>(`/obligations/?${q.toString()}`);
  }

  async getObligation(id: number): Promise<ObligationItem> {
    return this.request<ObligationItem>(`/obligations/${id}`);
  }

  async reviewObligation(id: number, data: {
    action: 'approved' | 'rejected' | 'corrected';
    responsible_entity?: string;
    required_action?: string;
    deadline?: string;
    comments?: string;
  }): Promise<ObligationItem> {
    return this.request<ObligationItem>(`/obligations/${id}/review`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Evidence
  async getEvidenceDetails(obligationId: number): Promise<any> {
    return this.request<any>(`/evidence/${obligationId}`);
  }

  // Comparisons
  async getComparisons(): Promise<ComparisonItem[]> {
    return this.request<ComparisonItem[]>('/comparisons/');
  }

  async getComparison(id: number): Promise<ComparisonItem> {
    return this.request<ComparisonItem>(`/comparisons/${id}`);
  }

  async createComparison(data: { base_document_id: number; target_document_id: number; title?: string }): Promise<ComparisonItem> {
    return this.request<ComparisonItem>('/comparisons/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async verifyChange(changeId: number, verifiedType?: string): Promise<any> {
    const q = verifiedType ? `?verified_type=${verifiedType}` : '';
    return this.request<any>(`/comparisons/changes/${changeId}/verify${q}`, {
      method: 'PUT',
    });
  }

  // Controls
  async getControlCategories(): Promise<ControlCategory[]> {
    return this.request<ControlCategory[]>('/controls/categories');
  }

  async createControlCategory(data: { code: string; name: string; description?: string }): Promise<ControlCategory> {
    const q = new URLSearchParams({ code: data.code, name: data.name });
    if (data.description) q.append('description', data.description);
    return this.request<ControlCategory>(`/controls/categories?${q.toString()}`, {
      method: 'POST',
    });
  }

  async getControlMappings(params: { obligation_id?: number; control_category_id?: number; review_status?: string } = {}): Promise<ObligationControlMapping[]> {
    const q = new URLSearchParams();
    if (params.obligation_id) q.append('obligation_id', params.obligation_id.toString());
    if (params.control_category_id) q.append('control_category_id', params.control_category_id.toString());
    if (params.review_status) q.append('review_status', params.review_status);
    return this.request<ObligationControlMapping[]>(`/controls/mappings?${q.toString()}`);
  }

  async createControlMapping(data: { obligation_id: number; control_category_id: number; rationale: string }): Promise<ObligationControlMapping> {
    const q = new URLSearchParams({
      obligation_id: data.obligation_id.toString(),
      control_category_id: data.control_category_id.toString(),
      rationale: data.rationale,
    });
    return this.request<ObligationControlMapping>(`/controls/mappings?${q.toString()}`, {
      method: 'POST',
    });
  }

  async updateControlMapping(mappingId: number, data: { review_status: string; rationale?: string }): Promise<ObligationControlMapping> {
    return this.request<ObligationControlMapping>(`/controls/mappings/${mappingId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Reports
  async getReports(): Promise<ImpactReportItem[]> {
    return this.request<ImpactReportItem[]>('/reports/');
  }

  async generateReport(data: { document_id?: number; comparison_id?: number; title?: string }): Promise<ImpactReportItem> {
    return this.request<ImpactReportItem>('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReport(id: number): Promise<ImpactReportItem> {
    return this.request<ImpactReportItem>(`/reports/${id}`);
  }

  getReportDownloadUrl(id: number): string {
    return `${API_BASE}/reports/${id}/download`;
  }

  async downloadReport(id: number, format: 'json' | 'pdf'): Promise<void> {
    const token = localStorage.getItem('rois_token');
    const endpoint = format === 'pdf'
      ? `/reports/${id}/download/pdf`
      : `/reports/${id}/download`;
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (response.status === 401) {
      localStorage.removeItem('rois_token');
      localStorage.removeItem('rois_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      let errorMessage = `Report export failed (${response.status}).`;
      try {
        const errorBody = await response.json();
        errorMessage = errorBody.detail || errorMessage;
      } catch {
        // Keep the status-based message for non-JSON server errors.
      }
      throw new Error(errorMessage);
    }

    const objectUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = `ROIS_Impact_Report_${id}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }

  // Users
  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/users/');
  }

  async createUser(data: any): Promise<User> {
    return this.request<User>('/users/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateUser(userId: number, data: any): Promise<User> {
    return this.request<User>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Audit
  async getAuditLogs(params: { resource_type?: string; action?: string; skip?: number; limit?: number } = {}): Promise<AuditLogItem[]> {
    const q = new URLSearchParams();
    if (params.resource_type) q.append('resource_type', params.resource_type);
    if (params.action) q.append('action', params.action);
    if (params.skip) q.append('skip', params.skip.toString());
    if (params.limit) q.append('limit', params.limit.toString());
    return this.request<AuditLogItem[]>(`/audit/?${q.toString()}`);
  }
}

export const api = new ApiClient();
