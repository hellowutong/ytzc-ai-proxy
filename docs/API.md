# AI Gateway API Documentation

## Overview

The AI Gateway provides two sets of APIs:

1. **Admin APIs** (`/proxy/admin/*`) - Backend management, RESTful style
2. **Chat/Routing APIs** (`/proxy/api/v1/*`) - OpenAI-compatible chat endpoints

## Base URLs

- **Development**: `http://localhost:8000`
- **Admin APIs**: `http://localhost:8000/proxy/admin`
- **Chat APIs**: `http://localhost:8000/proxy/api/v1`

---

## Authentication

### Admin APIs

No authentication required by default (local deployment for personal use).

### Chat APIs

Uses Bearer token authentication:

```http
Authorization: Bearer <proxy_key>
```

The `proxy_key` is configured per upstream model in the virtual model configuration.

---

## Admin APIs

### Virtual Models

#### List All Virtual Models
```http
GET /proxy/admin/virtual-models
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "models": [...],
    "total": 10,
    "enabled_count": 8
  },
  "message": "success"
}
```

#### Create Virtual Model
```http
POST /proxy/admin/virtual-models
Content-Type: application/json

{
  "model_name": "my-custom-model",
  "small": {
    "name": "gpt-3.5-turbo",
    "proxy_key": "sk-small-key",
    "base_url": "https://api.openai.com/v1"
  },
  "big": {
    "name": "gpt-4",
    "proxy_key": "sk-big-key",
    "base_url": "https://api.openai.com/v1"
  },
  "small2big": {
    "enable": true,
    "token_threshold": 3000
  },
  "enable": true
}
```

#### Get Virtual Model
```http
GET /proxy/admin/virtual-models/{model_name}
```

#### Update Virtual Model
```http
PUT /proxy/admin/virtual-models/{model_name}
Content-Type: application/json

{
  "small": {
    "name": "gpt-3.5-turbo-16k",
    "proxy_key": "sk-new-key"
  },
  "enable": true
}
```

#### Delete Virtual Model
```http
DELETE /proxy/admin/virtual-models/{model_name}
```

#### Enable/Disable Model
```http
POST /proxy/admin/virtual-models/{model_name}/enable?enable=true|false
```

#### Switch Small/Big Model
```http
POST /proxy/admin/virtual-models/{model_name}/switch-model
Content-Type: application/json

{
  "model_type": "small"
}
```

#### Get Model Statistics
```http
GET /proxy/admin/virtual-models/{model_name}/stats
```

---

### Configuration

#### Get Full Config
```http
GET /proxy/admin/config
```

#### Get Config Section
```http
GET /proxy/admin/config/{section}
```

Sections: `app`, `servers`, `models`, `virtual_models`, `proxy`, `features`, `knowledge`, `media`, `rss`

#### Update Config Values
```http
POST /proxy/admin/config/update
Content-Type: application/json

{
  "section": {
    "key": "value"
  }
}
```

**Note:** Only value updates allowed. Cannot add/remove keys in readonly sections.

---

### Knowledge Base

#### List Documents
```http
GET /proxy/admin/knowledge/documents?page=1&page_size=20&status=completed&type=text
```

Query Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)
- `status`: Filter by status (pending/processing/completed/error)
- `type`: Filter by type (text/pdf/doc/docx/md/html)
- `search`: Search in title/content
- `model_name`: Filter by model name

#### Create Document
```http
POST /proxy/admin/knowledge/documents
Content-Type: application/json

{
  "title": "My Document",
  "content": "Document content...",
  "source": "manual",
  "type": "text",
  "tags": ["ai", "ml"],
  "model_name": "custom-model",
  "permanent": false
}
```

#### Upload File
```http
POST /proxy/admin/knowledge/documents/upload
Content-Type: multipart/form-data

file: <binary>
title: My Uploaded File
source: upload
tags: ["tag1", "tag2"]
```

#### Extract Document
```http
POST /proxy/admin/knowledge/documents/{id}/extract
```

#### Query Knowledge
```http
POST /proxy/admin/knowledge/query
Content-Type: application/json

{
  "query": "search query",
  "model_name": "custom-model",
  "top_k": 5,
  "permanent_only": false
}
```

#### Get Document Detail
```http
GET /proxy/admin/knowledge/documents/{id}
```

#### Update Document
```http
PUT /proxy/admin/knowledge/documents/{id}
Content-Type: application/json

{
  "title": "Updated Title",
  "tags": ["new-tag"],
  "permanent": true
}
```

#### Delete Document
```http
DELETE /proxy/admin/knowledge/documents/{id}
```

#### Get Statistics
```http
GET /proxy/admin/knowledge/stats
```

---

### Media Processing

#### List Media Files
```http
GET /proxy/admin/media/files?page=1&page_size=20&type=video&status=completed
```

Query Parameters:
- `type`: video/audio/text
- `status`: pending/processing/completed/error
- `search`: Search in title

#### Upload Media
```http
POST /proxy/admin/media/upload
Content-Type: multipart/form-data

file: <binary>
title: My Video
type: video
description: Video description
tags: ["tag1"]
```

#### Download from URL
```http
POST /proxy/admin/media/download-url
Content-Type: application/json

{
  "url": "https://example.com/video.mp4",
  "title": "Downloaded Video",
  "type": "video",
  "tags": ["download"]
}
```

#### Transcribe Media
```http
POST /proxy/admin/media/files/{id}/transcribe
Content-Type: application/json

{
  "model": "base",
  "language": "zh",
  "extract_to_knowledge": true
}
```

#### Get Media Detail
```http
GET /proxy/admin/media/files/{id}
```

