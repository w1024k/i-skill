---
name: jenkins-build-skill
description: 当用户要调用 Jenkins 构建任务、查看 Jenkins 全量任务、查询 pipeline 参数、按任务名或参数语义匹配并执行构建时使用。支持先列出所有任务供用户按序号或名称选择，也支持用户直接给出任务和参数后结合脚本结果做匹配。 
---

# Jenkins 构建 Skill

这个 skill 用于通过预置 Python 脚本调用 Jenkins 任务，适合 `opencode`、`codex`、`claude code`、`trae` 等工具直接复用。



## 文件位置
- 脚本再SKILL.md同级目录下
- 使用opencode时,到文件夹.opencode/skills/jenkins-build-skill/寻找文件
- `SKILL.md`：当前 skill 的工作说明。
- `config.json`：Jenkins 地址、账号密码、任务别名/备注、参数别名/备注配置。
- `script/base.py`：初始化 Jenkins 连接、读取配置、遍历全部任务、公共匹配函数。
- `script/list_jobs.py`：递归列出所有任务，支持按任务名、别名、备注匹配。
- `script/get_job_params.py`：读取指定任务的 pipeline 参数，展示默认值、描述、可选项、别名、备注。
- `script/build_job.py`：触发 Jenkins 构建。

说明里一律使用上述固定路径，避免不同工具找不到脚本或配置文件。

## 使用前检查

先确认运行环境已安装 `python-jenkins`，否则这些脚本无法连接 Jenkins。

先看 `config.json` 是否已配置：

- `jenkins_url`
- `username`
- `password`

只要任一字段为空，就不要继续调用 Jenkins，而是直接提醒用户先补全 `config.json`。

## 支持的命令行环境

本 skill 支持以下命令行环境：

- **Linux/macOS**: bash、zsh 等
- **Windows**: PowerShell、CMD

在 Windows 环境下运行时：

- PowerShell 中使用 `python` 或 `python3` 命令
- CMD 中使用 `python` 或 `python3` 命令
- 路径分隔符自动兼容（脚本内部已处理）

`config.json` 还支持两类增强配置：

- `job_aliases`
- `param_aliases`

它们用于补充任务别名、任务备注、参数别名、参数备注，便于展示和语义匹配。

## 工作流程

### 1. 用户没说要构建哪个任务

先执行：

```bash
# Linux/macOS
python3 jenkins-build-skill/script/list_jobs.py

# Windows PowerShell/CMD
python jenkins-build-skill\script\list_jobs.py
```

要求：

- 遍历每一级文件夹，列出全部 Jenkins 任务。
- 展示任务序号、任务全名、别名、备注。
- 让用户通过“序号”或“名称”选择任务。

### 2. 用户直接说了任务名，但表达不完全标准

先执行：

```bash
# Linux/macOS
python3 jenkins-build-skill/script/list_jobs.py --query "用户原话里的任务描述"

# Windows PowerShell
python jenkins-build-skill\script\list_jobs.py --query "用户原话里的任务描述"

# Windows CMD
python jenkins-build-skill\script\list_jobs.py --query "用户原话里的任务描述"
```

**Windows 参数说明**：
- PowerShell 和 CMD 中，带空格的字符串参数需要用双引号包裹
- 如果参数中包含特殊字符（如 `&`、`|`、`<`、`>`），需要使用反引号（PowerShell）或 `^`（CMD）转义

做法：

- 结合大模型语义理解，从用户原话中抽取候选任务描述。
- 用脚本返回的任务名、别名、备注做匹配。
- 如果匹配结果不唯一，给用户展示候选项并要求确认。
- 不要跳过脚本，最终匹配必须以脚本结果为准。

### 3. 确定任务后查询参数

执行：

```bash
# Linux/macOS
python3 jenkins-build-skill/script/get_job_params.py --job "folder-a/example-pipeline"

# Windows PowerShell/CMD
python jenkins-build-skill\script\get_job_params.py --job "folder-a/example-pipeline"
```

要求：

- 展示参数序号、参数名、类型、默认值、描述、可选项。
- 如果参数有别名或备注，也要一起展示。
- 让用户按参数名或序号填写。

如果用户已经直接说了参数，也不能直接构建，要先查询参数并校验匹配。

### 4. 用户直接说了参数，按语义匹配参数

执行：

