# Azure Functions / Durable Extension path

Use this path when the agent requires:

- Azure Functions event triggers;
- reliable long-running execution;
- checkpointing / resume-after-failure;
- waiting for external events;
- multi-agent orchestration with durable guarantees.

Install:

```bash
pip install -e ".[functions]"
```

The included `function_app.py` shows the `AgentFunctionApp` pattern documented by Microsoft Agent Framework.

Because the Azure Functions integration has evolved rapidly, verify the currently published package version and hosting contract before production deployment:

https://learn.microsoft.com/en-us/agent-framework/hosting/azure-functions

For local Functions execution, follow Microsoft's current guidance for Azure Functions Core Tools and Azurite.
