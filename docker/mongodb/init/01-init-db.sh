#!/bin/bash
#
# MongoDB Initialization Script for AI Gateway
# This script runs on first container startup to create databases, users, and initial collections
#

set -e

echo "=========================================="
echo "Initializing MongoDB for AI Gateway"
echo "=========================================="

# Get environment variables
MONGO_ROOT_USER="${MONGO_INITDB_ROOT_USERNAME:-admin}"
MONGO_ROOT_PASS="${MONGO_INITDB_ROOT_PASSWORD:-admin123}"
DB_NAME="${MONGODB_DATABASE:-ai_gateway}"
DB_USER="${MONGODB_USERNAME:-ai_gateway_user}"
DB_PASS="${MONGODB_PASSWORD:-user123}"

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to start..."
until mongosh --eval "db.adminCommand('ping')" --quiet; do
  sleep 1
done
echo "MongoDB is ready!"

# Create application database and user
echo "Creating database: $DB_NAME"
echo "Creating user: $DB_USER"

mongosh admin -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASS" <<EOF
use $DB_NAME

db.createUser({
  user: "$DB_USER",
  pwd: "$DB_PASS",
  roles: [
    { role: "readWrite", db: "$DB_NAME" },
    { role: "dbAdmin", db: "$DB_NAME" }
  ]
})

// Create initial collections
db.createCollection("conversations")
db.createCollection("messages")
db.createCollection("api_keys")
db.createCollection("rate_limits")
db.createCollection("cache")
db.createCollection("user_settings")

// Create indexes for performance
db.conversations.createIndex({ "user_id": 1, "created_at": -1 })
db.conversations.createIndex({ "conversation_id": 1 }, { unique: true })
db.messages.createIndex({ "conversation_id": 1, "timestamp": 1 })
db.messages.createIndex({ "message_id": 1 }, { unique: true })
db.api_keys.createIndex({ "key_hash": 1 }, { unique: true })
db.api_keys.createIndex({ "user_id": 1 })
db.rate_limits.createIndex({ "key_id": 1, "window_start": -1 })
db.cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
db.cache.createIndex({ "cache_key": 1 }, { unique: true })
db.user_settings.createIndex({ "user_id": 1 }, { unique: true })

print("Database initialization completed successfully!")
EOF

echo ""
echo "=========================================="
echo "MongoDB initialization complete!"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "=========================================="
