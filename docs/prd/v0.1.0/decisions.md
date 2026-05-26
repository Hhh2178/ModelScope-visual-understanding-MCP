# ModelScope Vision MCP v0.1.0 Decisions

## Decision 1: Keep This MCP Self-Contained

All project files stay under the MCP project folder.

Reason:

- Avoid scattering MCP-specific docs, prompts, source, tests, and state across the Hermes workspace.
- Make the MCP portable and easier to move into another workspace or runtime environment.

## Decision 2: Use ModelScope Vision Models Instead of DeepSeek Direct Image Input

The MCP delegates image recognition to dedicated ModelScope vision models. DeepSeek remains responsible for downstream reasoning.

Reason:

- DeepSeek Flash/Pro is better treated as the reasoning layer.
- ModelScope has multiple small vision-capable models and daily quotas.
- This keeps vision recognition replaceable without changing Hermes main-model behavior.

## Decision 3: Output Detailed Visual Evidence, Not Simple Captions

The built-in prompt requires structured, high-density visual recognition.

Reason:

- Simple captions are not enough for downstream DeepSeek analysis.
- Detailed output preserves camera, subject, environment, composition, lighting, color, texture, visible text, and uncertainty.

## Decision 4: Use Relative Paths Only

The design forbids hard-coded machine-specific absolute paths.

Reason:

- The MCP should remain portable across Windows, WSL, Linux servers, and future Hermes deployments.
- Deployment-specific paths should live in startup commands or runtime configuration.

## Decision 5: Count Successful Calls First

The first version increments usage after successful model calls.

Reason:

- It avoids overcounting local validation failures.
- If ModelScope charges failed attempts, the setting can be expanded later with a `count_failed_attempts` option.

## Decision 6: Default Vision Model Order

The default order is `Qwen/Qwen3-VL-8B-Instruct`, then `moonshotai/Kimi-K2.5`, then the remaining Qwen 3.5 models.

Reason:

- `Qwen/Qwen3-VL-8B-Instruct` is explicitly a vision-language model and returned stable JSON in Hermes chain tests.
- `moonshotai/Kimi-K2.5` produced detailed visual descriptions and is a strong fallback.
- `Qwen/Qwen3.5-35B-A3B` supports image input with streaming, but occasionally returns malformed JSON under the strict structured prompt, so it is kept after the two more stable choices.
