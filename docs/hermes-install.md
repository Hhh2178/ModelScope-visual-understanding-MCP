# Hermes Installation Notes

These notes describe how this repository was installed into a Hermes runtime.

## Runtime Layout

Recommended installation layout:

```text
<hermes-home>/
  mcp/
    modelscope-vision/
      .venv/
      config/
      prompts/
      scripts/
      src/
      tests/
      state/
  skills/
    vision/
      modelscope-vision/
        SKILL.md
```

Do not commit runtime files such as `.venv/`, `state/`, `.pytest_cache/`, or API tokens.

## Install MCP

```bash
git clone https://github.com/Hhh2178/ModelScope-visual-understanding-MCP.git modelscope-vision
cd modelscope-vision
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
chmod +x scripts/run-server.sh
```

Set `MODELSCOPE_TOKEN` in the Hermes runtime environment, preferably in the runtime `.env` file rather than `config.yaml`.

Register the MCP:

```bash
hermes mcp add modelscope-vision \
  --command /path/to/modelscope-vision/scripts/run-server.sh \
  --env MODELSCOPE_TOKEN='${MODELSCOPE_TOKEN}'
```

The config entry should keep the token indirect:

```yaml
mcp_servers:
  modelscope-vision:
    command: /path/to/modelscope-vision/scripts/run-server.sh
    env:
      MODELSCOPE_TOKEN: ${MODELSCOPE_TOKEN}
    enabled: true
    timeout: 120
```

## Install Skill

Copy the included skill into Hermes:

```bash
mkdir -p <hermes-home>/skills/vision/modelscope-vision
cp -R skills/modelscope-vision/* <hermes-home>/skills/vision/modelscope-vision/
```

The skill tells Hermes to use `mcp_modelscope_vision_analyze_image` as the default visual understanding workflow.

## Optional Hermes Dedupe Patch

Some Hermes/FastMCP combinations include the same tool result twice:

- `result`
- `structuredContent.result`

For large vision outputs this can double downstream model context. If your Hermes version has this behavior, apply:

```text
patches/hermes-mcp-dedupe.patch
```

This patch is intentionally narrow: it only drops `structuredContent` when it is exactly the same payload as text `result`.

## Validation

```bash
hermes mcp test modelscope-vision
```

Expected:

```text
Connected
Tools discovered: 1
analyze_image
```

Run a tool-chain smoke test from Hermes or call the MCP directly:

```bash
PYTHONPATH=src MODELSCOPE_TOKEN=<token> .venv/bin/python -m modelscope_vision_mcp.smoke_test \
  --preferred-model Qwen/Qwen3-VL-8B-Instruct \
  --image https://modelscope.oss-cn-beijing.aliyuncs.com/resource/qwen.png
```
