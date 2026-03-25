REVIEW_REF_SOLID = """## SOLID Smell Prompts

### SRP (Single Responsibility)
- File owns unrelated concerns (e.g., HTTP + DB + domain rules in one file)
- Large class/module with low cohesion or multiple reasons to change
- Functions that orchestrate many unrelated steps
- God objects that know too much about the system
- **Ask**: "What is the single reason this module would change?"

### OCP (Open/Closed)
- Adding a new behavior requires editing many switch/if blocks
- Feature growth requires modifying core logic rather than extending
- No plugin/strategy/hook points for variation
- **Ask**: "Can I add a new variant without touching existing code?"

### LSP (Liskov Substitution)
- Subclass checks for concrete type or throws for base method
- Overridden methods weaken preconditions or strengthen postconditions
- Subclass ignores or no-ops parent behavior
- **Ask**: "Can I substitute any subclass without the caller knowing?"

### ISP (Interface Segregation)
- Interfaces with many methods, most unused by implementers
- Callers depend on broad interfaces for narrow needs
- Empty/stub implementations of interface methods
- **Ask**: "Do all implementers use all methods?"

### DIP (Dependency Inversion)
- High-level logic depends on concrete IO, storage, or network types
- Hard-coded implementations instead of abstractions or injection
- Import chains that couple business logic to infrastructure
- **Ask**: "Can I swap the implementation without changing business logic?"

### Common Code Smells (Beyond SOLID)

| Smell | Signs |
|-------|-------|
| Long method | Function > 30 lines, multiple levels of nesting |
| Feature envy | Method uses more data from another class than its own |
| Data clumps | Same group of parameters passed together repeatedly |
| Primitive obsession | Using strings/numbers instead of domain types |
| Shotgun surgery | One change requires edits across many files |
| Dead code | Unreachable or never-called code |
| Speculative generality | Abstractions for hypothetical future needs |
| Magic numbers/strings | Hardcoded values without named constants |

### Refactor Heuristics
1. Split by responsibility, not by size
2. Introduce abstraction only when needed — wait for the second use case
3. Keep refactors incremental — isolate behavior before moving
4. Preserve behavior first — add tests before restructuring
5. Prefer composition over inheritance
6. Make illegal states unrepresentable — use types to enforce invariants
"""

REVIEW_REF_SECURITY = """## Security and Reliability Checklist

### Input/Output Safety
- **XSS**: Unsafe HTML injection, `dangerouslySetInnerHTML`, unescaped templates, innerHTML
- **Injection**: SQL/NoSQL/command/GraphQL injection via string concatenation
- **SSRF**: User-controlled URLs reaching internal services without allowlist
- **Path traversal**: User input in file paths without sanitization (`../` attacks)
- **Prototype pollution**: Unsafe object merging with user input

### AuthN/AuthZ
- Missing tenant or ownership checks for read/write operations
- New endpoints without auth guards or RBAC enforcement
- Trusting client-provided roles/flags/IDs
- Broken access control (IDOR)
- Session fixation or weak session management

### JWT & Token Security
- Algorithm confusion attacks (accepting `none` or `HS256` when expecting `RS256`)
- Weak or hardcoded secrets
- Missing expiration (`exp`) or not validating it
- Sensitive data in JWT payload
- Not validating `iss` or `aud`

### Secrets and PII
- API keys, tokens, or credentials in code/config/logs
- Secrets in git history or env variables exposed to client
- Excessive logging of PII or sensitive payloads

### Supply Chain & Dependencies
- Unpinned dependencies allowing malicious updates
- Dependency confusion (private package name collision)
- Importing from untrusted sources without integrity checks
- Outdated dependencies with known CVEs

### CORS & Headers
- Overly permissive CORS (`*` with credentials)
- Missing security headers (CSP, X-Frame-Options, X-Content-Type-Options)

### Runtime Risks
- Unbounded loops, recursive calls, or large in-memory buffers
- Missing timeouts, retries, or rate limiting on external calls
- Blocking operations on request path (sync I/O in async context)
- Resource exhaustion (file handles, connections, memory)
- ReDoS (Regular Expression Denial of Service)

### Race Conditions
- Multiple threads/async tasks accessing shared variables without synchronization
- **Check-Then-Act (TOCTOU)**: `if (exists) then use` without atomic operations
- **Database Concurrency**: Missing optimistic/pessimistic locking, read-modify-write without transactions
- **Distributed Systems**: Missing distributed locks, cache invalidation races
- **Ask**: "What happens if two requests hit this code simultaneously?"

### Cryptography
- Weak algorithms (MD5, SHA1 for security purposes)
- Hardcoded IVs or salts
- Encryption without authentication (ECB mode, no HMAC)

### Data Integrity
- Missing transactions, partial writes, inconsistent state updates
- Weak validation before persistence
- Missing idempotency for retryable operations
"""

