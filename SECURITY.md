# Security Policy

Azure Agent Harness is a starter architecture, not a security certification.

## Reporting vulnerabilities

Please report security issues privately to the repository maintainers rather than opening a public issue. Configure a GitHub Security Advisory channel after publishing the repository.

## Production checklist

Before production use:

- replace development credentials with Managed Identity or another explicit production credential;
- use Azure Key Vault / platform secret stores;
- apply least-privilege RBAC to Foundry, storage, queues, databases and external services;
- treat all tool and MCP output as untrusted input;
- use allowlists for MCP servers/tools and pin trusted package/container versions;
- enforce high-risk business rules inside deterministic action code;
- require approval for high-risk actions;
- implement idempotency keys for externally mutating operations;
- redact PII/secrets before exporting prompts, tool arguments or tool results to telemetry;
- set retention policies appropriate to your data classification;
- restrict egress/network access where required;
- use private endpoints/VNet integration where your threat model requires it;
- validate webhook signatures and replay protection;
- configure rate limits and abuse controls;
- keep model-visible tool errors generic; send detailed exceptions only to trusted telemetry;
- scan dependencies, containers and IaC in CI;
- protect production GitHub environments with approvals and branch protection.

## Agent-specific threats

Threat-model at least:

- prompt injection and indirect prompt injection;
- tool abuse / confused-deputy attacks;
- unauthorized cross-tenant or cross-user data access;
- secret exfiltration through tool results;
- over-broad MCP capabilities;
- unsafe retry of non-idempotent actions;
- poisoned memory or retrieved knowledge;
- evaluator manipulation;
- telemetry leakage;
- autonomous prompt/policy drift.
