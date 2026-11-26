# Discovery: find the attack surface

Goal: a complete endpoint inventory plus the controls that wrap each endpoint.

## 1. Identify the stack
Check manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `pom.xml`, `go.mod`, `composer.json`, `Gemfile`) and entry files.

## 2. Locate routes/handlers

| Stack | Where to look |
|---|---|
| Express/Koa/Fastify | `app.(get\|post\|put\|patch\|delete\|use)`, `router.*`, `fastify.route`, `server.register` |
| NestJS | `@Controller`, `@Get/@Post/...`, guards, pipes, interceptors, DTO classes |
| Next.js / Remix / SvelteKit | `app/**/route.ts`, `pages/api/**`, server actions, `+server.ts`, loaders/actions |
| Django / DRF | `urls.py`, `ViewSet`, `APIView`, serializers, `permission_classes` |
| Flask / FastAPI | `@app.route`, `@router.get`, Pydantic models, `Depends(...)` |
| Spring | `@RestController`, `@RequestMapping`, `@Valid`, security filter chain |
| Rails | `config/routes.rb`, controllers, strong params, serializers |
| Laravel | `routes/*.php`, controllers, FormRequests, API resources |
| Go (net/http, gin, chi, echo) | `HandleFunc`, `r.GET`, middleware `Use` |
| GraphQL | schema/resolvers, depth/complexity limits, introspection, field auth |
| WebSocket / SSE / webhooks | message handlers, signature verification |
| File upload / download | multipart handlers, static serving, path joins |

## 3. Locate the controls
- **Global middleware order** (CORS, helmet/headers, body parsers + limits, rate limit, auth, CSRF, validation, error handler).
- **Auth**: where identity is established, where authorization is checked (route, service, or nowhere).
- **Validators/schemas**: Joi/Zod/Yup/class-validator/Pydantic/serializers/strong params. Note which routes lack one.
- **Serializers / DTOs / response mappers**: what shapes leave the system.
- **Error handler**: what a thrown error becomes in the response body.
- **Config**: CORS origins, cookie flags, trust-proxy, body size limits, debug flags.

## 4. Inventory
Fill one row per endpoint (see `SKILL.md`). Add "Unprotected / unvalidated" and "Returns raw model?" flags; those drive prioritization.

## 5. Coverage statement
Record files not read and why (generated, vendored, too large) so the report can state its limits.