#### Update Media
```http
PUT /proxy/admin/media/files/{id}
Content-Type: application/json

{
  "title": "Updated Title",
  "description": "New description",
  "tags": ["updated"]
}
```

#### Delete Media
```http
DELETE /proxy/admin/media/files/{id}
```

#### Download Original File
```http
GET /proxy/admin/media/files/{id}/download
```

#### Get Statistics
```http
GET /proxy/admin/media/stats
```

---

### RSS Management

#### List Projects
```http
GET /proxy/admin/rss/projects
```

#### Get Project
```http
GET /proxy/admin/rss/projects/{name}
```

#### Update Project
```http
PUT /proxy/admin/rss/projects/{name}
Content-Type: application/json

{
  "enabled": true,
  "fetch_interval": 30,
  "retention_days": 30,
  "default_permanent": false,
  "model_name": "custom-model"
}
```

#### Fetch Feeds
```http
POST /proxy/admin/rss/fetch
Content-Type: application/json

{
  "project_name": "feed"  // null for all projects
}
```

#### List Items
```http
GET /proxy/admin/rss/items?page=1&page_size=20&status=unread&extracted=false
```

Query Parameters:
- `project_name`: Filter by project
- `status`: all/unread/read
- `storage_type`: all/archive/permanent
- `extracted`: Filter by extraction status
- `search`: Search in title/content

#### Get Item
```http
GET /proxy/admin/rss/items/{id}
```

#### Update Item
```http
PUT /proxy/admin/rss/items/{id}
Content-Type: application/json

{
  "title": "Updated Title",
  "permanent": true
}
```

#### Delete Item
```http
DELETE /proxy/admin/rss/items/{id}
```

#### Mark as Read
```http
POST /proxy/admin/rss/items/{id}/read
Content-Type: application/json

{
  "read": true
}
```

#### Extract to Knowledge
```http
POST /proxy/admin/rss/items/{id}/extract
Content-Type: application/json

{
  "model_name": "custom-model",
  "extract_images": true
}
```

#### Batch Operations
```http
POST /proxy/admin/rss/batch
Content-Type: application/json

{
  "operation": "read|archive|permanent|unpermanent|delete",
  "ids": ["id1", "id2", "id3"]
}
```

#### Search Items
```http
POST /proxy/admin/rss/search
Content-Type: application/json

{
  "query": "search term",
  "project_name": "feed",
  "status": "unread",
  "extracted": false,
  "limit": 20
}
```

#### Cleanup Old Items
```http
POST /proxy/admin/rss/cleanup
Content-Type: application/json

{
  "project_name": "feed",
  "older_than_days": 30,
  "dry_run": true
}
```

#### Get Statistics
```http
GET /proxy/admin/rss/stats
```

---

### Logs

#### Query Request Logs
```http
GET /proxy/admin/logs/requests?limit=100&level=INFO&from_time=2024-01-01T00:00:00
```

Query Parameters:
- `limit`: Max results (default: 100)
- `level`: Filter by level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `from_time/to_time`: Time range
- `model_name`: Filter by model

#### Query System Logs
```http
GET /proxy/admin/logs/system?limit=100&level=ERROR
```

#### Query Operation Logs
```http
GET /proxy/admin/logs/operations?limit=100&operation=CREATE
```

#### Get Statistics
```http
GET /proxy/admin/logs/stats?from_time=2024-01-01T00:00:00
```

#### Clear Old Logs
```http
POST /proxy/admin/logs/clear
Content-Type: application/json

{
  "older_than_days": 30
}
```

---

### Dashboard

#### Get Dashboard
```http
GET /proxy/admin/dashboard
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "overview": {
      "virtual_models_total": 10,
      "virtual_models_enabled": 8,
      "knowledge_documents": 100,
      "media_files": 50,
      "rss_items": 200,
      "today_requests": 500
    },
    "statistics": {
      "knowledge": { ... },
      "media": { ... },
      "rss": { ... },
      "logs": { ... }
    },
    "service_health": {
      "mongodb": "healthy",
      "redis": "healthy",
      "qdrant": "healthy"
    },
    "models_summary": [...]
  }
}
```

---

## Chat/Routing APIs (OpenAI-Compatible)

### Models

#### List Models
```http
GET /proxy/api/v1/models
```

**Response:** OpenAI-compatible model list
```json
{
  "object": "list",
  "data": [
    {
      "id": "my-custom-model",
      "object": "model",
      "created": 1700000000,
      "owned_by": "ai-gateway"
    }
  ]
}
```

#### Get Model
```http
GET /proxy/api/v1/models/{model}
```

---

### Chat Completions

#### Create Chat Completion
```http
POST /proxy/api/v1/chat/completions
Authorization: Bearer <proxy_key>
Content-Type: application/json

{
  "model": "my-custom-model",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 100,
  "top_p": 1.0,
  "stream": false
}
```

**Response (Non-streaming):**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "my-custom-model",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 10,
    "total_tokens": 20
  }
}
```

**Streaming Response (SSE):**
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1700000000,"model":"my-custom-model","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1700000000,"model":"my-custom-model","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: [DONE]
```

---

## Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00",
    "version": "0.1.0",
    "services": {
      "mongodb": "connected",
      "redis": "connected",
      "qdrant": "connected"
    }
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "code": 400,
  "error": {
    "type": "validation_error",
    "message": "Invalid request data",
    "details": {...}
  }
}
```

Common HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## Rate Limiting

Currently not implemented (local deployment for personal use).

---

## OpenAPI Schema

Access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These provide interactive exploration and testing of all endpoints.
