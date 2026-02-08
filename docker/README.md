# Docker Infrastructure - AI Gateway

Complete Docker Compose infrastructure for the AI Gateway project with all required services.

## Services Overview

| Service | Port | Purpose | Image |
|---------|------|---------|-------|
| MongoDB | 27017 | Primary data persistence | mongo:7.0 |
| Redis | 6379 | Cache and session storage | redis:7.2-alpine |
| Qdrant | 6333 | Vector database for embeddings | qdrant/qdrant:v1.7.4 |
| SearxNG | 8080 | Privacy-respecting search | searxng/searxng:latest |
| LibreX | 8081 | Privacy-focused search | hnhx/librex:latest |
| 4get | 8082 | Lightweight search aggregator | evanpurl/4get:latest |

## Directory Structure

```
.
├── docker-compose.yml          # Main compose file
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── docker/
    ├── mongodb/
    │   ├── init/
    │   │   └── 01-init-db.sh   # MongoDB initialization
    │   └── mongod.conf         # MongoDB configuration
    ├── redis/
    │   └── redis.conf          # Redis configuration
    └── searxng/
        └── settings.yml        # SearxNG settings
```

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Update secrets in `.env`:**
   - Change all default passwords
   - Add your API keys (OpenAI, Anthropic, etc.)

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Verify services are running:**
   ```bash
   docker-compose ps
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f [service-name]
   ```

## Service Health Checks

All services include health checks that monitor:
- MongoDB: Database ping command
- Redis: Increment operation
- Qdrant: HTTP health endpoint
- SearxNG: HTTP health endpoint
- LibreX: HTTP response check
- 4get: HTTP response check

Check health status:
```bash
docker-compose ps
```

## Data Persistence

Docker volumes are used for data persistence:
- `mongodb_data` - MongoDB data files
- `redis_data` - Redis data and AOF files
- `qdrant_data` - Qdrant vector storage
- `searxng_data` - SearxNG configuration

## Networks

All services communicate through the `ai-gateway-network` bridge network (subnet: 172.20.0.0/16).

## MongoDB Collections

The initialization script creates the following collections with indexes:
- `conversations` - Chat conversations
- `messages` - Individual messages
- `api_keys` - API key storage
- `rate_limits` - Rate limiting data
- `cache` - Application cache
- `user_settings` - User preferences

## Redis Configuration

- Memory limit: 256MB with LRU eviction
- AOF persistence enabled for durability
- Keyspace notifications enabled for cache invalidation

## Environment Variables

See `.env.example` for all available configuration options including:
- Database credentials
- API keys for AI providers
- Service ports and settings
- Security configuration

## Troubleshooting

**MongoDB fails to start:**
```bash
docker-compose logs mongodb
```

**Reset all data (WARNING: Destructive):**
```bash
docker-compose down -v
docker-compose up -d
```

**Check individual service:**
```bash
docker-compose exec mongodb mongosh
```

## Production Considerations

1. **Security:**
   - Change all default passwords in `.env`
   - Enable MongoDB authentication
   - Use strong Redis password
   - Set SearxNG secret key

2. **Resource Limits:**
   Uncomment resource limits in `.env`:
   ```env
   MONGODB_MEMORY_LIMIT=2g
   REDIS_MEMORY_LIMIT=1g
   QDRANT_MEMORY_LIMIT=2g
   ```

3. **Backup:**
   - MongoDB: Use `mongodump`
   - Redis: Backup `/data` volume
   - Qdrant: Backup storage volume

4. **Monitoring:**
   - Enable Prometheus metrics
   - Set up log aggregation
   - Monitor health check status

## License

Part of the AI Gateway project.
