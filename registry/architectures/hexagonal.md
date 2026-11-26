---
id: hexagonal
name: Hexagonal (Ports & Adapters)
version: 1.0.0
status: stable
summary: A framework-free core defines ports; adapters at the edge implement or drive them.
tags: [backend, domain-rich, integrations, testability]
layers:
  - id: adapters-in
    responsibility: Driving adapters (HTTP, CLI, queue consumers) that translate external input into use-case calls.
    may_depend_on: [application]
    owns: [http-controllers, cli-commands, message-consumers]
    must_not: [business rules, direct outbound adapter use]
  - id: application
    responsibility: Use cases; orchestrates domain objects through inbound and outbound ports.
    may_depend_on: [domain]
    owns: [use-cases, inbound-ports, outbound-ports]
    must_not: [framework types, concrete adapters]
  - id: domain
    responsibility: Entities, value objects, domain services and events; pure business logic.
    may_depend_on: []
    owns: [entities, value-objects, domain-events]
    must_not: [I/O, framework imports]
  - id: adapters-out
    responsibility: Driven adapters implementing outbound ports (DB, messaging, third-party APIs, clock).
    may_depend_on: [application, domain]
    owns: [repositories, gateways, publishers]
    must_not: [business rules, being imported by core]
---

## Intent

Maximum isolation of business logic and easy testing with fakes. Choose it for rich domains
and systems with many external dependencies. It adds interfaces and mapping; avoid for simple CRUD.

## Layers & Responsibilities

### adapters-in
- Does: authenticate, validate/translate input, call an inbound port, translate output.
- Never: reach into adapters-out or domain internals.

### application
- Does: define ports (interfaces), implement use cases, manage transactions via ports.
- Never: import an adapter or framework type.

### domain
- Does: rules and invariants in pure code.
- Never: depend on anything outside itself.

### adapters-out
- Does: implement outbound ports; map between external models and domain objects.
- Never: leak external/ORM types into the core.

## Dependency Rules

```
adapters-in → application → domain
adapters-out → application (ports) , domain
```

Dependencies point **inward**. The core (`application` + `domain`) never imports adapters;
adapters are injected at the composition root. Ports are owned by the core and expressed in its language.

## Conventions

- Port names describe capability (`OrderRepository`, `PaymentGateway`), not technology.
- One mapper per adapter boundary; external DTOs never cross into the core.
- Use cases are single-purpose classes/functions with explicit input/output types.
- Tests: core with in-memory fakes; adapters with contract/integration tests.
- A single composition root wires adapters to ports.

## Request / Data Flow

1. Inbound adapter receives input and maps it to a use-case command.
2. Use case loads aggregates via an outbound port.
3. Domain logic runs; events/results are produced.
4. Use case persists via the outbound port and publishes events.
5. Inbound adapter maps the result to the external response.

## Anti-patterns

- Domain or application importing an ORM, HTTP client, or SDK.
- Inbound adapters calling outbound adapters directly (skipping the use case).
- Ports shaped like the database or the vendor API instead of the domain.
- Anemic use cases that just proxy a repository.

### Accepted exceptions

_None._

## Detection Hints

- `domain/**` and `application/**` must not import `adapters-in/**`, `adapters-out/**`, or any framework/ORM/SDK package.
- `adapters-in/**` must not import `adapters-out/**`.
- `adapters-out/**` must not import `adapters-in/**`.
- Only the composition root may import both adapter families.
- Grep: `grep -rEn "import .*(adapters|infrastructure)" src/domain src/application`.

## Planning Checklist

- What is the use case, and what are its input/output types?
- Which ports does it need, and do they already exist?
- Which invariants belong in the domain?
- Which adapters change, and how are they tested (fake vs integration)?

## Refactoring Playbook

1. Identify a use case hidden in a controller; extract it behind an inbound port.
2. Extract each external dependency used by it into an outbound port in the core.
3. Move the existing implementation into an adapter that implements the port.
4. Replace external types in signatures with domain types plus a mapper.
5. Introduce a composition root and remove direct adapter imports from the core.
