# Architecture Registry

Reusable, validated architecture specs. Used by the [`architecture` skill](../../skills/architecture/SKILL.md).

| id | Style | Choose when |
|---|---|---|
| [`mvc`](mvc.md) | Model–View–Controller | Small/medium apps, server-rendered or thin API |
| [`layered`](layered.md) | Layered (N-tier) | General backend services with moderate domain logic |
| [`hexagonal`](hexagonal.md) | Ports & Adapters | Rich domain, many integrations, testability first |
| [`service-middleware-aggregate`](service-middleware-aggregate.md) | Service–Middleware–Aggregate | APIs composing several services with shared policy |

## Adding a style

1. Copy [`../../skills/architecture/templates/architecture-spec.template.md`](../../skills/architecture/templates/architecture-spec.template.md) to `<id>.md` (id = filename stem).
2. Fill it in following [`spec-schema.md`](../../skills/architecture/references/spec-schema.md).
3. `python3 scripts/validate-registry.py` and `scripts/check-secrets.sh` must pass.
4. Add a row above. Specs are **generic**: no private project names, hosts, or code.

Private, project-specific specs belong in that project's `.claude/architectures/`, not here.
