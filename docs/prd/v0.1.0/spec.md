# ModelScope Vision MCP v0.1.0 Spec

## 1. 项目目录

全部项目内容保留在 `mcp/modelscope-vision/` 内。

```text
mcp/modelscope-vision/
  README.md
  config/
    models.example.yaml
  docs/
    prd/
      README.md
      v0.1.0/
        prd.md
        spec.md
  prompts/
    vision_reverse_prompt.zh.md
  src/
  tests/
  state/
```

`src/`、`tests/`、`state/` 在实现阶段创建。`state/` 用于本地运行时计数，不应提交真实用户数据。

路径原则：

- 项目文档、配置、提示词、状态文件和测试资源全部使用相对路径。
- MCP 运行时通过项目根目录解析 `config/`、`prompts/`、`state/` 等内部路径。
- 不在代码和配置中写死 Windows、WSL、Linux 用户目录或 Hermes 运行态绝对路径。
- 部署到不同环境时，由启动命令、环境变量或 Hermes 接入配置提供项目根目录。
- 用户输入的图片路径可以是调用方传入的路径，但 MCP 内部不得把它转换成依赖某台机器的固定路径。

## 2. MCP 工具定义

### 2.1 `analyze_image`

功能：对单张图片进行详细视觉识别，并返回适合 DeepSeek 后续分析的结构化结果。

输入 schema：

```json
{
  "type": "object",
  "properties": {
    "image": {
      "type": "string",
      "description": "图片本地路径、URL 或 base64 数据"
    },
    "question": {
      "type": "string",
      "description": "用户针对图片的可选问题"
    },
    "detail": {
      "type": "string",
      "enum": ["medium", "high", "json"],
      "default": "medium"
    },
    "preferred_model": {
      "type": "string",
      "description": "可选，优先尝试的模型 ID"
    }
  },
  "required": ["image"]
}
```

输出 schema：

```json
{
  "ok": true,
  "model_used": "string",
  "fallback_used": false,
  "attempts": [],
  "deepseek_context": "string",
  "vision": {
    "summary": "string",
    "camera": [],
    "subject": [],
    "environment": [],
    "composition": [],
    "lighting": [],
    "color": [],
    "texture": [],
    "text_detected": [],
    "effects": [],
    "quality": [],
    "uncertainties": []
  }
}
```

## 3. 模型配置

模型配置文件建议为：

```text
config/models.yaml
```

字段：

- `id`：魔搭模型 ID。
- `daily_limit`：每日最多使用次数，可手动修改。
- `priority`：优先级，数字越小越先尝试。
- `enabled`：是否启用。
- `timeout_seconds`：单次调用超时。
- `cooldown_seconds`：非额度类失败后的冷却时间。
- `supports_image_url`：是否支持 URL 图片。
- `supports_base64`：是否支持 base64 图片。

每日计数状态文件：

```text
state/usage.json
```

状态字段：

```json
{
  "date": "2026-05-25",
  "models": {
    "Qwen/xxx": {
      "used_today": 12,
      "blocked_today": false,
      "last_error": "",
      "cooldown_until": ""
    }
  }
}
```

## 4. 模型选择算法

1. 读取模型配置和今日状态。
2. 如果状态日期不是今天，重置所有模型的 `used_today`、`blocked_today` 和 `cooldown_until`。
3. 如果请求包含 `preferred_model`，将其排在第一位，但仍需检查启用状态和额度。
4. 过滤不可用模型：
   - `enabled = false`
   - `used_today >= daily_limit`
   - `blocked_today = true`
   - 当前时间小于 `cooldown_until`
5. 按 `priority` 排序。
6. 逐个调用模型，直到成功或全部失败。

## 5. 失败处理

失败类型：

- `quota_exhausted`：额度耗尽，当天屏蔽该模型。
- `timeout`：设置冷却时间，尝试下一个模型。
- `unsupported_input`：记录配置错误，尝试下一个模型。
- `auth_error`：停止调用并返回认证错误。
- `network_error`：尝试下一个模型。
- `model_error`：尝试下一个模型。

计数规则：

- 只有魔搭请求已经发出，才记录一次 attempt。
- 默认只有成功结果增加 `used_today`。
- 如果平台明确对失败请求也计费，后续通过配置增加 `count_failed_attempts`。
- 如果 API 返回额度耗尽，不增加 `used_today`，但设置 `blocked_today = true`。

## 6. 视觉提示词策略

内置提示词位于：

```text
prompts/vision_reverse_prompt.zh.md
```

提示词目标：

- 让视觉模型输出详细、具体、可验证的视觉描述。
- 保留图像生成反推所需的摄影、镜头、光影、材质、构图、商业气质维度。
- 扩展为通用图像识别，不局限人物摄影。
- 强制区分高置信事实与不确定推测。
- 避免 Markdown、闲聊、过程解释和多版本输出。

## 7. DeepSeek 上下文生成

MCP 不直接把视觉模型原文传给 DeepSeek，而是生成 `deepseek_context`。

默认结构：

```text
图片识别结果：
1. 整体概括：...
2. 主体与关系：...
3. 场景与空间：...
4. 机位、镜头与构图：...
5. 光影、色彩与材质：...
6. 可见文字：...
7. 不确定点：...

用户问题：...

请基于以上视觉识别结果继续分析；不要假设未被识别出的画面细节；如需要判断，请区分已确认事实与推测。
```

长度策略：

- `medium`：600-1200 中文字。
- `high`：1200-2200 中文字。
- `json`：返回结构化 JSON，同时生成简短 `deepseek_context`。

## 8. Hermes 接入原则

实现完成后，再接入 WSL 中的 Hermes。接入前必须确认：

- MCP 安装目标路径。
- 是否需要修改运行态 Hermes 主配置文件。
- 是否需要修改运行态 Hermes 环境变量文件。
- 是否需要重启 `hermes-gateway.service`。
- 回滚方法。

本设计阶段不直接修改运行态 Hermes。

## 9. 验收标准

- 使用一张本地图片能得到详细识别结果。
- 使用一张 URL 图片能得到详细识别结果。
- 模型 A 额度设为 0 时，自动使用模型 B。
- 模型 A 模拟失败时，自动 fallback 到模型 B。
- 返回结果包含 `model_used`、`attempts` 和 `deepseek_context`。
- `deepseek_context` 不是一句话摘要，而是完整视觉证据。
- API token 不出现在日志或错误输出中。
