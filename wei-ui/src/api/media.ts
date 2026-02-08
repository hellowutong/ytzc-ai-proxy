/**
 * Media Processing API Client
 * 
 * Features:
 * - Media file upload/download
 * - URL download
 * - Transcription management
 * - Statistics
 */

import { request } from './request';

export type MediaType = 'video' | 'audio' | 'text' | 'image';
export type MediaStatus = 
  | 'pending' 
  | 'downloading' 
  | 'uploaded' 
  | 'transcribing' 
  | 'transcribed' 
  | 'extracting' 
  | 'processed' 
  | 'failed';

export interface TranscriptionSegment {
  id: string;
  start: number;
  end: number;
  text: string;
  confidence: number;
  speaker?: string;
}

export interface TranscriptionResult {
  text: string;
  language: string;
  confidence: number;
  segments: TranscriptionSegment[];
  duration: number;
  word_count: number;
  processing_time_ms: number;
}

export interface MediaFile {
  id: string;
  title: string;
  media_type: MediaType;
  file_name: string;
  file_path?: string;
  file_size: number;
  mime_type?: string;
  duration?: number;
  source_type: string;
  source_url?: string;
  status: MediaStatus;
  status_message?: string;
  transcription?: TranscriptionResult;
  transcription_model?: string;
  knowledge_document_id?: string;
  tags: string[];
  custom_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  processed_at?: string;
}

export interface MediaCreateRequest {
  title: string;
  media_type: MediaType;
  source_url?: string;
  tags?: string[];
  custom_metadata?: Record<string, any>;
}

export interface MediaUpdateRequest {
  title?: string;
  tags?: string[];
  custom_metadata?: Record<string, any>;
}

export interface MediaListResponse {
  total: number;
  media_files: MediaFile[];
  skip: number;
  limit: number;
}

export interface MediaUploadResponse {
  success: boolean;
  media_id: string;
  file_name: string;
  file_size: number;
  media_type: MediaType;
  message: string;
  status: MediaStatus;
}

export interface TranscriptionRequest {
  language?: string;
  model?: string;
  split?: number;
}

export interface TranscriptionResponse {
  success: boolean;
  media_id: string;
  transcription?: TranscriptionResult;
  message: string;
}

export interface DownloadUrlRequest {
  url: string;
  title?: string;
  media_type: MediaType;
  tags?: string[];
  auto_transcribe?: boolean;
}

export interface DownloadUrlResponse {
  success: boolean;
  media_id: string;
  message: string;
  status: MediaStatus;
}

export interface MediaStats {
  total_files: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  total_duration: number;
  transcribed_count: number;
  pending_count: number;
  failed_count: number;
}

/**
 * List media files with filters
 */
export function listMediaFiles(
  media_type?: MediaType,
  status?: MediaStatus,
  search?: string,
  skip = 0,
  limit = 20
): Promise<MediaListResponse> {
  const params = new URLSearchParams();
  if (media_type) params.append('media_type', media_type);
  if (status) params.append('status', status);
  if (search) params.append('search', search);
  params.append('skip', skip.toString());
  params.append('limit', limit.toString());
  
  return request.get(`/media/files?${params.toString()}`);
}

/**
 * Get a specific media file
 */
export function getMediaFile(mediaId: string): Promise<MediaFile> {
  return request.get(`/media/files/${mediaId}`);
}

/**
 * Create a new media record
 */
export function createMediaRecord(data: MediaCreateRequest): Promise<MediaFile> {
  return request.post('/media/files', data);
}

/**
 * Update media metadata
 */
export function updateMediaFile(
  mediaId: string,
  data: MediaUpdateRequest
): Promise<MediaFile> {
  return request.put(`/media/files/${mediaId}`, data);
}

/**
 * Delete a media file
 */
export function deleteMediaFile(mediaId: string): Promise<{ success: boolean; message: string }> {
  return request.delete(`/media/files/${mediaId}`);
}

/**
 * Upload a media file
 */
export function uploadMediaFile(
  file: File,
  media_type?: MediaType,
  title?: string,
  tags?: string[],
  auto_transcribe = true
): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (media_type) formData.append('media_type', media_type);
  if (title) formData.append('title', title);
  if (tags?.length) formData.append('tags', tags.join(','));
  formData.append('auto_transcribe', auto_transcribe.toString());
  
  return request.post('/media/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * Download media from URL
 */
export function downloadFromUrl(data: DownloadUrlRequest): Promise<DownloadUrlResponse> {
  return request.post('/media/download-url', data);
}

/**
 * Start transcription for a media file
 */
export function transcribeMedia(
  mediaId: string,
  data: TranscriptionRequest = {}
): Promise<TranscriptionResponse> {
  return request.post(`/media/files/${mediaId}/transcribe`, data);
}

/**
 * Download the original media file
 */
export function downloadMediaFile(mediaId: string): string {
  return `/proxy/admin/media/files/${mediaId}/download`;
}

/**
 * Get media statistics
 */
export function getMediaStats(): Promise<MediaStats> {
  return request.get('/media/stats');
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format duration for display
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds === 0) return '-';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get status color for Element Plus
 */
export function getStatusType(status: MediaStatus): '' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<MediaStatus, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'info',
    downloading: 'info',
    uploaded: 'info',
    transcribing: 'warning',
    transcribed: 'success',
    extracting: 'warning',
    processed: 'success',
    failed: 'danger',
  };
  return typeMap[status] || 'info';
}

/**
 * Get status label
 */
export function getStatusLabel(status: MediaStatus): string {
  const labelMap: Record<MediaStatus, string> = {
    pending: '待处理',
    downloading: '下载中',
    uploaded: '已上传',
    transcribing: '转录中',
    transcribed: '已转录',
    extracting: '提取中',
    processed: '已处理',
    failed: '失败',
  };
  return labelMap[status] || status;
}

/**
 * Get media type icon
 */
export function getMediaTypeIcon(type: MediaType): string {
  const iconMap: Record<MediaType, string> = {
    video: 'VideoCamera',
    audio: 'Microphone',
    text: 'Document',
    image: 'Picture',
  };
  return iconMap[type] || 'Document';
}
