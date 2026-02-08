# AI Gateway

A comprehensive AI gateway system for personal use with virtual model management, chat routing, knowledge base, media processing, and RSS feed management.

## Features

### Core Features
- **Virtual Model Management** - Create and manage virtual models with automatic small-to-big model switching
- **OpenAI-Compatible API** - Drop-in replacement for OpenAI API with custom routing logic
- **Knowledge Base** - Upload documents, extract text, and perform semantic search
- **Media Processing** - Video/audio transcription with Whisper, automatic knowledge extraction
- **RSS Feed Management** - Subscribe to feeds, auto-fetch articles, extract to knowledge base
- **Dashboard & Monitoring** - Real-time statistics and service health monitoring

### Technical Features
- **Template Pattern Configuration** - Config in YAML, virtual models editable via API
- **Hot Reload** - Configuration changes without restart
- **Dual Logging** - MongoDB + file logging for comprehensive tracking
- **Vector Search** - Qdrant integration for semantic knowledge search
- **Redis Caching** - Fast caching and background task queue
- **TypeScript Frontend** - Vue 3 + Element Plus with full type safety

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-gateway

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Start Infrastructure

```bash
# Start MongoDB, Redis, Qdrant
docker-compose up -d mongodb redis qdrant

# Wait for services to be ready
sleep 10
```

### 3. Start Backend

```bash
cd app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend

```bash
cd wei-ui
npm install
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:5175
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Configuration

All configuration is managed through `config.yml` at the project root.

### Important Rules

1. **Virtual Models**: Full CRUD via API or direct YAML editing
2. **Other Sections**: Value updates only, structure cannot be modified
3. **No Database Config**: All configuration stays in `config.yml`
4. **Hot Reload**: Changes to `config.yml` are automatically reloaded

### Example Configuration

```yaml
app:
  name: "AI Gateway"
  version: "0.1.0"
  debug: false
  
models:
  small:
    name: "gpt-3.5-turbo"
    proxy_key: "sk-your-key"
    base_url: "https://api.openai.com/v1"
  big:
    name: "gpt-4"
    proxy_key: "sk-your-key"
    base_url: "https://api.openai.com/v1"

virtual_models:
  - model_name: "default-assistant"
    small:
      name: "gpt-3.5-turbo"
    big:
      name: "gpt-4"
    small2big:
      enable: true
      token_threshold: 3000
    enable: true

features:
  knowledge_base:
    enabled: true
    chunk_size: 500
    overlap: 50
    embedding_model: "text-embedding-3-small"
  media_processing:
    enabled: true
    whisper_model: "base"
  rss:
    enabled: true
    auto_fetch: true
    fetch_interval: 30
```

## Usage

### Virtual Models

1. Open http://localhost:5175
2. Navigate to "虚拟模型" (Virtual Models)
3. Create a new virtual model with small and big upstream models
4. Enable automatic switching based on token threshold

### Chat Interface

1. Navigate to "聊天" (Chat)
2. Select a virtual model
3. Enter your API key
4. Start chatting!

The API is OpenAI-compatible:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/proxy/api/v1",
    api_key="your-proxy-key"
)

response = client.chat.completions.create(
    model="default-assistant",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Knowledge Base

1. Navigate to "知识库" (Knowledge)
2. Upload documents or create manually
3. Click "提取" (Extract) to process documents
4. Use "查询" (Query) for semantic search

### Media Processing

1. Navigate to "媒体" (Media)
2. Upload video/audio files
3. Click "转录" (Transcribe) to generate text
4. Text is automatically extracted to knowledge base

### RSS Feeds

1. Navigate to "RSS" (RSS)
2. Configure RSS projects in `config.yml`
3. Click "获取" (Fetch) to retrieve articles
4. Click "提取" (Extract) to add to knowledge base

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend      │     │   Services      │
│   (Vue 3)       │────▶│   (FastAPI)     │────▶│  (Docker)       │
│                 │     │                 │     │                 │
│ - Dashboard     │     │ - Virtual       │     │ - MongoDB       │
│ - Chat UI       │     │   Models        │     │ - Redis         │
│ - Management    │     │ - Chat Routing  │     │ - Qdrant        │
│                 │     │ - Knowledge     │     │                 │
│   Port: 5175    │     │ - Media Proc    │     │                 │
│                 │     │ - RSS           │     │                 │
└─────────────────┘     │   Port: 8000    │     └─────────────────┘
                        └─────────────────┘
```

## API Documentation

Full API documentation available at:

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Manual**: See [docs/API.md](docs/API.md)

### API Overview

**Admin APIs** (`/proxy/admin/*`):
- Virtual Models CRUD
- Configuration Management
- Knowledge Base
- Media Processing
- RSS Management
- Logs & Statistics

**Chat APIs** (`/proxy/api/v1/*`):
- OpenAI-compatible endpoints
- Chat completions (streaming & non-streaming)
- Models list

## Development

### Backend Development

```bash
cd app

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_integration.py -v

# Format code
black .
isort .

# Type checking
mypy .
```

### Frontend Development

```bash
cd wei-ui

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint
npm run lint
```

## Production Deployment

### Docker Production

```bash
# Build and start all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f app
```

### Manual Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Directory Structure

```
ai-gateway/
├── app/                    # Backend application
│   ├── api/               # API endpoints
│   ├── core/              # Core utilities (config, logger, exceptions)
│   ├── db/                # Database clients (MongoDB, Redis, Qdrant)
│   ├── models/            # Pydantic models
│   ├── tests/             # Test suite
│   ├── main.py            # FastAPI entry point
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Container definition
├── wei-ui/                # Frontend application
│   ├── src/
│   │   ├── api/          # API clients
│   │   ├── components/   # Vue components
│   │   ├── views/        # Page components
│   │   ├── router/       # Vue Router config
│   │   └── stores/       # Pinia stores
│   ├── package.json
│   └── Dockerfile
├── docker/               # Docker configurations
│   ├── mongodb/
│   ├── redis/
│   └── searxng/
├── docs/                 # Documentation
│   ├── API.md           # API documentation
│   └── DEPLOYMENT.md    # Deployment guide
├── config.yml           # Main configuration file
├── docker-compose.yml   # Docker services
├── .env.example         # Environment template
└── README.md            # This file
```

## Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check MongoDB connection
docker-compose ps mongodb

# Check Redis connection
redis-cli ping

# Check Qdrant connection
curl http://localhost:6333/healthz
```

**Frontend build fails**
```bash
cd wei-ui
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Config not reloading**
- Check file permissions on `config.yml`
- Verify YAML syntax is valid
- Check backend logs for reload events

### Getting Help

- Check [docs/API.md](docs/API.md) for API usage
- Review [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment issues
- Open an issue on GitHub

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

- FastAPI - Modern Python web framework
- Vue 3 - Progressive JavaScript framework
- Element Plus - Vue 3 component library
- MongoDB - Document database
- Redis - In-memory data store
- Qdrant - Vector similarity search engine
- OpenAI - AI models and API inspiration
