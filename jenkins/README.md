# Jenkins Docker Compose 配置说明

## 概述

此 `docker-compose.yml` 文件用于在本地环境中快速启动 Jenkins，适用于测试和开发目的。

## 服务配置

### jenkins 服务

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 镜像 | `jenkins/jenkins:latest` | 使用最新官方 Jenkins 镜像 |
| 容器名 | `jenkins` | 容器名称便于管理 |
| 重启策略 | `unless-stopped` | 除非手动停止，否则自动重启 |

## 端口映射

| 主机端口 | 容器端口 | 用途 |
|----------|----------|------|
| 8080 | 8080 | Jenkins Web 界面访问 |
| 50000 | 50000 | Agent 连接端口（用于分布式构建） |

**访问地址**: http://localhost:8080

## 数据卷配置

### jenkins_home
- **路径**: `/var/jenkins_home` (容器内)
- **用途**: 持久化存储 Jenkins 所有数据，包括：
  - 用户配置
  - Job/任务定义
  - 插件数据
  - Build 历史记录

### docker_sock
- **路径**: `/var/run/docker.sock` (宿主机) → `/var/run/docker.sock` (容器内)
- **用途**: 允许 Jenkins 在容器内执行 Docker 命令，支持构建 Docker 镜像和运行容器

### docker_bins
- **路径**: `/usr/local/bin/docker` (宿主机) → `/usr/local/bin/docker` (容器内)
- **用途**: 挂载 Docker CLI 工具，方便 Jenkins Pipeline 调用

## 环境变量

```yaml
JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF-8
```

设置 Java 编码为 UTF-8，避免中文乱码问题。

## 网络配置

- **网络类型**: bridge
- **网络名称**: jenkins_network
- **用途**: 隔离的网络环境，便于与其他服务通信

## 使用方法

### 1. 启动 Jenkins

```bash
docker-compose up -d
```

### 2. 查看运行状态

```bash
docker-compose ps
```

### 3. 查看日志

```bash
docker-compose logs -f jenkins
```

### 4. 获取初始管理员密码

首次启动后，通过以下命令获取密码：

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### 5. 停止 Jenkins

```bash
docker-compose down
```

如需删除数据卷（慎用）：

```bash
docker-compose down -v
```

### 6. 进入容器

```bash
docker exec -it jenkins sh
```

## 初始化步骤

1. 访问 http://localhost:8080
2. 输入初始管理员密码（参考上文）
3. 选择安装建议的插件或自定义选择
4. 创建第一个管理员账户
5. 保存并完成初始化

## 注意事项

- 数据卷 `jenkins_home` 会持久化存储所有数据，重新创建容器不会丢失
- 如需重置 Jenkins，删除数据卷即可：`docker-compose down -v`
- 生产环境建议使用更安全的认证方式和备份策略
- 本地测试环境默认无外部防火墙限制，注意安全性

## 常见问题

### Q: 无法访问 Jenkins 页面？
A: 检查端口 8080 是否被占用：`netstat -ano | findstr :8080`

### Q: Jenkins 启动失败？
A: 查看日志：`docker-compose logs jenkins`

### Q: 如何升级 Jenkins？
A: 拉取新镜像后重建：`docker-compose pull && docker-compose up -d`
