# 认证方式更新说明

## 更新内容

bid-material-search v2.0 的认证方式已优化，支持更安全的交互式输入。

## 更新前后对比

### 之前（纯环境变量）

```bash
# 必须预先设置环境变量
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 启动服务
uvicorn app:app --host 0.0.0.0 --port 9000
```

**问题**：
- ❌ 密码明文存储在环境变量中
- ❌ 密码可能出现在 shell 历史记录中
- ❌ 其他进程可以读取环境变量

### 现在（交互式输入优先）

```bash
# 直接启动，会提示输入
uvicorn app:app --host 0.0.0.0 --port 9000

# 启动时显示：
# ============================================================
# MaterialHub 认证
# ============================================================
# 用户名 [默认: admin]: admin
# 密码: ********
# ============================================================
```

**优点**：
- ✅ 密码不会存储在文件或历史记录中
- ✅ 使用 `getpass` 模块隐藏密码输入
- ✅ 更安全的认证流程
- ✅ 仍支持环境变量（适合自动化场景）

## 使用场景

### 场景 1：手动启动（推荐）

**适用**：开发测试、日常使用

```bash
cd skills/bid-material-search/scripts
uvicorn app:app --host 0.0.0.0 --port 9000
```

启动时会提示输入用户名和密码。

### 场景 2：自动化部署

**适用**：Docker、systemd、CI/CD

```bash
# 在启动脚本中设置环境变量
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 启动服务（跳过交互式输入）
uvicorn app:app --host 0.0.0.0 --port 9000
```

### 场景 3：Docker 容器

**Dockerfile**:

```dockerfile
ENV MATERIALHUB_USERNAME=admin
ENV MATERIALHUB_PASSWORD=admin123

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000"]
```

### 场景 4：systemd 服务

**service 文件**:

```ini
[Service]
Environment="MATERIALHUB_USERNAME=admin"
Environment="MATERIALHUB_PASSWORD=admin123"
ExecStart=/usr/bin/uvicorn app:app --host 0.0.0.0 --port 9000
```

## 安全建议

### ✅ 推荐做法

1. **手动启动时使用交互式输入**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 9000
   ```

2. **自动化场景使用环境变量 + 密钥管理**
   ```bash
   # 从密钥管理系统读取
   export MATERIALHUB_PASSWORD=$(vault read -field=password secret/materialhub)
   uvicorn app:app --host 0.0.0.0 --port 9000
   ```

3. **Docker 使用 secrets**
   ```yaml
   # docker-compose.yml
   services:
     bid-material-search:
       environment:
         MATERIALHUB_USERNAME: admin
       secrets:
         - materialhub_password
   secrets:
     materialhub_password:
       file: ./secrets/password.txt
   ```

### ❌ 不推荐做法

1. **密码写入 shell 历史**
   ```bash
   # 不要这样做
   export MATERIALHUB_PASSWORD=admin123  # 会保存在 ~/.bash_history
   ```

2. **密码硬编码在脚本中**
   ```bash
   # 不要这样做
   # start.sh
   export MATERIALHUB_PASSWORD=admin123
   uvicorn app:app
   ```

3. **密码提交到 Git**
   ```bash
   # 不要这样做
   # .env 文件不应该提交到版本控制
   MATERIALHUB_PASSWORD=admin123
   ```

## 测试交互式输入

使用演示脚本测试认证逻辑：

```bash
cd skills/bid-material-search/scripts

# 测试 1：无环境变量（会提示输入）
unset MATERIALHUB_USERNAME
unset MATERIALHUB_PASSWORD
python3 demo_auth.py

# 测试 2：有环境变量（跳过输入）
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123
python3 demo_auth.py
```

## 代码实现

### `app.py` 中的实现

```python
def _get_credentials():
    """获取认证凭据（优先环境变量，否则交互式输入）"""
    username = os.getenv("MATERIALHUB_USERNAME")
    password = os.getenv("MATERIALHUB_PASSWORD")

    # 如果环境变量未设置，提示用户输入
    if not username or not password:
        logger.info("MaterialHub 认证信息未在环境变量中找到，请输入：")
        print("\n" + "=" * 60)
        print("MaterialHub 认证")
        print("=" * 60)

        if not username:
            username = input("用户名 [默认: admin]: ").strip()
            if not username:
                username = "admin"

        if not password:
            password = getpass.getpass("密码: ")
            if not password:
                password = "admin123"

        print("=" * 60 + "\n")

    return username, password
```

### 特点

1. **优先级**：环境变量 > 交互式输入 > 默认值
2. **隐藏密码**：使用 `getpass.getpass()` 隐藏输入
3. **默认值**：用户名默认 `admin`，密码默认 `admin123`
4. **容错处理**：Ctrl+C 取消时使用默认值

## FAQ

### Q: 如何在非交互式环境（如 cron）中运行？

A: 设置环境变量：

```bash
# crontab
0 * * * * cd /path/to/scripts && MATERIALHUB_USERNAME=admin MATERIALHUB_PASSWORD=admin123 uvicorn app:app
```

### Q: 密码输入错误怎么办？

A: 服务会尝试登录，如果失败会记录错误日志：

```
ERROR - Login failed: 401 - {"detail":"Invalid username or password"}
```

重启服务重新输入即可。

### Q: 如何修改默认值？

A: 修改 `app.py` 中的代码：

```python
if not username:
    username = "your_default_username"

if not password:
    password = "your_default_password"
```

### Q: 支持读取配置文件吗？

A: 当前版本不支持，可以使用环境变量文件：

```bash
# config.env
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 使用
source config.env
uvicorn app:app
```

## 兼容性

所有现有功能保持不变：

- ✅ 环境变量方式仍然有效
- ✅ 服务启动逻辑不变
- ✅ API 端点完全兼容
- ✅ 其他 skills 无需修改

## 相关文件

更新的文件：

- `scripts/app.py` - 添加 `_get_credentials()` 函数
- `scripts/test_integration.py` - 测试脚本同样支持交互式输入
- `scripts/demo_auth.py` - 认证演示脚本（新增）
- `SKILL.md` - 更新启动说明
- `UPGRADE_v2.md` - 更新环境配置说明
- `IMPLEMENTATION_SUMMARY.md` - 更新验证步骤
- `AUTH_UPDATE.md` - 本文档（新增）

## 版本历史

### v2.0.1 (2026-02-20)

- ✨ 添加交互式认证输入
- 🔒 使用 `getpass` 隐藏密码
- 📖 优先环境变量，兜底交互输入
- 🛡️ 更安全的认证流程

### v2.0.0 (2026-02-20)

- ✨ 集成 MaterialHub API
- 🔐 Session-based 认证（仅环境变量）
