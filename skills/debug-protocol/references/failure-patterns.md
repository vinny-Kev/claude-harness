# Common failure patterns (candidate hypotheses)

Use as a checklist of *candidates*; each still needs an observation that confirms or refutes it.

| Symptom | Likely causes to test first |
|---|---|
| `undefined` / `null` / `NoneType` access | Value never set on this path; async data not loaded yet; wrong key or shape from API; optional field missing; shadowed variable; destructuring a failed result |
| Works first time, fails later | Mutated shared state; cache staleness; resource leak (connections, file handles); counter/overflow; token or session expiry |
| Passes locally, fails in CI/prod | Env vars/config differ; dependency version drift (lockfile ignored); different OS/path case sensitivity; timezone/locale; missing build step; data differences; clock skew; resource limits |
| Intermittent failure | Race condition; test order dependence; shared fixtures; randomness; time-dependent logic; network/timeouts; port collisions |
| Wrong number | Off-by-one; float rounding; integer overflow/division; unit mismatch; timezone/DST; inclusive vs exclusive ranges; implicit string/number coercion |
| Wrong text | Encoding (UTF-8 vs other); normalization; locale; escaping/double-escaping; trailing whitespace/newlines; case |
| Wrong order | Unstable sort; map/set/dict iteration assumptions; async completion order; DB without `ORDER BY` |
| Duplicate side effects | Retries without idempotency; double click/submit; at-least-once delivery; missing unique constraint; effect in a re-running hook/render |
| Hang / timeout | Deadlock; missing `await`; unbounded loop/recursion; waiting on a condition that never occurs; blocked event loop; slow query; DNS/network |
| Memory growth | Unbounded cache/list; listeners not removed; closures retaining large objects; connection pool leak |
| "It was working yesterday" | Dependency auto-upgrade; config/secret rotated; data volume or shape changed; expiring certificate/token; feature flag; deploy of a different service |
| Permission/auth errors | Wrong environment credentials; expired token; missing scope; clock skew; proxy stripping headers; CORS vs real auth failure |
| DB errors | Migration not applied; constraint violation; wrong transaction isolation; connection pool exhaustion; N+1 causing timeouts; case sensitivity |
| Frontend glitch | Stale state/closure; effect dependency list; key collisions in lists; race between fetches; hydration mismatch; CSS specificity |
| Build/type errors after upgrade | Breaking API change; duplicated dependency versions; stale caches (`node_modules`, build dir); lockfile drift |

## Questions that often crack it
- What is the *first* place the data differs from what I expect?
- What changed between the last good and first bad run (code, data, config, environment, time)?
- Is this code path actually executing (log it) and is it the version I think it is (build, cache)?
- Am I looking at the right instance (environment, tenant, process, file)?
- What would have to be true for this symptom to occur, and can I check each condition?

## Smells that you are guessing
Changing several things at once; adding retries or sleeps; wrapping in try/except; "it should work"; explaining the bug without having observed it; fixes that only work once.
