// MongoDB 初始化脚本
// 创建数据库和用户

// 切换到目标数据库
db = db.getSiblingDB('tw_ai_proxy');

// 创建管理员用户
db.createUser({
    user: 'admin',
    pwd: 'password123',
    roles: [
        { role: 'readWrite', db: 'tw_ai_proxy' },
        { role: 'dbAdmin', db: 'tw_ai_proxy' }
    ]
});

// 创建集合并添加索引
db.createCollection('sessions');
db.sessions.createIndex({ "proxy_key": 1 });
db.sessions.createIndex({ "created_at": -1 });
db.sessions.createIndex({ "status": 1 });

db.createCollection('skills');
db.skills.createIndex({ "base_id": 1 }, { unique: true });
db.skills.createIndex({ "created_at": -1 });

db.createCollection('connections');
db.connections.createIndex({ "proxy_key": 1 }, { unique: true });
db.connections.createIndex({ "name": 1 });

db.createCollection('vectors');
db.vectors.createIndex({ "session_id": 1 });
db.vectors.createIndex({ "skill_id": 1 });
db.vectors.createIndex({ "collection_name": 1, "session_id": 1 });

db.createCollection('backups');
db.backups.createIndex({ "created_at": -1 });
db.backups.createIndex({ "backup_type": 1 });

db.createCollection('baseskills');
db.baseskills.createIndex({ "base_id": 1 }, { unique: true });

db.createCollection('audit_logs');
db.audit_logs.createIndex({ "event": 1 });
db.audit_logs.createIndex({ "user_id": 1 });
db.audit_logs.createIndex({ "created_at": -1 });

// 插入初始测试数据
db.sessions.insertMany([
    {
        proxy_key: "tw-test-session-001",
        status: "active",
        messages: [
            { role: "user", content: "测试消息", timestamp: new Date().toISOString() }
        ],
        summary: "测试会话",
        created_at: new Date().toISOString()
    }
]);

db.skills.insertMany([
    {
        base_id: "test-skill-001",
        active_version_id: 1,
        versions: [
            {
                version_id: 1,
                status: "published",
                created_at: new Date().toISOString(),
                created_by: "test-user",
                source_session_id: "test-session-001",
                change_reason: "初始版本",
                content: "# 测试技能\n\n这是一个测试技能"
            }
        ],
        created_at: new Date().toISOString()
    }
]);

print("MongoDB 初始化完成!");
print("数据库: tw_ai_proxy");
print("用户: admin / password123");
print("集合: sessions, skills, connections, vectors, backups, baseskills, audit_logs");