REVIEW_REF_QUALITY = """## Code Quality Checklist

### Error Handling
- **Swallowed exceptions**: Empty catch blocks or catch with only logging
- **Overly broad catch**: Catching base `Exception`/`Error` instead of specific types
- **Error information leakage**: Stack traces or internal details exposed to users
- **Missing error handling**: No try-catch around fallible operations (I/O, network, parsing)
- **Async error handling**: Unhandled promise rejections, missing `.catch()`, no error boundary
- **Ask**: "What happens when this operation fails? Will the caller know?"

### Performance & Caching
- **N+1 queries**: Loop that makes a query per item instead of batch
- **CPU hotspots**: Expensive operations in hot paths (regex compilation, JSON parsing in loops)
- **Missing memoization**: Pure functions called repeatedly with same inputs
- **Over-fetching**: SELECT * when only few columns needed; no pagination
- **Missing cache**: Repeated expensive API calls or DB queries without caching
- **Cache without TTL**: Stale data served indefinitely
- **Unbounded collections**: Arrays/maps that grow without limit
- **Ask**: "How does this behave with 10x/100x data?"

### Boundary Conditions
- **Null/undefined handling**: Accessing properties on potentially null objects
- **Truthy/falsy confusion**: `if (value)` when `0` or `""` are valid
- **Empty collections**: Code assumes array has items; `arr[0]` without length check
- **Division by zero**: Missing check before division
- **Integer overflow**: Large numbers exceeding safe integer range
- **Off-by-one errors**: Loop bounds, array slicing, pagination
- **Unicode edge cases**: Emoji, RTL text, combining characters
- **Ask**: "What if this is null? What if this collection is empty?"
"""

REVIEW_REF_REMOVAL = """## Removal and Iteration Plan Template

### Priority Levels
- **P0**: Immediate removal needed (security risk, significant cost, blocking other work)
- **P1**: Remove in current sprint
- **P2**: Backlog / next iteration

### Safe to Remove Now

| Field | Details |
|-------|---------|
| **Location** | `path/to/file:line` |
| **Rationale** | Why this should be removed |
| **Evidence** | Unused (no references), dead feature flag, deprecated API |
| **Impact** | None / Low — no active consumers |
| **Deletion steps** | 1. Remove code 2. Remove tests 3. Remove config |
| **Verification** | Run tests, check no runtime errors, monitor logs |

### Defer Removal (Plan Required)

| Field | Details |
|-------|---------|
| **Location** | `path/to/file:line` |
| **Why defer** | Active consumers, needs migration, stakeholder sign-off |
| **Preconditions** | Feature flag off for 2 weeks, telemetry shows 0 usage |
| **Migration plan** | Steps for consumers to migrate |
| **Timeline** | Target date or sprint |
| **Rollback plan** | How to restore if issues found |

### Checklist Before Removal
- [ ] Searched codebase for all references
- [ ] Checked for dynamic/reflection-based usage
- [ ] Verified no external consumers (APIs, SDKs, docs)
- [ ] Tests updated/removed
- [ ] Documentation updated
"""

# ==============================================================================
# 5d. STACK-AWARE REFERENCE PROFILES (STORY-026)
# ==============================================================================

# --- Role-Specific References (STORY-026 R1-R2) ---

