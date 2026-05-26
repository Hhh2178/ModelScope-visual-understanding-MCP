# Security

## API Keys

Do not commit ModelScope tokens or other secrets.

Use an environment variable:

```bash
export MODELSCOPE_TOKEN="your-token"
```

For Hermes MCP configuration, prefer environment interpolation:

```yaml
mcp_servers:
  modelscope-vision:
    command: /path/to/ModelScope-visual-understanding-MCP/scripts/run-server.sh
    env:
      MODELSCOPE_TOKEN: ${MODELSCOPE_TOKEN}
```

## Runtime State

The `state/` directory stores local daily usage counters and model cooldown status. It is ignored by git.

## Reporting Issues

If you find a security issue, rotate affected tokens first, then open a private report or contact the maintainer.
