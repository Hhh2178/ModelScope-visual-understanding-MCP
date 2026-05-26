# ModelScope Visual Understanding MCP

An MCP server that adds detailed image understanding to AI agents through the ModelScope OpenAI-compatible API.

It is designed for Hermes Agent, but it can be used by any MCP client that supports stdio servers.

## What It Does

- Analyzes a single image from a URL, local path, data URL, or base64 string.
- Uses ModelScope multimodal models through `https://api-inference.modelscope.cn/v1`.
- Tracks per-model daily call quotas locally.
- Skips exhausted models and falls back automatically when a model fails.
- Supports ModelScope streaming responses.
- Resizes oversized local images so the longest side is at most `2048px`.
- Returns high-density visual evidence for downstream reasoning models.
- Avoids duplicating MCP structured output by returning a JSON string payload.

## Default Model Order

The default `config/models.yaml` contains:

| Priority | Model | Daily limit |
| --- | --- | --- |
| 1 | `Qwen/Qwen3-VL-8B-Instruct` | 50 |
| 2 | `moonshotai/Kimi-K2.5` | 50 |
| 3 | `Qwen/Qwen3.5-35B-A3B` | 50 |
| 4 | `Qwen/Qwen3.5-27B` | 50 |
| 5 | `Qwen/Qwen3.5-397B-A17B` | 50 |
| 6 | `Qwen/Qwen3.5-122B-A10B` | 50 |

You can edit `config/models.yaml` to change model IDs, priority, daily limits, timeouts, and whether streaming is enabled.

## Installation

```bash
git clone https://github.com/Hhh2178/ModelScope-visual-understanding-MCP.git
cd ModelScope-visual-understanding-MCP
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Set your ModelScope token:

```bash
export MODELSCOPE_TOKEN="your-modelscope-token"
```

Run a smoke test:

```bash
PYTHONPATH=src .venv/bin/python -m modelscope_vision_mcp.smoke_test \
  --preferred-model Qwen/Qwen3-VL-8B-Instruct \
  --image https://modelscope.oss-cn-beijing.aliyuncs.com/demo/images/audrey_hepburn.jpg \
  --question "Describe this image in detail."
```

## Hermes Agent Setup

Use the included launcher script:

```bash
chmod +x scripts/run-server.sh
hermes mcp add modelscope-vision \
  --command "$(pwd)/scripts/run-server.sh" \
  --env MODELSCOPE_TOKEN='${MODELSCOPE_TOKEN}'
```

Then restart Hermes or start a new session so it can discover the MCP tool.

The registered tool name in Hermes is typically:

```text
mcp_modelscope_vision_analyze_image
```

For a more complete runtime install checklist, see [docs/hermes-install.md](docs/hermes-install.md).

## MCP Tool

### `analyze_image`

Input:

```json
{
  "image": "https://example.com/image.jpg",
  "question": "What is happening in this image?",
  "detail": "medium",
  "preferred_model": "Qwen/Qwen3-VL-8B-Instruct"
}
```

Output is a JSON string with:

- `ok`
- `model_used`
- `fallback_used`
- `attempts`
- `deepseek_context`
- `vision.summary`
- `vision.camera`
- `vision.subject`
- `vision.environment`
- `vision.composition`
- `vision.lighting`
- `vision.color`
- `vision.texture`
- `vision.text_detected`
- `vision.style`
- `vision.effects`
- `vision.quality`
- `vision.uncertainties`

## Prompt Strategy

The built-in prompt is intentionally detailed. It asks the vision model to extract camera, subject, environment, composition, lighting, color, texture, visible text, style, effects, quality, and uncertainty.

The prompt is stored at:

```text
prompts/vision_reverse_prompt.zh.md
```

Current prompt size is about `2,038` characters. It is sent to the ModelScope vision model. It does not directly consume the downstream reasoning model context unless you pass the prompt itself onward.

The downstream context cost mainly comes from the returned `deepseek_context` and JSON result. This project returns a JSON string instead of structured MCP content to avoid duplicating the same payload in clients that include both text content and `structuredContent`.

If your Hermes/FastMCP version still duplicates `result` into `structuredContent.result`, see [patches/hermes-mcp-dedupe.patch](patches/hermes-mcp-dedupe.patch).

## Image Size Handling

For local files, images larger than the model limit are resized before upload.

The current policy:

- If width and height are both `<= 2048`, keep the image unchanged.
- If either side is larger than `2048`, resize proportionally so the longest side is `2048`.
- Preserve aspect ratio.

Examples:

- `1256 x 2760` -> approximately `932 x 2048`
- `3000 x 1000` -> approximately `2048 x 683`

## Development

Install development dependencies:

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest -q
```

Run the portability check:

```bash
PYTHONPATH=src python -m modelscope_vision_mcp.portability_check
```

## Security

- Never commit `MODELSCOPE_TOKEN`.
- Runtime state is stored in `state/` and ignored by git.
- `config/models.yaml` contains model IDs and quota settings only, no secrets.

See [SECURITY.md](SECURITY.md).

## License

MIT
