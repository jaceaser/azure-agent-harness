# Architecture

## Two planes

### Runtime plane

The runtime plane performs useful work:

```text
request/event → agent → memory → tool/MCP → deterministic action → response
```

### LLMOps plane

The LLMOps plane determines whether that work is observable, correct and safe to release:

```text
trace → observe → evaluate → diagnose → gate → release
```

Keeping these concerns separate prevents business logic from becoming tightly coupled to one monitoring or evaluation implementation.

## Thin-agent rule

Agent folders should contain only agent-specific behavior: instructions, selected tools, optional workflow composition, policy configuration and eval cases. Shared infrastructure belongs under the harness.

## Tool boundary

Tools that mutate external systems must enforce invariants in code. Examples:

- a cancellation tool can expose only "cancel at period end" rather than a generic subscription mutation endpoint;
- an outbound-email tool can validate recipient/domain restrictions;
- money movement can require an approval token generated outside the LLM context.

## Memory

Do not treat raw chat history as the only memory strategy. Separate:

- working/session state;
- procedural instructions and skills;
- semantic facts and retrieved knowledge;
- episodic records of actions and outcomes.

## Improvement loop

A future optimization agent may inspect traces and eval failures and propose prompt, tool or policy changes. It must create a branch/PR or issue rather than modify production directly.
