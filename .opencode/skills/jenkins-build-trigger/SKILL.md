---
name: jenkins-build-trigger
description: Jenkins 构建任务触发器。当你需要触发 Jenkins Pipeline 构建时务必使用此技能，包括列出所有任务、查看任务参数、配置参数并启动构建。适用于用户提到"运行构建"、"触发流水线"、"执行 Jenkins 任务"、"跑一下这个 pipeline"等情况，即使没有明确提及 Jenkins 也应当使用此技能。
---

# Jenkins 构建任务触发器

此技能用于与 Jenkins CI/CD 系统交互，触发和管理 Pipeline 构建任务。

## 何时使用

**当用户提出以下需求时使用：**
- "运行/触发/启动某个构建任务"
- "执行 Jenkins pipeline"
- "跑一下这个项目"
- "构建部署 XXX"
- "运行测试/构建/发布流程"
- 任何涉及持续集成/持续部署的构建请求

**即使用户没有明确说"Jenkins"，只要涉及到项目构建、部署、CI/CD 流程，都应当使用此技能。**

## 工作流程

### 1. 确定要构建的任务

**情况 A：用户未指定具体任务**
```
→ 调用脚本列出所有可用任务
→ 展示任务列表（序号 + 名称）
→ 让用户选择（输入序号或任务名称）
```

**情况 B：用户已指定任务**
```
→ 直接使用该任务名称
→ 验证任务是否存在
```

### 2. 获取并配置参数

**查询任务参数：**
```
→ 调用脚本查询任务的构建参数
→ 展示参数列表（名称、类型、默认值、描述）
→ 让用户确认或修改参数
```

**参数处理规则：**
- **string/text 类型**：直接接受用户输入
- **boolean 类型**：接受 true/false/yes/no/on 等
- **choice 类型**：展示可选值，让用户选择其中一个

**如果任务没有参数：**
```
→ 直接告知用户该任务无需参数
→ 进入确认步骤
```

### 3. 参数验证与匹配

**自动验证规则：**
- 检查用户提供的参数名是否与任务定义的参数名匹配
- 检查 choice 类型参数的值是否在允许范围内
- 对于必填参数（无默认值），确保用户已提供

**参数格式：**
```
--param 参数名 参数值
```

### 4. 最终确认

在向用户展示构建摘要时，必须包含以下信息：

```
待构建任务：[任务名称]
构建参数：
  - [参数 1]: [值 1]
  - [参数 2]: [值 2]
...
是否确认构建？(y/n)
```

**只有在用户明确确认（输入 y/是/confirm 等）后，才执行构建。**

### 5. 执行构建

**调用预置脚本执行：**
```bash
python scripts/run_build.py build \
  --job "[任务名称]" \
  --param "[参数 1]" "[值 1]" \
  --param "[参数 2]" "[值 2]"
```

**输出结果处理：**
- 成功：显示构建编号和访问链接
- 失败：显示错误原因并建议排查方向

## 脚本位置

```
skills/jenkins-build-trigger/scripts/run_build.py
```

## 配置文件配置

使用 `config.json` 文件存储 Jenkins 连接信息：

```json
{
    "jenkins": {
        "url": "http://localhost:8080",
        "username": "你的用户名",
        "token": "你的 API Token"
    }
}
```

**配置文件位置：** `skills/jenkins-build-trigger/config.json`

**必填项说明：**
| 字段 | 说明 | 是否必需 |
|------|------|----------|
| `url` | Jenkins 服务器地址 | 否（默认 http://localhost:8080） |
| `username` | 用户名（API Token 认证方式需要） | 条件必需 |
| `token` | API Token（推荐认证方式） | 条件必需 |

**认证方式：**
- 如果提供了 `username` 和 `token`，则使用 API Token 认证（推荐）
- 如果不提供，则以匿名方式访问（需要 Jenkins 允许匿名访问）

## 命令行用法

### 列出所有任务
```bash
python scripts/run_build.py list [--json]
```

### 查看任务参数
```bash
python scripts/run_build.py params --job "[任务名称]" [--json]
```

### 触发构建
```bash
python scripts/run_build.py build \
  --job "[任务名称]" \
  --param "[参数名]" "[值]" \
  --param "[参数名2]" "[值 2]"
```

## 示例对话流程

### 场景 1：用户想运行构建但未指定任务

**用户：** "帮我跑一下构建"

**技能响应：**
```
找到以下构建任务：

1. frontend-build
2. backend-deploy
3. mobile-release
4. integration-test

请选择要运行的任务（输入序号或名称）：
```

### 场景 2：用户指定了任务且有参数

**用户：** "运行 frontend-build，版本设为 2.0"

**技能响应：**
```
查询到任务 'frontend-build' 的参数：

• VERSION: string (默认：1.0) - 版本号
• ENVIRONMENT: choice (选项：dev, test, prod) - 环境
• DO_BUILD: boolean (默认：true) - 是否执行构建

当前配置：
  - VERSION: 2.0
  - ENVIRONMENT: (未指定，使用默认值)
  - DO_BUILD: (未指定，使用默认值)

请补充缺失的参数或确认使用默认值。
```

### 场景 3：用户完整指定所有参数

**用户：** "触发 backend-deploy，参数：ENV=prod, DEPLOY_VERSION=1.5.0"

**技能响应：**
```
待构建任务：backend-deploy
构建参数：
  - ENV: prod
  - DEPLOY_VERSION: 1.5.0

是否确认构建？(y/n)
```

**用户：** "y"

**技能执行：**
```bash
python scripts/run_build.py build \
  --job "backend-deploy" \
  --param "ENV" "prod" \
  --param "DEPLOY_VERSION" "1.5.0"
```

## 注意事项

1. **安全性**：只在用户明确确认后才会执行构建操作
2. **参数准确性**：严格验证参数名和参数值，避免拼写错误
3. **错误处理**：遇到连接问题或权限问题时，给出清晰的错误提示
4. **构建追踪**：提供构建链接，方便用户查看构建详情

## 依赖

- Python 3.6+
- python-jenkins 库：`pip install python-jenkins`
