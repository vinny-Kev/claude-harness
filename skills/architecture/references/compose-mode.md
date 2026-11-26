# Mode A — Compose & Register

Goal: produce a reusable, validated architecture spec and save it where it can be found again.

## 1. Gather inputs (ask only what's missing, in one message)

- Project type (REST API, web app, CLI, library, event consumer…) and language/framework.
- Team constraints: testing strategy, ORM/persistence, sync vs async, multi-tenancy.
- Style: pick a registered one, or describe a custom one.

## 2. Choose a base

Registered styles in `registry/architectures/`: `mvc`, `layered`, `hexagonal`,
`service-middleware-aggregate`. Quick guide:

| Situation | Start from |
|---|---|
| Small/medium CRUD web app with server-rendered views or thin API | `mvc` |
| Typical backend service, clear tiers, moderate domain logic | `layered` |
| Rich domain, many external integrations, testability is key | `hexagonal` |
| API composing several downstream services with cross-cutting policies | `service-middleware-aggregate` |
| None fit | `templates/architecture-spec.template.md` |

State the trade-off in one or two sentences when recommending.

## 3. Author the spec

1. Copy the base; set a new `id` (slug) if forking, bump `version`, set `status: draft`.
2. Define layers with an **allow-list** `may_depend_on`. Keep the graph acyclic.
3. Fill every required section (see `spec-schema.md`). In *Detection Hints*, write concrete
   patterns for the project's language (e.g. "files under `controllers/` must not import `*/repositories/*`").
4. Add stack-specific *Conventions* (file naming, DTO placement, transaction boundaries, error mapping).

## 4. Validate

- In the harness repo: `python3 scripts/validate-registry.py`.
- Elsewhere: walk the checklist in `spec-schema.md` manually (keys, graph references, acyclic, sections).

## 5. Register

Ask the user, then write:

| Target | Path | Visibility |
|---|---|---|
| Project-local | `<project>/.claude/architectures/<id>.md` | Private to that repo (default) |
| Harness registry | `registry/architectures/<id>.md` | **Public**: strip anything project-specific |

For the public registry also: confirm no company/product names, hostnames, internal paths, or
real identifiers appear; run `scripts/check-secrets.sh`.

If the project has a `CLAUDE.md`, offer (don't force) to add one line: `Architecture: follow .claude/architectures/<id>.md`.

## 6. Report

Id, version, layer list with allowed dependencies, save location, and any open decisions (e.g. unresolved exceptions).
