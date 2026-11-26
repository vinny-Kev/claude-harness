---
id: service-middleware-aggregate
name: Service–Middleware–Aggregate
version: 1.0.0
status: stable
summary: Single-purpose services own data and rules; middleware applies cross-cutting policy; aggregates compose services into API responses.
tags: [backend, api, composition, microservices]
layers:
  - id: middleware
    responsibility: Cross-cutting request policy (authentication, rate limiting, validation, tracing, error mapping).
    may_depend_on: []
    owns: [auth, rate-limit, request-validation, correlation-id, error-handler]
    must_not: [business decisions, data access]
  - id: aggregate
    responsibility: Compose results from several services into one response-shaped result; no rules of its own.
    may_depend_on: [service]
    owns: [aggregators, response-assemblers, orchestration]
    must_not: [persistence, owning invariants, calling data stores]
  - id: service
    responsibility: One bounded capability each; owns its business rules and its data access.
    may_depend_on: [data]
    owns: [services, domain-rules, service-dtos]
    must_not: [HTTP types, calling sibling services' data stores, response shaping]
  - id: data
    responsibility: Persistence and external-resource access, private to the owning service.
    may_depend_on: []
    owns: [repositories, queries, clients]
    must_not: [business rules, being used by another service]
---

## Intent

Keeps cross-cutting policy out of business code and prevents services from entangling.
Choose it for APIs that assemble data from multiple capabilities (orders + customers + inventory)
or that are migrating toward service boundaries. Rules are only as good as the boundaries
between services; keep each service's data private.

## Layers & Responsibilities

### middleware
- Does: authenticate, authorize at the coarse level, rate-limit, validate shape, correlate, translate errors.
- Never: decide business outcomes or touch data.

### aggregate
- Does: call services (parallel where independent), merge/shape results, handle partial failure policy.
- Never: persist, enforce invariants, or query stores. If it needs a rule, ask the owning service.

### service
- Does: enforce one capability's rules, own its data via its `data` layer, expose a typed interface.
- Never: read another service's tables, or return transport-shaped responses.

### data
- Does: queries and external clients for exactly one service.
- Never: be shared across services.

## Dependency Rules

```
middleware (wraps every request; no dependencies)
aggregate → service → data
```

Middleware runs around handlers and does not import business layers. Services call each other
only through their public interfaces (or via an aggregate), never through each other's `data`.
Data access is private: one service's `data` is not imported by anything but that service.

## Conventions

- Services expose narrow typed interfaces; internal models stay internal.
- Aggregates return response DTOs and never leak service-internal models.
- Middleware order is explicit and documented (e.g. correlation → rate-limit → auth → validation).
- Fine-grained authorization (object-level) happens in the owning service; coarse checks in middleware.
- Partial-failure policy (fail, degrade, default) is stated per aggregate.

## Request / Data Flow

1. Request passes the middleware chain (correlation, rate limit, authn, validation).
2. Handler invokes an aggregate (or a single service for simple reads).
3. Aggregate calls the needed services, in parallel where independent.
4. Each service applies its rules and reads/writes its own data.
5. Aggregate assembles the response DTO; error middleware maps failures.

## Anti-patterns

- Aggregates with their own queries or rules ("god aggregator").
- Service A reading Service B's tables.
- Middleware that branches on business state (e.g. plan type) beyond coarse policy.
- Handlers that skip the aggregate and stitch services inline.
- Returning service-internal models from the API.

### Accepted exceptions

_None._

## Detection Hints

- `aggregate/**` must not import `data/**` or DB/ORM packages.
- `service/<a>/**` must not import `service/<b>/data/**`; cross-service calls use the public interface.
- `middleware/**` must not import `service/**`, `aggregate/**`, or `data/**`.
- `service/**` must not import HTTP framework request/response types.
- Grep: `grep -rEn "(SELECT|INSERT)\b|\.query\(|repository" src/aggregate src/middleware`.

## Planning Checklist

- Which service owns each new rule or datum?
- Does this need a new aggregate, or a change to an existing one?
- Which middleware policies apply (auth, rate limit, validation), and in what order?
- What is the partial-failure behavior?
- What are the public interfaces between services?

## Refactoring Playbook

1. Identify handlers that stitch several data sources; extract an aggregate.
2. Move each data source behind its owning service interface.
3. Replace cross-service table reads with service calls.
4. Pull auth, validation, rate limiting and error mapping into middleware.
5. Introduce response DTOs so internals stop leaking.