DEV_REF_FRONTEND = """## Frontend Development Reference

### Component Architecture
- **Decomposition**: Prefer small, single-responsibility components over monolithic page components
- **Presentational vs Container**: Separate data-fetching/state logic from rendering logic
- **Props hygiene**: Watch for props drilling (>3 levels deep); consider Context, Zustand, or composition pattern
- **Excessive props**: If a component takes >7 props, it likely does too much — split it
- **Controlled vs Uncontrolled**: Be explicit about form input ownership; avoid mixing patterns
- **Key prop**: Always use stable, unique keys in lists — never use array index for dynamic lists

### Rendering Performance
- **Unnecessary re-renders**: Components re-rendering when their props/state haven't changed
- **Missing memoization**: Expensive computations in render path without `useMemo`/`React.memo`/`computed`
- **Callback stability**: Inline arrow functions in JSX cause child re-renders — use `useCallback` or extract
- **Large list virtualization**: Lists >100 items should use virtual scrolling (react-window, TanStack Virtual)
- **Image optimization**: Use lazy loading, responsive `srcSet`, next-gen formats (WebP/AVIF)
- **Layout thrashing**: Reading layout properties (offsetHeight) then writing styles in a loop
- **Ask**: "Does this component re-render when it shouldn't? What triggers the re-render?"

### Accessibility (a11y)
- **Semantic HTML**: Use `<button>` not `<div onClick>`, `<nav>` not `<div class="nav">`
- **ARIA roles**: Add `role`, `aria-label`, `aria-describedby` when native semantics are insufficient
- **Keyboard navigation**: All interactive elements must be focusable and operable via keyboard
- **Focus management**: After modal open/close, route change — focus must move to logical target
- **Color contrast**: WCAG AA requires 4.5:1 for normal text, 3:1 for large text
- **Screen reader**: Test with VoiceOver/NVDA; ensure meaningful alt text, live regions for dynamic content
- **Ask**: "Can a keyboard-only user complete this flow? Does a screen reader convey the meaning?"

### Styling & Layout
- **CSS specificity**: Avoid `!important`; prefer low-specificity selectors or CSS Modules/Tailwind
- **Responsive design**: Test at 320px, 768px, 1024px, 1440px breakpoints
- **z-index management**: Use a z-index scale (10, 20, 30...) or CSS variables — never arbitrary large numbers
- **Layout shift (CLS)**: Reserve dimensions for images/embeds; avoid inserting content above the fold
- **Dark mode**: Ensure all custom colors respect the theme — don't hardcode `#fff`/`#000`

### Bundle & Loading Performance
- **Code splitting**: Split by route at minimum; heavy libraries should be dynamically imported
- **Lazy loading**: Components below the fold should load on demand (`React.lazy`, dynamic `import()`)
- **Tree shaking**: Import only what you use (`import { map } from 'lodash-es'` not `import _ from 'lodash'`)
- **Asset optimization**: Compress images, use SVG for icons, subset fonts
- **Core Web Vitals**: Monitor LCP (<2.5s), FID/INP (<100ms), CLS (<0.1)
- **Ask**: "What is the initial bundle size? Can this be deferred?"

### Client-Side Security
- **Token storage**: Never store auth tokens in `localStorage` (XSS-accessible); prefer `httpOnly` cookies
- **postMessage**: Always validate `event.origin` before trusting `event.data`
- **iframe sandboxing**: Use `sandbox` attribute; restrict `allow-scripts` and `allow-same-origin`
- **CSP compliance**: Avoid inline scripts/styles; use nonces or hashes if inline is unavoidable
- **Sensitive data in state**: Don't persist PII in Redux/Zustand stores that sync to localStorage
- **Third-party scripts**: Audit analytics/chat/tracking scripts — they can exfiltrate data
"""

DEV_REF_BACKEND = """## Backend Development Reference

### API Design
- **RESTful conventions**: Use proper HTTP methods (GET=read, POST=create, PUT=replace, PATCH=update, DELETE=remove)
- **Error responses**: Return consistent error format (`{ error: { code, message, details } }`); never expose stack traces
- **Pagination**: Use cursor-based pagination for large datasets; always set a max page size
- **Versioning**: Version APIs via URL prefix (`/v1/`) or header; never break existing clients
- **Idempotency**: POST/PATCH operations should support idempotency keys for safe retries
- **Rate limiting**: Protect endpoints with rate limits; return `429 Too Many Requests` with `Retry-After` header
- **Ask**: "What happens if a client retries this request? Is the response format consistent with other endpoints?"

### Data Layer
- **ORM patterns**: Use query builders or ORM for type-safe queries; avoid raw SQL string concatenation
- **Migration safety**: Migrations must be reversible; avoid `DROP COLUMN` in production without a deprecation period
- **Connection pooling**: Configure pool size based on expected concurrency; monitor for connection leaks
- **N+1 prevention**: Use eager loading / joins / DataLoader pattern; monitor query count per request
- **Transaction boundaries**: Wrap multi-step mutations in transactions; define clear rollback behavior
- **Schema evolution**: Add columns as nullable first; backfill data; then add constraints
- **Ask**: "How many queries does this endpoint execute? Is there a transaction boundary?"

### Concurrency & Async
- **Thread safety**: Shared mutable state must be protected (mutex, atomic, actor model)
- **Async patterns**: Don't mix sync and async I/O; use async all the way or none
- **Queue-based decoupling**: Long-running tasks should go to a job queue, not execute in-request
- **Distributed locking**: Use Redis/etcd locks for cross-process coordination; always set TTL
- **Graceful shutdown**: Handle SIGTERM; drain in-flight requests; close connections cleanly
- **Backpressure**: Producers must respect consumer capacity; use bounded queues
- **Ask**: "What happens under 100x concurrent requests? Is there a bottleneck?"

### Observability
- **Structured logging**: Use JSON logs with `request_id`, `user_id`, `duration_ms`; never log PII
- **Metrics**: Track request latency (p50/p95/p99), error rate, queue depth, connection pool usage
- **Distributed tracing**: Propagate trace context (OpenTelemetry); instrument external calls
- **Health checks**: Expose `/health` (liveness) and `/ready` (readiness) endpoints
- **Alerting**: Set alerts on error rate spikes, latency degradation, resource exhaustion
- **Ask**: "If this fails in production, how will we know? Can we trace the request?"

### Deployment & Configuration
- **Config management**: Use environment variables for config; never hardcode URLs or credentials
- **Secrets management**: Use a vault (AWS Secrets Manager, HashiCorp Vault); rotate credentials regularly
- **Container best practices**: Use multi-stage builds; run as non-root; health check in Dockerfile
- **Database migrations**: Run migrations as a separate step before deployment; never auto-migrate on startup
- **Feature flags**: Use feature flags for gradual rollouts; clean up old flags regularly
- **Rollback plan**: Every deployment should have a documented rollback procedure
"""

