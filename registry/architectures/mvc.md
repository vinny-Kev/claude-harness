---
id: mvc
name: Model–View–Controller
version: 1.0.0
status: stable
summary: Controllers coordinate; models hold data and business rules; views only render.
tags: [web, server-rendered, small-app, api]
layers:
  - id: controller
    responsibility: Receives requests, validates input, invokes models/services, selects the view or serializer.
    may_depend_on: [model, view]
    owns: [controllers, routes, request-validators]
    must_not: [business rules, SQL, markup generation]
  - id: model
    responsibility: Data, business rules and persistence access (including repository/ORM objects).
    may_depend_on: []
    owns: [models, entities, repositories, domain-services]
    must_not: [request/response objects, view logic]
  - id: view
    responsibility: Presentation only (templates, serializers, view-models); renders what it is given.
    may_depend_on: []
    owns: [templates, serializers, presenters]
    must_not: [queries, business decisions, mutating state]
---

## Intent

Fast to build and easy to learn for small and medium apps. Choose it when the domain is
modest. As business logic grows, extract a service layer (see `layered`) so models don't become
catch-alls.

## Layers & Responsibilities

### controller
- Does: authentication/authorization checks, input validation, call model/service, pick view or serializer, set status.
- Never: contain business rules or queries; build HTML/JSON by hand.

### model
- Does: invariants, relationships, queries (via repository or ORM), domain operations.
- Never: know about requests, sessions, or rendering.

### view
- Does: render supplied data; format for display.
- Never: query data, call models for more, change state.

## Dependency Rules

```
controller → model
controller → view
```

`model` and `view` do not depend on each other or on `controller`. The controller passes the
view plain data (view-models or serialized structures), not live model objects that lazily query.

## Conventions

- One controller per resource; actions map to CRUD or named verbs.
- Models expose intention-revealing methods (`order.cancel()`), not setters scattered across controllers.
- Serializers whitelist output fields; never serialize a model wholesale.
- Validation: shape/type at the controller edge; invariants in the model.

## Request / Data Flow

1. Router dispatches to a controller action.
2. Controller validates input and authorizes.
3. Controller calls model operations (or a service wrapping them).
4. Controller passes results to a view/serializer.
5. Response is returned with the proper status.

## Anti-patterns

- Fat controller: logic, queries and branching in actions.
- Fat model with request/session awareness.
- Views that lazy-load associations or call services (N+1, hidden queries).
- Serializing a whole model (leaks fields).

### Accepted exceptions

_None._

## Detection Hints

- `controllers/**` must not contain raw SQL or query-builder chains; calls go through model methods.
- `models/**` must not import controller, request, session or view modules.
- `views/**` and serializers must not import `models/**` repositories or perform queries.
- Grep: `grep -rEn "(SELECT|INSERT|UPDATE|DELETE)\b|\.query\(" controllers/`.

## Planning Checklist

- Which resource and actions are affected?
- What new model behavior or invariants are required?
- Which fields may the view/serializer expose?
- Where is authorization enforced?

## Refactoring Playbook

1. Move queries out of controller actions into named model methods.
2. Move conditionals about business state into model methods.
3. Replace inline JSON/HTML building with serializers/templates that whitelist fields.
4. When models bloat, extract a service layer and migrate to `layered`.
