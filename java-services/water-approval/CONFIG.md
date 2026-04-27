# SmartWater 后端服务配置说明

## 配置文件结构

```
src/main/resources/
├── application.yaml              # 主配置文件（无敏感信息）
├── application-secrets.yaml      # 敏感配置文件（密码、密钥）
├── application-secrets.yaml.example  # 敏感配置模板
├── db/
│   ├── init.sql                  # 数据库初始化脚本
│   ├── init-db.sh               # Linux/Mac 数据库初始化
│   └── init-db.bat              # Windows 数据库初始化
```

## 快速开始

### 1. 配置敏感信息

```bash
# 复制模板文件
cp src/main/resources/application-secrets.yaml.example \
   src/main/resources/application-secrets.yaml

# 编辑 application-secrets.yaml，填入实际密码
```

**application-secrets.yaml 示例：**
```yaml
spring:
  datasource:
    password: your-mysql-password

storage:
  s3:
    access-key: your-s3-access-key
    secret-key: your-s3-secret-key
```

### 2. 初始化数据库

**方式一：使用脚本**
```bash
# Windows
src/main/resources/db/init-db.bat root your-password

# Linux/Mac
chmod +x src/main/resources/db/init-db.sh
./src/main/resources/db/init-db.sh root your-password
```

**方式二：手动执行**
```bash
mysql -u root -p < src/main/resources/db/init.sql
```

### 3. 启动服务

```bash
./mvnw spring-boot:run
```

### 4. 环境变量（可选）

如果不使用 `application-secrets.yaml`，也可以通过环境变量配置：

```powershell
# Windows PowerShell
$env:MYSQL_PASSWORD="your-password"
$env:S3_ACCESS_KEY="your-access-key"
$env:S3_SECRET_KEY="your-secret-key"
```

```bash
# Linux/Mac
export MYSQL_PASSWORD="your-password"
export S3_ACCESS_KEY="your-access-key"
export S3_SECRET_KEY="your-secret-key"
```

## 安全提醒

⚠️ **application-secrets.yaml 已添加到 .gitignore，请勿手动将其提交到 Git！**

如果误提交敏感信息，请立即：
1. 修改所有密码和密钥
2. 从 Git 历史中移除该文件
3. 强制推送到远程仓库
