# ModelScope Vision MCP v0.1.0 Release Notes

## Release State

Not released. Local implementation is complete, but real ModelScope smoke testing and Hermes runtime integration are still pending.

## Planned Scope

- Single-image detailed visual recognition MCP.
- ModelScope API integration.
- Multi-model daily quota tracking.
- Automatic fallback on quota exhaustion or model failure.
- DeepSeek-ready visual context generation.

## Acceptance Checklist

- Local package imports successfully. Done.
- Unit tests pass. Done.
- Relative path scan passes. Done.
- A local or URL image can be analyzed.
- URL image smoke test passes with ModelScope streaming models.
- Quota exhaustion fallback works.
- Model failure fallback works.
- Token is not printed in logs or error output.
- Hermes runtime integration steps are reviewed before use.

## Out of Scope

- Multi-image comparison.
- Video understanding.
- Bounding-box object detection.
- Table reconstruction.
- Automatic Feishu image attachment download.
