---
name: modelscope-vision
description: "Default image recognition workflow for Hermes. Use ModelScope Vision MCP for images, screenshots, visual analysis, OCR-like visible text extraction, and image-to-prompt visual detail before reasoning with the main model."
version: 0.1.0
author: Hermes Workspace
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Vision, Images, OCR, ModelScope, MCP, DeepSeek]
    related_skills: [native-mcp, ocr-and-documents]
---

# ModelScope Vision

Use this skill whenever the user asks Hermes to understand an image, screenshot, poster, product photo, character image, document image, UI screenshot, or any visual attachment.

## Default Rule

When an image is available and the task requires visual understanding, call:

```text
mcp_modelscope_vision_analyze_image
```

Use the MCP output as visual evidence for follow-up reasoning. Do not rely on the main text model to infer image content without calling the vision MCP first.

## Tool Inputs

Recommended defaults:

- `image`: image URL, local path, data URL, or base64 string.
- `question`: the user's actual visual question.
- `detail`: `medium`.
- `preferred_model`: omit unless the user asks for a specific model.

Use `preferred_model: Qwen/Qwen3-VL-8B-Instruct` only when forcing the first vision model is useful. Otherwise let the MCP quota and fallback selector choose.

## Reasoning Flow

1. Call `mcp_modelscope_vision_analyze_image`.
2. Read `deepseek_context`.
3. Base the final answer on `deepseek_context` and the user's question.
4. Preserve uncertainty: if the MCP marks something uncertain, do not present it as confirmed fact.
5. If the user asks for prompt reverse-engineering, use the detailed `vision` fields for camera, subject, composition, lighting, color, texture, effects, and quality.

## Output Preference

For normal user answers:

- Summarize the image clearly.
- Include visible text when relevant.
- Mention uncertainty when relevant.
- Avoid dumping the entire raw JSON unless the user asks for structured output.

For image generation prompt reconstruction:

- Start with camera angle, framing, lens feel, and depth of field.
- Then describe subject, pose, clothing, materials, environment, light, color, composition, style, effects, and quality.
- Keep the result dense and concrete.

## Fallback Behavior

The MCP automatically:

- tracks each configured model's daily quota;
- skips exhausted models;
- cools down failing models;
- falls back to the next available model;
- returns the model used and attempt history.

If all models fail, report the failure clearly and include the attempt reasons. Do not pretend the image was recognized.