# --- Stack-Specific Testing References (STORY-026 R3) ---

TEST_REF_PYTHON = """## Python Testing Reference (pytest)

### Project Structure
- `tests/unit/` — Unit tests (fast, isolated, no I/O)
- `tests/e2e/` — Integration/E2E tests (may touch DB, network)
- `conftest.py` — Shared fixtures, placed at appropriate directory level

### Core Patterns
- **Fixtures**: Use `@pytest.fixture` for setup/teardown; prefer function scope for isolation
- **Parametrize**: Use `@pytest.mark.parametrize` to test multiple inputs without code duplication
- **Markers**: Use `@pytest.mark.slow`, `@pytest.mark.integration` to categorize tests
- **Assertion introspection**: Use plain `assert` — pytest rewrites for rich failure messages
- **Exception testing**: Use `with pytest.raises(ValueError, match="expected message")`

### Mocking
- **`monkeypatch`**: Prefer pytest's `monkeypatch` over `unittest.mock` for env vars, attributes
- **`unittest.mock.patch`**: Use for replacing imports/functions; always patch where used, not where defined
- **Fixture-based mocking**: Create mock fixtures in `conftest.py` for reuse across tests
- **Avoid over-mocking**: If you mock more than you test, the test is meaningless

### Best Practices
- **One assert per concept**: A test should verify one behavior; multiple asserts are OK if testing one logical outcome
- **Test naming**: `test_<what>_<condition>_<expected>` (e.g., `test_login_invalid_password_returns_401`)
- **Coverage**: Aim for >80% on business logic; 100% coverage doesn't mean correctness
- **Determinism**: No random data, no sleep, no real network calls in unit tests
- **Fast feedback**: Unit tests should complete in <10 seconds; use `-x` for fail-fast
"""

TEST_REF_NODE = """## Node.js/TypeScript Testing Reference (Jest / Vitest)

### Project Structure
- `__tests__/` or `*.test.ts` co-located — Choose one convention and be consistent
- `jest.config.ts` / `vitest.config.ts` — Central configuration
- `__mocks__/` — Manual mocks for modules

### Core Patterns
- **describe/it blocks**: Group related tests in `describe`; use `it` for individual cases
- **Matchers**: `expect(x).toBe()` for primitives, `.toEqual()` for objects, `.toMatchObject()` for partial
- **Async testing**: Use `async/await` in test functions; avoid `.then()` chains in tests
- **Snapshot testing**: Use `toMatchSnapshot()` for complex output; update snapshots intentionally, not blindly
- **Testing Library**: Prefer `@testing-library/react` for component tests — query by role/text, not CSS class

### Mocking
- **`jest.mock('module')`**: Auto-mock entire modules; provide manual mock in `__mocks__/` for complex cases
- **`jest.spyOn()`**: Spy on methods without replacing; useful for verifying calls
- **`vi.fn()` (Vitest)**: Create mock functions; use `.mockResolvedValue()` for async
- **MSW (Mock Service Worker)**: Intercept HTTP at the network level for integration tests
- **Avoid over-mocking**: Test real behavior where feasible; mock only external boundaries

### Best Practices
- **Isolation**: Each test file runs in its own context; avoid shared mutable state between tests
- **Cleanup**: Use `afterEach(() => jest.restoreAllMocks())` to prevent mock leakage
- **Test naming**: `it('should return 404 when user not found')` — describe expected behavior
- **Coverage**: Configure with `--coverage`; set thresholds in config for CI enforcement
- **E2E**: Use Playwright or Cypress for browser-level tests; keep them in a separate directory
"""

