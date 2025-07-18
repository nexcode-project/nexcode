// MongoDB 初始化脚本
// 用于创建数据库、集合和索引

// 切换到协作文档数据库
db = db.getSiblingDB('nexcode_docs');

// 创建文档集合
db.createCollection('documents');
db.createCollection('document_versions');
db.createCollection('document_collaborators');
db.createCollection('document_comments');
db.createCollection('document_sessions');

// 创建索引
db.documents.createIndex({ "owner_id": 1 });
db.documents.createIndex({ "title": "text", "content": "text" });
db.documents.createIndex({ "created_at": -1 });
db.documents.createIndex({ "updated_at": -1 });

db.document_versions.createIndex({ "document_id": 1, "version_number": -1 });
db.document_versions.createIndex({ "changed_by": 1 });

db.document_collaborators.createIndex({ "document_id": 1 });
db.document_collaborators.createIndex({ "user_id": 1 });
db.document_collaborators.createIndex({ "document_id": 1, "user_id": 1 }, { unique: true });

db.document_comments.createIndex({ "document_id": 1 });
db.document_comments.createIndex({ "user_id": 1 });
db.document_comments.createIndex({ "created_at": -1 });

db.document_sessions.createIndex({ "document_id": 1 });
db.document_sessions.createIndex({ "user_id": 1 });
db.document_sessions.createIndex({ "session_id": 1 }, { unique: true });

// 创建应用用户（可选）
db.createUser({
  user: "nexcode_user",
  pwd: "nexcode_pass",
  roles: [
    { role: "readWrite", db: "nexcode_docs" }
  ]
});

print("✅ MongoDB 初始化完成");
print("📊 数据库: nexcode_docs");
print("📁 集合: documents, document_versions, document_collaborators, document_comments, document_sessions");
print("🔍 索引: 已创建必要的索引");
print("👤 用户: nexcode_user (可选)"); 