```bash
# Linux/macOS
python3 jenkins-build-skill/script/get_job_params.py --job "folder-a/example-pipeline" --query "用户原话里的参数描述"

# Windows PowerShell
python jenkins-build-skill\script\get_job_params.py --job "folder-a/example-pipeline" --query "用户原话里的参数描述"

# Windows CMD
python jenkins-build-skill\script\get_job_params.py --job "folder-a/example-pipeline" --query "用户原话里的参数描述"
```

**Windows 参数说明**：
- `--job` 参数通常不需要特殊处理
- `--query` 参数如果包含空格或特殊字符，需要用双引号包裹

做法：

- 先让大模型从用户话术中提取参数意图和值。
- 再用脚本返回的参数名、别名、备注、描述做匹配。
- 如果一个描述可能对应多个参数，必须让用户确认。
- 如果参数不在脚本返回的列表中，不要自行猜测为有效参数。

### 5. 构建前强制确认

在真正调用构建前，必须明确写出：

- 任务名称
- 最终参数清单

然后让用户确认。

只有用户明确确认后，才能执行：

**方式一：使用 `--param` 参数（推荐用于 Windows PowerShell/CMD）**

```bash
# Linux/macOS
python3 jenkins-build-skill/script/build_job.py --job "folder-a/example-pipeline" --param ENV=test --param VERSION=1.0.0

# Windows PowerShell
python jenkins-build-skill\script\build_job.py --job "folder-a/example-pipeline" --param ENV=test --param VERSION=1.0.0

# Windows CMD
python jenkins-build-skill\script\build_job.py --job "folder-a/example-pipeline" --param ENV=test --param VERSION=1.0.0
```

**方式二：使用 `--params-json` 参数（推荐用于 Linux/macOS）**

```bash
# Linux/macOS
python3 jenkins-build-skill/script/build_job.py --job "folder-a/example-pipeline" --params-json '{"ENV":"test","VERSION":"1.0.0"}'

# Windows PowerShell（单引号，内部双引号不转义）
python jenkins-build-skill\script\build_job.py --job "folder-a/example-pipeline" --params-json '{"ENV":"test","VERSION":"1.0.0"}'

# Windows CMD（双引号 + 转义）
python jenkins-build-skill\script\build_job.py --job "folder-a/example-pipeline" --params-json "{\"ENV\":\"test\",\"VERSION\":\"1.0.0\"}"
```

**方式三：使用 `--params-file` 参数（适用于复杂 JSON）**

```bash
# 1. 创建临时 JSON 文件
echo '{"ENV":"test","VERSION":"1.0.0"}' > params.json

# 2. 执行构建
python jenkins-build-skill\script\build_job.py --job "folder-a/example-pipeline" --params-file params.json

# 3. 删除临时文件（可选）
del params.json
```

**Windows 参数传递说明**：

- **推荐方案**：在 Windows 下使用 `--param` 参数，无需转义，简单可靠
  - 示例：`--param ENV=test --param MESSAGE="hello world"`
  - 支持多个 `--param` 参数
  
- **PowerShell**: 
  - 使用单引号包裹 JSON 字符串，内部双引号**不需要**转义：`'{"KEY":"VALUE"}'`
  - 示例：`--params-json '{"MESSAGE":"hello world"}'`
  - 注意：某些环境下 PowerShell 可能会移除引号，如遇问题请使用 `--param` 或 `--params-file`
  
- **CMD**: 
  - 使用双引号包裹 JSON 字符串，内部双引号需要转义：`"{\"KEY\":\"VALUE\"}"`
  - 示例：`--params-json "{\"MESSAGE\":\"hello world\"}"`

如果用户没有确认，不允许直接触发构建。

## 输出要求

和用户交互时，优先用中文，至少包含：

- 已选任务名称
- 任务别名或备注（如果存在）
- 参数名称、参数值、参数别名或备注（如果存在）
- 最终确认语句

如果脚本返回错误，也要把错误直接告诉用户，尤其是以下场景：

- `config.json` 未配置
- 未安装 `python-jenkins`
- 任务不存在
- 参数不存在
- Jenkins 连接失败
- 构建触发失败

## 约束

- 不要绕过脚本直接调用 Jenkins API。
- 不要在用户未确认前执行 `build_job.py`。
- 任务和参数匹配都必须以脚本查询结果为准。
- 当匹配不唯一时，必须要求用户确认，不要擅自选择。
