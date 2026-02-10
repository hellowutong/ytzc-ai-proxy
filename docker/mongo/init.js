# MongoDB初始化脚本
# 创建数据库和用户

db = db.getSiblingDB('ai_gateway');

// 创建应用用户（可选，如果使用root用户则不需要）
db.createUser({
  user: "app_user",
  pwd: "app_password",
  roles: [
    { role: "readWrite", db: "ai_gateway" }
  ]
});

// 创建集合（显式创建以便设置验证规则）
db.createCollection('conversations', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["virtual_model", "messages", "created_at"],
      properties: {
        virtual_model: {
          bsonType: "string",
          description: "虚拟模型名称"
        },
        messages: {
          bsonType: "array",
          description: "消息列表"
        },
        created_at: {
          bsonType: "date",
          description: "创建时间"
        }
      }
    }
  }
});

db.createCollection('knowledge_docs');
db.createCollection('media_files');
db.createCollection('rss_subscriptions');
db.createCollection('rss_articles');
db.createCollection('operation_logs');

// 创建索引
db.conversations.createIndex({ "virtual_model": 1, "updated_at": -1 });
db.conversations.createIndex({ "updated_at": -1 });
db.knowledge_docs.createIndex({ "virtual_model": 1, "source": 1 });
db.knowledge_docs.createIndex({ "vectorized": 1 });
db.media_files.createIndex({ "type": 1, "status": 1 });
db.rss_articles.createIndex({ "subscription_id": 1, "fetched_at": -1 });
db.operation_logs.createIndex({ "timestamp": -1 });

print('Database initialization completed!');
