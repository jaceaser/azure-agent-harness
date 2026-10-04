# Enterprise Readiness Checklist

This checklist is intentionally stricter than the minimal starter.

## Identity and access
- [ ] Production uses Managed Identity or explicit workload identity.
- [ ] Foundry Responses host uses inbound Entra ID authentication in production.
- [ ] RBAC is least privilege per agent/workload.
- [ ] Tool-level authorization maps Entra roles/scopes to each tool risk level.
- [ ] Human administration is separated from runtime identities.
- [ ] External SaaS credentials are scoped and rotated.

## Network
- [ ] Egress requirements are documented.
- [ ] Private networking is evaluated for Foundry, storage, databases and Key Vault.
- [ ] MCP servers are authenticated and network-restricted.

## Data
- [ ] Data classification is documented.
- [ ] PII/regulated data is redacted from telemetry where required.
- [ ] Retention/deletion policies exist for traces and memory.
- [ ] Cross-tenant/user authorization is tested.

## Actions
- [ ] Mutating tools are idempotent.
- [ ] Webhooks validate signatures and replay protection.
- [ ] High-risk operations have deterministic policy checks.
- [ ] Human approval is durable and auditable where required.

## LLMOps
- [ ] Regression dataset represents real failure modes.
- [ ] Deterministic tests run on every PR.
- [ ] Model-based evals run before production releases.
- [ ] Production traces are sampled for ongoing evaluation.
- [ ] Prompt/model/tool/policy versions are recorded on traces.
- [ ] Quality thresholds block releases.

## Operations
- [ ] SLOs exist for availability, latency and task success.
- [ ] Alerts exist for error-rate and tool-failure regressions.
- [ ] Dead-letter/retry strategy exists for event-driven workloads.
- [ ] Runbooks cover model/provider outages.
- [ ] Cost budgets and token/tool-call limits are configured.
