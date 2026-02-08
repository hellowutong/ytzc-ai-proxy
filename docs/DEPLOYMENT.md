# Deployment Guide

Complete guide for deploying AI Gateway in production environments.

## Quick Start (Docker Compose)

For manual testing, use the unified docker-compose configuration:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit environment variables (optional for testing)
# nano .env

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be ready
echo "Waiting for services..."
sleep 15

# 5. Verify services are running
docker-compose ps

# 6. Check health
curl http://localhost:8000/api/v1/health
curl http://localhost:5175
```

**Access Points:**
- Frontend UI: http://localhost:5175
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MongoDB: localhost:27017
- Redis: localhost:6379
- Qdrant: localhost:6333

**Stop Services:**
```bash
docker-compose down
docker-compose down -v  # Also removes volumes
```

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Reverse Proxy Setup](#reverse-proxy-setup)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB SSD
- OS: Ubuntu 20.04+, CentOS 8+, Debian 11+

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD
- Network: 100Mbps+

### Required Software

- Docker 24.0+
- Docker Compose 2.20+
- Git

### Optional Software

- Nginx (for reverse proxy)
- Certbot (for SSL certificates)
- Prometheus + Grafana (for monitoring)

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    restart: always
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/ai_gateway
      - REDIS_URI=redis://redis:6379/0
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - LOG_LEVEL=INFO
    volumes:
      - ./config.yml:/app/config.yml:ro
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      - mongodb
      - redis
      - qdrant
    networks:
      - ai-gateway
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  wei-ui:
    build:
      context: ./wei-ui
      dockerfile: Dockerfile
    restart: always
    ports:
      - "127.0.0.1:3000:80"
    depends_on:
      - app
    networks:
      - ai-gateway

  mongodb:
    image: mongo:7.0
    restart: always
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_ROOT_USER:-admin}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_ROOT_PASSWORD}
      - MONGO_INITDB_DATABASE=ai_gateway
    volumes:
      - mongodb_data:/data/db
      - ./docker/mongodb/init:/docker-entrypoint-initdb.d:ro
      - ./docker/mongodb/mongod.conf:/etc/mongod.conf:ro
    command: ["mongod", "--config", "/etc/mongod.conf"]
    networks:
      - ai-gateway
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
      - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - ai-gateway
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  qdrant:
    image: qdrant/qdrant:latest
    restart: always
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}
    networks:
      - ai-gateway
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/ssl:/etc/nginx/ssl:ro
      - ./docker/nginx/logs:/var/log/nginx
    depends_on:
      - app
      - wei-ui
    networks:
      - ai-gateway

volumes:
  mongodb_data:
  redis_data:
  qdrant_data:

networks:
  ai-gateway:
    driver: bridge
```

### Environment Variables

Create `.env`:

```bash
# MongoDB
MONGODB_ROOT_USER=admin
MONGODB_ROOT_PASSWORD=your_secure_password_here
MONGODB_USER=ai_gateway
MONGODB_PASSWORD=your_app_password_here

# Redis
REDIS_PASSWORD=your_redis_password_here

# Qdrant
QDRANT_API_KEY=your_qdrant_api_key_here

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Deploy with Docker

```bash
# 1. Clone repository
git clone <repository-url>
cd ai-gateway

# 2. Create environment file
cp .env.example .env
# Edit .env with your secure passwords

# 3. Create required directories
mkdir -p logs data docker/nginx/ssl docker/nginx/logs

# 4. Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Check status
docker-compose ps

# 6. View logs
docker-compose logs -f app
```

---

## Manual Deployment

### Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git nginx

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Backend Deployment

```bash
# Create user
sudo useradd -r -s /bin/false ai-gateway

# Setup directory
sudo mkdir -p /opt/ai-gateway
sudo chown ai-gateway:ai-gateway /opt/ai-gateway

# Clone code
cd /opt/ai-gateway
git clone <repository-url> .

# Setup Python environment
sudo -u ai-gateway python3.11 -m venv venv
sudo -u ai-gateway venv/bin/pip install -r app/requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/ai-gateway.service << 'EOF'
[Unit]
Description=AI Gateway Backend
After=network.target

[Service]
Type=simple
User=ai-gateway
Group=ai-gateway
WorkingDirectory=/opt/ai-gateway/app
Environment=PYTHONPATH=/opt/ai-gateway/app
Environment=MONGODB_URI=mongodb://localhost:27017/ai_gateway
Environment=REDIS_URI=redis://localhost:6379/0
Environment=QDRANT_HOST=localhost
Environment=QDRANT_PORT=6333
Environment=LOG_LEVEL=INFO
ExecStart=/opt/ai-gateway/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable ai-gateway
sudo systemctl start ai-gateway
```

### Frontend Deployment

```bash
cd /opt/ai-gateway/wei-ui

# Install dependencies
npm install

# Build for production
npm run build

