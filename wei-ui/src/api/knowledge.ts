/**
 * Knowledge Base API client
 * 
 * Endpoints:
 * - GET /proxy/admin/knowledge/documents - List documents
 * - POST /proxy/admin/knowledge/documents - Create document
 * - GET /proxy/admin/knowledge/documents/:id - Get document
 * - PUT /proxy/admin/knowledge/documents/:id - Update document
 * - DELETE /proxy/admin/knowledge/documents/:id - Delete document
 * - POST /proxy/admin/knowledge/documents/upload - Upload file
 * - POST /proxy/admin/knowledge/documents/:id/extract - Extract knowledge
 * - GET /proxy/admin/knowledge/documents/:id/download - Download file
 * - POST /proxy/admin/knowledge/query - Query knowledge base
 * - GET /proxy/admin/knowledge/stats - Get statistics
 */

import { request } from './request';

export type DocumentStatus = 'pending' | 'extracting' | 'extracted' | 'processing' | 'processed' | 'failed';
export type DocumentType = 'text' | 'pdf' | 'doc' | 'image' | 'video' | 'audio' | 'rss' | 'web';

export interface KnowledgeChunk {
  id?: string;
  content: string;
  document_id: string;
  model_id?: string;
  topic?: string;
  metadata: Record<string, any>;
  score?: number;
  created_at: string;
}

export interface Document {
  id?: string;
  title: string;
  content?: string;
  content_type: DocumentType;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  status: DocumentStatus;
  status_message?: string;
  model_id?: string;
  shared: boolean;
  topics: string[];
  extraction_confidence?: number;
  chunk_count: number;
  word_count?: number;
  source_url?: string;
  source_type?: string;
  tags: string[];
  custom_metadata: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface DocumentListParams {
  model_id?: string;
  status?: DocumentStatus;
  content_type?: DocumentType;
  shared?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface DocumentListResponse {
  total: number;
  documents: Document[];
  skip: number;
  limit: number;
}

export interface DocumentCreateRequest {
  title: string;
  content_type?: DocumentType;
  model_id?: string;
  shared?: boolean;
  tags?: string[];
  source_url?: string;
  source_type?: string;
  custom_metadata?: Record<string, any>;
}

export interface DocumentUpdateRequest {
  title?: string;
  content?: string;
  model_id?: string;
  shared?: boolean;
  tags?: string[];
  topics?: string[];
  custom_metadata?: Record<string, any>;
}

export interface FileUploadResponse {
  success: boolean;
  document_id?: string;
  file_name: string;
  file_size: number;
  content_type: DocumentType;
  message: string;
  status: DocumentStatus;
}

export interface KnowledgeQueryRequest {
  query: string;
  model_id?: string;
  topic?: string;
  limit?: number;
  threshold?: number;
}

export interface KnowledgeQueryResponse {
  query: string;
  results: KnowledgeChunk[];
  total_found: number;
  threshold_used: number;
}

export interface ExtractionRequest {
  document_id: string;
  model_id?: string;
  threshold?: number;
  auto_classify?: boolean;
}

export interface ExtractionResult {
  document_id: string;
  success: boolean;
  chunks_created: number;
  topics_detected: string[];
  confidence_score?: number;
  message: string;
  processing_time_ms?: number;
}

export interface DocumentStats {
  total_documents: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_model: Record<string, number>;
  total_chunks: number;
  total_words: number;
  avg_extraction_confidence?: number;
}

// List documents
export function getDocuments(params: DocumentListParams = {}): Promise<DocumentListResponse> {
  return request.get('/knowledge/documents', { params });
}

// Create document
export function createDocument(data: DocumentCreateRequest): Promise<Document> {
  return request.post('/knowledge/documents', data);
}

// Get document
export function getDocument(id: string): Promise<Document> {
  return request.get(`/knowledge/documents/${id}`);
}

// Update document
export function updateDocument(id: string, data: DocumentUpdateRequest): Promise<Document> {
  return request.put(`/knowledge/documents/${id}`, data);
}

// Delete document
export function deleteDocument(id: string): Promise<{ success: boolean; message: string }> {
  return request.delete(`/knowledge/documents/${id}`);
}

// Upload file
export function uploadFile(
  file: File,
  options: {
    model_id?: string;
    shared?: boolean;
    title?: string;
    tags?: string;
  } = {}
): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (options.model_id) formData.append('model_id', options.model_id);
  if (options.shared) formData.append('shared', String(options.shared));
  if (options.title) formData.append('title', options.title);
  if (options.tags) formData.append('tags', options.tags);
  
  return request.post('/knowledge/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

// Extract knowledge from document
export function extractDocument(
  id: string,
  data: Omit<ExtractionRequest, 'document_id'> = {}
): Promise<ExtractionResult> {
  return request.post(`/knowledge/documents/${id}/extract`, data);
}

// Reprocess document
export function reprocessDocument(
  id: string,
  data: Omit<ExtractionRequest, 'document_id'> = {}
): Promise<ExtractionResult> {
  return request.post(`/knowledge/documents/${id}/reprocess`, data);
}

// Download document file
export function downloadDocument(id: string): Promise<Blob> {
  return request.get(`/knowledge/documents/${id}/download`, {
    responseType: 'blob',
  });
}

// Query knowledge base
export function queryKnowledge(data: KnowledgeQueryRequest): Promise<KnowledgeQueryResponse> {
  return request.post('/knowledge/query', data);
}

// Get statistics
export function getKnowledgeStats(): Promise<DocumentStats> {
  return request.get('/knowledge/stats');
}
