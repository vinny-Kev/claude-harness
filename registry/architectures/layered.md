---
id: layered
name: Layered (N-tier)
version: 1.0.0
status: stable
summary: Presentation, application, domain and infrastructure tiers with strictly downward dependencies.
tags: [backend, web, api, general]
layers:
  - id: presentation
    responsibility: Transport concerns (HTTP routes, controllers, CLI handlers); validates and maps input to application calls and results to responses.
    may_depend_on: [application]
    owns: [routes, controllers, request-dtos, response-dtos]
    must_not: [business rules, direct database access]
  - id: application
    responsibility: Use-case orchestration, transactions, authorization decisions; coordinates domain objects and infrastructure through interfaces.
    may_depend_on: [domain]
    owns: [services, use-cases, command-handlers]
    must_not: [HTTP types, SQL, framework request objects]
  - id: domain
    responsibility: Business entities, value objects, invariants and repository interfaces; framework-free.
    may_depend_on: []
    owns: [entities, value-objects, domain-errors, repository-interfaces]
    must_not: [framework imports, ORM annotations leaking behavior, I/O]
  - id: infrastructure
    responsibility: Implements domain interfaces (persistence, queues, external APIs, config).
    may_depend_on: [domain]
    owns: [repositories, api-clients, orm-models, migrations]
    must_not: [business rules, HTTP concerns]
---

## Intent

Simple, widely understood structure for services with moderate domain logic. Choose it when
you want clear separation without ceremony. Prefer `hexagonal` when many external systems
need swappable adapters, or `mvc` for small server-rendered apps.

## Layers & Responsibilities

### presentation
- Does: parse/validate input, call one application use case, map result or error to a response.
- Never: query the database, apply business rules, return persistence entities.

### application
- Does: one method per use case, transaction boundaries, authorization checks, calls domain + repository interfaces.
- Never: know about HTTP status codes, `req`/`res`, SQL, or ORM sessions.

### domain
- Does: enforce invariants, model the business vocabulary, declare repository interfaces.
- Never: import frameworks, perform I/O, depend on outer layers.

### infrastructure
- Does: implement repository interfaces, talk to databases/queues/third parties.
- Never: contain business decisions; expose ORM types upward.

## Dependency Rules

```
presentation → application → domain ← infrastructure
```

`infrastructure` depends on `domain` (it implements its interfaces) and is wired to
`application` at composition time (dependency injection) — `application` never imports it.
Anything not listed in `may_depend_on` is forbidden. Data crossing a boundary is a DTO or
domain object, never a request object or ORM entity.

## Conventions

- One use case per application method; name by intent (`placeOrder`, not `processOrder`).
- Request/response DTOs live in `presentation`; domain objects in `domain`; ORM models in `infrastructure`.
- Domain errors are typed; `presentation` maps them to transport errors (status codes).
- Transactions open and close in `application`.
- Composition root (DI wiring) is the single place allowed to import all layers.

## Request / Data Flow

1. Route receives request; presentation validates and builds an input DTO.
2. Presentation calls an application use case.
3. Application loads/saves via domain repository interfaces and applies domain logic.
4. Infrastructure repository executes persistence and returns domain objects.
5. Application returns a result; presentation maps it to a response DTO.

## Anti-patterns

- Fat controllers that contain queries or rules.
- Services that accept `Request` objects or return HTTP-shaped errors.
- Returning ORM entities directly from endpoints (leaks fields, couples schema to API).
- Domain importing an ORM or HTTP library "just for a decorator".
- Application importing concrete repositories instead of interfaces.

### Accepted exceptions

_None._

## Detection Hints

- `presentation/**` must not import from `infrastructure/**` or ORM/DB packages.
- `application/**` must not import `infrastructure/**`, HTTP framework types, or DB drivers.
- `domain/**` must not import any other layer or any framework/ORM/HTTP package.
- `infrastructure/**` must not import `application/**` or `presentation/**`.
- Grep examples: `grep -rEn "from ['\"].*infrastructure" src/presentation src/application`; `grep -rEn "(req|res|Request|Response)\b" src/application src/domain`.

## Planning Checklist

- Which use case(s) does this feature add or change?
- Does it need a new domain concept or invariant?
- Which repository interface methods are needed, and who implements them?
- What are the input/output DTOs at the edge?
- Where does the transaction boundary sit?

## Refactoring Playbook

1. Extract the query from the controller into an application service method.
2. Introduce a repository interface in `domain`; move the query into an `infrastructure` implementation.
3. Replace ORM entities in responses with response DTOs and a mapper.
4. Move business conditionals from services/controllers into domain objects.
5. Remove framework types from `application` and `domain`; inject via interfaces.
