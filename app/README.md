# AI Gateway FastAPI Backend

FastAPI backend framework with Template Pattern Configuration Management.

## Features

- **ConfigManager with Template Pattern**: Virtual models allow CRUD, other sections fixed
- **Dual Logging**: MongoDB + file logging with rotation
- **Database Connections**: MongoDB (Motor), Redis, Qdrant
- **Health Checks**: Comprehensive health endpoints
- **Hot Reload**: Configuration auto-reloads on file changes

## Quick Start

### 1. Install Dependencies

```bash
cd app
pip install -r requirements.txt
```

### 2. Ensure Docker Services are Running

```bash
# From project root
docker-compose up -d mongo redis qdrant
```

### 3. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py script
python main.py
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API documentation
curl http://localhost:8000/docs
```

## Project Structure

```
app/
├── main.py                 # FastAPI entry point
├── requirements.txt        # Dependencies
├── Dockerfile             # Container config
├── config.yml             # Configuration file
├── core/                  # Core components
│   ├── config_manager.py  # ConfigManager with Template Pattern
│   ├── config_template.py # Template definitions
│   ├── logger.py          # Dual logging system
│   ├── exceptions.py      # Custom exceptions
│   └── middleware.py      # FastAPI middleware
├── db/                    # Database connections
│   ├── mongodb.py         # MongoDB (Motor)
│   ├── redis.py           # Redis
│   └── qdrant.py          # Qdrant
├── models/                # Pydantic models
│   ├── base.py            # Base models
│   └── log.py             # Log models
├── api/                   # API routes
│   └── v1/
│       └── endpoints/
│           └── health.py  # Health check endpoints
└── utils/                 # Utilities
    └── helpers.py         # Helper functions
```

## Configuration

### Template Pattern Rules

1. **Virtual Models**: Full CRUD allowed
   - Can add new models
   - Can delete existing models
   - Can modify structure

2. **Fixed Nodes**: Values only
   - Cannot add new keys
   - Cannot delete keys
   - Can only change values

### Example Config Operations

```python
from app.core import get_config_manager

cm = get_config_manager()

# Read config
port = cm.get("app.port")

# Modify value (allowed)
cm.set("app.port", 9000)

# Add virtual model (allowed)
cm.add_virtual_model("new_model", {...})

# Delete virtual model (allowed)
cm.delete_virtual_model("old_model")

# Add key to fixed node (BLOCKED)
cm.set("app.new_key", "value")  # Error!
```

## API Endpoints

### Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Overall health status |
| `GET /api/v1/health/ready` | Readiness probe |
| `GET /api/v1/health/live` | Liveness probe |
| `GET /api/v1/health/mongodb` | MongoDB health |
| `GET /api/v1/health/redis` | Redis health |
| `GET /api/v1/health/qdrant` | Qdrant health |

### Configuration

| Endpoint | Description |
|----------|-------------|
| `GET /config` | Get current configuration |

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
cd app
python -m pytest tests/ -v
```

### Manual Testing

```bash
# Start services
docker-compose up -d

# Run example usage
python example_usage.py

# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test config hot reload
# 1. Edit config.yml
# 2. Watch logs for reload message
```

## Docker Deployment

### Build Image

```bash
cd app
docker build -t ai-gateway:latest .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config.yml:/app/config.yml \
  -e CONFIG_PATH=/app/config.yml \
  --name ai-gateway \
  ai-gateway:latest
```

## Logging

### MongoDB Collections

- `system_logs`: System events
- `operation_logs`: User operations

### File Output

- `./logs/system/`: System logs
- `./logs/operation/`: Operation logs
- `./logs/error/`: Error logs (all errors)

Log rotation: Daily, 30-day retention

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | `config.yml` | Path to config file |
| `PYTHONPATH` | `/app` | Python path |

## License

MIT
