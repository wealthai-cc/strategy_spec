# 部署指南

## 构建配置

### 开发环境

```bash
npm run dev
```

访问 http://localhost:5173

### 生产环境构建

```bash
npm run build
```

构建产物在 `dist/` 目录，包含：
- `index.html` - 入口文件
- `assets/` - 静态资源（JS、CSS）
- 其他静态文件

## 部署方式

### 方式 1：静态文件服务器

#### Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 支持 JSON 数据文件
    location /data {
        alias /path/to/data/files;
        add_header Access-Control-Allow-Origin *;
    }
}
```

#### Apache

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /path/to/dist

    <Directory /path/to/dist>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # 支持 JSON 数据文件
    Alias /data /path/to/data/files
    <Directory /path/to/data/files>
        Require all granted
    </Directory>
</VirtualHost>
```

### 方式 2：CDN 部署

1. 构建项目：`npm run build`
2. 上传 `dist/` 目录到 CDN
3. 配置 CDN 支持 SPA 路由（所有请求返回 `index.html`）

### 方式 3：Docker 部署

#### Dockerfile

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 支持 JSON 数据文件（可选）
    location /data {
        alias /data;
        add_header Access-Control-Allow-Origin *;
    }
}
```

#### 构建和运行

```bash
docker build -t strategy-visualization .
docker run -d -p 8080:80 \
  -v /path/to/data:/data \
  strategy-visualization
```

### 方式 4：GitHub Pages

1. 安装 `gh-pages`：`npm install --save-dev gh-pages`
2. 添加部署脚本到 `package.json`：

```json
{
  "scripts": {
    "deploy": "npm run build && gh-pages -d dist"
  }
}
```

3. 运行：`npm run deploy`

## 环境变量

创建 `.env.production`：

```env
VITE_API_BASE_URL=https://api.example.com
VITE_DATA_BASE_URL=https://data.example.com
```

在代码中使用：

```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

## 性能优化

### 代码分割

已配置 `vite.config.ts` 进行代码分割：
- `react-vendor.js` - React 相关代码
- `charts-vendor.js` - TradingView Charts 代码
- `index.js` - 应用代码

### 资源压缩

构建时自动压缩：
- JS 文件使用 Terser 压缩
- CSS 文件自动压缩
- 图片资源优化

### 缓存策略

建议配置 HTTP 缓存头：

```nginx
location /assets {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 安全配置

### HTTPS

使用 Let's Encrypt 配置 HTTPS：

```bash
certbot --nginx -d your-domain.com
```

### CORS

如果从不同域加载数据，配置 CORS：

```nginx
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
add_header Access-Control-Allow-Headers "Content-Type";
```

## 监控和日志

### 错误监控

集成 Sentry 或其他错误监控服务：

```typescript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-dsn",
  environment: "production",
});
```

### 访问日志

Nginx 访问日志：

```nginx
access_log /var/log/nginx/strategy-visualization.access.log;
error_log /var/log/nginx/strategy-visualization.error.log;
```

## 更新流程

1. 构建新版本：`npm run build`
2. 备份当前版本
3. 部署新版本到服务器
4. 验证功能正常
5. 如有问题，回滚到备份版本