TEST_REF_GO = """## Go Testing Reference (go test)

### Project Structure
- `*_test.go` — Test files co-located with source in the same package
- `testdata/` — Test fixtures (auto-ignored by Go tooling)
- `internal/testutil/` — Shared test helpers (not exported)

### Core Patterns
- **Table-driven tests**: Define test cases as a slice of structs; iterate with `t.Run(name, func)`
  ```go
  tests := []struct{ name string; input int; want int }{...}
  for _, tt := range tests {
      t.Run(tt.name, func(t *testing.T) { ... })
  }
  ```
- **t.Run subtests**: Name each subtest for clear failure output; enables `-run` filtering
- **t.Helper()**: Mark helper functions with `t.Helper()` so failures report the caller's line
- **t.Parallel()**: Add to independent tests for faster execution; avoid shared state

### Mocking
- **Interfaces**: Define small interfaces at the consumer site; pass mock implementations in tests
- **testify**: `github.com/stretchr/testify/assert` for assertions, `testify/mock` for mock objects
- **httptest**: `net/http/httptest` for HTTP handler testing without a real server
- **Avoid mocking what you don't own**: Wrap external dependencies in your own interface

### Best Practices
- **Race detection**: Always run `go test -race ./...` in CI; fix all data races
- **Benchmark tests**: Use `func BenchmarkX(b *testing.B)` for performance-critical paths
- **Test coverage**: `go test -cover ./...`; use `-coverprofile` for detailed reports
- **Golden files**: For complex output, compare against files in `testdata/`; use `-update` flag to refresh
- **Build tags**: Use `//go:build integration` to separate slow tests from unit tests
"""

TEST_REF_JAVA = """## Java Testing Reference (JUnit 5 + Spring)

### Project Structure
- `src/test/java/` — Test classes mirror main source structure
- `src/test/resources/` — Test configuration, fixtures
- `@Nested` — Group related tests within a test class

### Core Patterns
- **JUnit 5 annotations**: `@Test`, `@BeforeEach`, `@AfterEach`, `@DisplayName` for readability
- **Assertions**: `assertEquals`, `assertThrows`, `assertAll` for grouped assertions
- **Parameterized tests**: `@ParameterizedTest` with `@ValueSource`, `@CsvSource`, `@MethodSource`
- **Test lifecycle**: `@BeforeAll`/`@AfterAll` for expensive setup (DB, containers); `@BeforeEach` for isolation
- **Conditional execution**: `@EnabledOnOs`, `@EnabledIfEnvironmentVariable` for platform-specific tests

### Mocking
- **Mockito**: `@Mock`, `@InjectMocks`, `when().thenReturn()`, `verify()` for behavior verification
- **`@ExtendWith(MockitoExtension.class)`**: Initialize mocks declaratively
- **Argument captors**: `ArgumentCaptor` to inspect values passed to mocked methods
- **Avoid static mocking**: Minimize `MockedStatic`; prefer dependency injection for testability

### Spring Boot Testing
- **`@SpringBootTest`**: Full application context — use sparingly (slow)
- **Test slicing**: `@WebMvcTest` (controllers only), `@DataJpaTest` (JPA only), `@JsonTest` (serialization)
- **`@MockBean`**: Replace a Spring bean with a Mockito mock in the application context
- **TestContainers**: Use `@Testcontainers` + `@Container` for real database/Redis in integration tests
- **`@Transactional`**: Auto-rollback DB changes after each test method

### Best Practices
- **Test naming**: `methodName_condition_expectedResult` (e.g., `findUser_notFound_throwsException`)
- **AAA pattern**: Arrange → Act → Assert; keep each section clearly separated
- **Coverage**: Use JaCoCo for coverage reports; enforce thresholds in CI
- **Fast tests**: Unit tests <5s; slice tests <30s; full integration <2min
- **CI**: Run `mvn test` or `gradle test` in CI; fail the build on any test failure
"""

# --- Main Review Prompt (STORY-022 R2-R8) ---

