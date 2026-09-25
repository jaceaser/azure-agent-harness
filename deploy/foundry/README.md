# Foundry Hosted Agent deployment

Microsoft Foundry Hosted Agents are the default managed hosting target for this starter.

The included `main.py` uses Microsoft Agent Framework with `ResponsesHostServer`, exposing the OpenAI-compatible `/responses` endpoint on port 8088.

## Local host

```bash
pip install -e ".[foundry-hosting]"
cp .env.example .env
az login
python deploy/foundry/main.py
```

Test:

```bash
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input":"Check the demo service status","stream":false}'
```

## Azure deployment

Agent Framework / Foundry deployment tooling is evolving quickly. Use the current Microsoft-managed `azd ai agent` workflow rather than pinning this starter to a stale generated manifest.

Current documented flow:

```bash
azd ext install azure.ai.agents
azd auth login
```

Initialize or adapt the current official Agent Framework hosted-agent manifest, then:

```bash
azd provision
azd ai agent run
azd deploy
```

See:
https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/framework-hosted-agents
