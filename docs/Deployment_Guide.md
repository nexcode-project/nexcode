# 协作文档平台部署指南

## 1. 环境要求

### 1.1 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **存储**: 100GB以上SSD
- **网络**: 100Mbps以上带宽

### 1.2 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Nginx**: 1.18+ (可选)

## 2. 快速部署

### 2.1 使用Docker Compose
```bash
# 1. 克隆项目
git clone <repository-url>
cd collaborative-docs

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要参数

# 3. 启动服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec backend python scripts/init_db.py

# 5. 检查服务状态
docker-compose ps
```

### 2.2 环境变量配置
```bash
# .env 文件示例
# 数据库配置
MONGODB_URL=mongodb://mongodb:27017/collaborative_docs
REDIS_URL=redis://redis:6379/0

# API配置
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key

# 服务配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 邮件配置（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 3. 生产环境部署

### 3.1 Nginx配置
```nginx
# /etc/nginx/sites-available/collaborative-docs
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /api/v1/documents/*/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 3.2 SSL配置
```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3.3 防火墙配置
```bash
# UFW配置
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 4. 数据库配置

### 4.1 MongoDB配置
```yaml
# docker-compose.yml MongoDB配置
mongodb:
  image: mongo:5.0
  restart: always
  environment:
    MONGO_INITDB_ROOT_USERNAME: admin
    MONGO_INITDB_ROOT_PASSWORD: password
    MONGO_INITDB_DATABASE: collaborative_docs
  volumes:
    - mongodb_data:/data/db
    - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js
  ports:
    - "27017:27017"
```

### 4.2 Redis配置
```yaml
# docker-compose.yml Redis配置
redis:
  image: redis:6.0-alpine
  restart: always
  command: redis-server --appendonly yes --requirepass password
  volumes:
    - redis_data:/data
  ports:
    - "6379:6379"
```

### 4.3 数据备份
```bash
# MongoDB备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mongodb"
mkdir -p $BACKUP_DIR

docker exec mongodb mongodump \
  --host localhost:27017 \
  --db collaborative_docs \
  --out /tmp/backup

docker cp mongodb:/tmp/backup $BACKUP_DIR/$DATE
```

## 5. 监控和日志

### 5.1 日志配置
```yaml
# docker-compose.yml 日志配置
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  frontend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5.2 健康检查
```yaml
# docker-compose.yml 健康检查
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### 5.3 监控脚本
```bash
#!/bin/bash
# monitor.sh - 服务监控脚本

check_service() {
    local service=$1
    local url=$2
    
    if curl -f -s $url > /dev/null; then
        echo "✅ $service is running"
    else
        echo "❌ $service is down"
        # 发送告警通知
        # send_alert "$service is down"
    fi
}

check_service "Backend API" "http://localhost:8000/health"
check_service "Frontend" "http://localhost:3000"
```

## 6. 性能优化

### 6.1 数据库优化
```javascript
// MongoDB索引创建
db.documents.createIndex({ "owner_id": 1 })
db.documents.createIndex({ "collaborators.user_id": 1 })
db.documents.createIndex({ "created_at": -1 })
db.documents.createIndex({ "title": "text", "content": "text" })

db.document_versions.createIndex({ "document_id": 1, "version_number": -1 })
```

### 6.2 缓存策略
```python
# Redis缓存配置
CACHE_CONFIG = {
    "document_cache_ttl": 3600,  # 1小时
    "user_session_ttl": 86400,   # 24小时
    "online_users_ttl": 300,     # 5分钟
}
```

### 6.3 CDN配置
```nginx
# 静态资源CDN
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header X-Content-Type-Options nosniff;
}
```

## 7. 安全配置

### 7.1 环境变量安全
```bash
# 使用Docker secrets
echo "your-secret-key" | docker secret create app_secret_key -
echo "your-db-password" | docker secret create db_password -
```

### 7.2 网络安全
```yaml
# docker-compose.yml 网络隔离
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  frontend:
    networks:
      - frontend
  
  backend:
    networks:
      - frontend
      - backend
  
  mongodb:
    networks:
      - backend
```

### 7.3 访问控制
```nginx
# Nginx访问限制
# 限制API访问频率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://localhost:8000;
}
```

## 8. 故障排查

### 8.1 常见问题
```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 检查网络连接
docker-compose exec backend ping mongodb
docker-compose exec backend ping redis

# 检查数据库连接
docker-compose exec mongodb mongo --eval "db.adminCommand('ismaster')"
```

### 8.2 性能诊断
```bash
# 检查资源使用
docker stats

# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查网络连接
netstat -tulpn | grep :8000
```

## 9. 升级和维护

### 9.1 版本升级
```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取新版本
git pull origin main

# 3. 更新镜像
docker-compose pull

# 4. 重启服务
docker-compose up -d

# 5. 运行迁移
docker-compose exec backend python scripts/migrate.py
```

### 9.2 定期维护
```bash
# 清理Docker资源
docker system prune -f

# 清理日志文件
find /var/log -name "*.log" -mtime +30 -delete

# 数据库维护
docker-compose exec mongodb mongo --eval "db.runCommand({compact: 'documents'})"
```

## 10. 扩展部署

### 10.1 负载均衡
```nginx
# Nginx负载均衡配置
upstream backend_servers {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend_servers;
    }
}
```

### 10.2 集群部署
```yaml
# docker-swarm.yml
version: '3.8'
services:
  backend:
    image: collaborative-docs-backend
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```