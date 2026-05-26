# ModelScope Vision MCP v0.1.0 Dev Notes

## Implementation Boundary

All development for this MCP stays inside this project folder. Project-internal paths are relative to the MCP project root.

## Runtime Path Policy

- Use `config/models.yaml` for local model configuration.
- Use `prompts/vision_reverse_prompt.zh.md` for the built-in vision prompt.
- Use `state/usage.json` for local daily usage state.
- Do not write machine-specific absolute paths into source code, config, tests, or docs.
- Deployment-specific paths belong in the deployment command or Hermes runtime configuration, not in this project.

## First Implementation Target

Implement one MCP tool: `analyze_image`.

The tool should:

- accept one image path, URL, or base64 image string;
- select the first available ModelScope model by quota and priority;
- call the visual model with the built-in detailed prompt;
- fall back to another model on quota exhaustion or model failure;
- normalize the result into structured visual evidence;
- generate `deepseek_context` for Hermes main-model reasoning.

## Validation Commands

Run from the MCP project root:

```bash
pytest -q
```

Path portability scan:

```bash
python -m modelscope_vision_mcp.portability_check
```
