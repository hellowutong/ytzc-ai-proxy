#!/bin/bash
#
# AI Gateway Backup Script
# Creates backups of MongoDB, Redis, Qdrant, and configuration
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ai-gateway_backup_${DATE}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Temporary directory for this backup
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

log_info "Starting backup: $BACKUP_NAME"

# Backup MongoDB
log_info "Backing up MongoDB..."
if docker-compose ps | grep -q "mongodb.*Up"; then
    docker-compose exec -T mongodb mongodump --archive > "$TEMP_DIR/mongodb.archive" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_success "MongoDB backup completed"
    else
        log_warning "MongoDB backup may have issues"
    fi
else
    log_warning "MongoDB is not running, skipping MongoDB backup"
fi

# Backup Redis
log_info "Backing up Redis..."
if docker-compose ps | grep -q "redis.*Up"; then
    docker-compose exec -T redis redis-cli BGSAVE > /dev/null 2>&1 || true
    sleep 2
    docker cp $(docker-compose ps -q redis):/data/dump.rdb "$TEMP_DIR/redis.rdb" 2>/dev/null || true
    if [ -f "$TEMP_DIR/redis.rdb" ]; then
        log_success "Redis backup completed"
    else
        log_warning "Redis backup may have issues"
    fi
else
    log_warning "Redis is not running, skipping Redis backup"
fi

# Backup Qdrant
log_info "Backing up Qdrant..."
if docker-compose ps | grep -q "qdrant.*Up"; then
    # Create tar archive of Qdrant data
    docker run --rm \
        -v ai-gateway_qdrant_data:/data \
        -v "$TEMP_DIR":/backup \
        alpine tar czf /backup/qdrant.tar.gz -C /data . 2>/dev/null
    
    if [ -f "$TEMP_DIR/qdrant.tar.gz" ]; then
        log_success "Qdrant backup completed"
    else
        log_warning "Qdrant backup may have issues"
    fi
else
    log_warning "Qdrant is not running, skipping Qdrant backup"
fi

# Backup configuration
log_info "Backing up configuration..."
if [ -f "config.yml" ]; then
    cp config.yml "$TEMP_DIR/config.yml"
    log_success "Configuration backup completed"
else
    log_warning "config.yml not found"
fi

# Backup environment file
if [ -f ".env" ]; then
    cp .env "$TEMP_DIR/.env"
    log_success "Environment backup completed"
else
    log_warning ".env not found"
fi

# Create final archive
log_info "Creating backup archive..."
cd "$TEMP_DIR"
tar czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" *
cd - > /dev/null

if [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" ]; then
    FILESIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    log_success "Backup archive created: ${BACKUP_NAME}.tar.gz (${FILESIZE})"
else
    log_error "Failed to create backup archive"
    exit 1
fi

# Cleanup old backups
log_info "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "ai-gateway_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

BACKUP_COUNT=$(find "$BACKUP_DIR" -name "ai-gateway_backup_*.tar.gz" | wc -l)
log_info "Total backups: $BACKUP_COUNT"

log_success "Backup completed successfully!"
log_info "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