# Copy to web server
sudo mkdir -p /var/www/ai-gateway
sudo cp -r dist/* /var/www/ai-gateway/
sudo chown -R www-data:www-data /var/www/ai-gateway
```

---

## Reverse Proxy Setup

### Nginx Configuration

Create `/etc/nginx/sites-available/ai-gateway`:

```nginx
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=chat:10m rate=50r/s;

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (see SSL/TLS section)
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Static file caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Chat API (higher rate limit)
    location /proxy/api/v1/chat/ {
        limit_req zone=chat burst=100 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE support for streaming
        proxy_buffering off;
        proxy_cache off;
        
        # Longer timeout for chat
        proxy_read_timeout 300s;
    }
    
    # Admin API
    location /proxy/admin/ {
        # IP restriction (optional)
        # allow 192.168.1.0/24;
        # deny all;
        
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/ai-gateway /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### Manual SSL

```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Copy certificates
sudo cp your-cert.pem /etc/nginx/ssl/fullchain.pem
sudo cp your-key.pem /etc/nginx/ssl/privkey.pem

# Set permissions
sudo chmod 600 /etc/nginx/ssl/privkey.pem
sudo chmod 644 /etc/nginx/ssl/fullchain.pem

# Reload nginx
sudo systemctl reload nginx
```

---

## Monitoring & Logging

### Application Logs

```bash
# View real-time logs
docker-compose logs -f app

# View specific service
docker-compose logs -f mongodb

# Export logs
docker-compose logs app > app_logs.txt
```

### System Monitoring

Install and configure monitoring stack:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3001:3000"
    
  node-exporter:
    image: prom/node-exporter:latest
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  grafana_data:
```

### Health Checks

```bash
# Backend health
curl https://your-domain.com/api/v1/health

# Frontend check
curl -I https://your-domain.com

# Database checks
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker-compose exec redis redis-cli ping
docker-compose exec qdrant curl http://localhost:6333/healthz
```

---

## Backup & Recovery

### Automated Backups

Create backup script `/opt/ai-gateway/scripts/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/backups/ai-gateway"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
docker-compose exec -T mongodb mongodump --archive > "$BACKUP_DIR/mongodb_$DATE.archive"

# Backup Redis
docker-compose exec -T redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Backup Qdrant
docker run --rm -v ai-gateway_qdrant_data:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/qdrant_$DATE.tar.gz" -C /data .

# Backup Config
cp /opt/ai-gateway/config.yml "$BACKUP_DIR/config_$DATE.yml"

# Compress and encrypt
cd "$BACKUP_DIR"
tar czf "ai-gateway_backup_$DATE.tar.gz" *
# Optional: gpg --encrypt --recipient your-email "ai-gateway_backup_$DATE.tar.gz"

# Cleanup old backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: ai-gateway_backup_$DATE.tar.gz"
```

Make it executable and schedule:

```bash
chmod +x /opt/ai-gateway/scripts/backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /opt/ai-gateway/scripts/backup.sh >> /var/log/ai-gateway-backup.log 2>&1
```

### Recovery

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE="$1"

# Extract backup
tar xzf "$BACKUP_FILE"

# Restore MongoDB
docker-compose exec -T mongodb mongorestore --archive < mongodb_*.archive

# Restore Redis
docker cp redis_*.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis

# Restore Qdrant
docker run --rm -v ai-gateway_qdrant_data:/data -v $(pwd):/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/qdrant_*.tar.gz -C /data"
docker-compose restart qdrant

# Restore Config
cp config_*.yml /opt/ai-gateway/config.yml
docker-compose restart app

echo "Restore completed"
```

---

## Security Considerations

### Network Security

1. **Firewall Configuration**:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

2. **Docker Network Isolation**:
```yaml
# Use internal networks
networks:
  internal:
    internal: true  # No external access
  external:
    driver: bridge
```

### Application Security

1. **Strong API Keys**: Use long, random keys
2. **Rate Limiting**: Configured in Nginx
3. **Input Validation**: Handled by Pydantic models
4. **CORS**: Configure allowed origins
5. **Security Headers**: Set in Nginx config

### Database Security

1. **Authentication**: Always enable auth
2. **Network Binding**: Bind to localhost only
3. **Encryption**: Enable TLS for production
4. **Backups**: Encrypt backup files

---

## Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check logs
docker-compose logs

# Check port conflicts
sudo netstat -tulpn | grep -E '8000|27017|6379|6333'

# Check disk space
df -h

# Check memory
free -h
```

**Database connection errors**
```bash
# Verify MongoDB
docker-compose exec mongodb mongosh -u admin -p --authenticationDatabase admin

# Verify Redis
docker-compose exec redis redis-cli -a <password> ping

# Verify Qdrant
curl http://localhost:6333/healthz
```

**Performance issues**
```bash
# Check resource usage
docker stats

# Check slow queries
docker-compose logs mongodb | grep -i slow

# Monitor connections
ss -tulpn | grep -E '8000|27017'
```

### Debug Mode

Enable debug logging:

```bash
# Set environment
export LOG_LEVEL=DEBUG

# Restart app
docker-compose restart app

# View debug logs
docker-compose logs -f app
```

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Review documentation in `docs/`
3. Open issue on GitHub with logs and config

---

## Maintenance

### Regular Tasks

**Daily**:
- Check service health
- Review error logs
- Monitor disk space

**Weekly**:
- Review backup status
- Check for updates
- Monitor performance metrics

**Monthly**:
- Rotate logs
- Clean old data (if configured)
- Review security logs

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Verify
docker-compose ps
```

---

## Support

For deployment support:
- Check [docs/API.md](API.md) for API issues
- Review [README.md](../README.md) for general usage
- Open GitHub issue with environment details
