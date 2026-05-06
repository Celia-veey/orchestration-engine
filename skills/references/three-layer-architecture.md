# 三层架构规范

## Three-Layer Architecture

```
Controller (HTTP) → Service (Business Logic) → Repository (Data Access)
```

| Layer | Responsibility | Never |
|-------|---------------|-------|
| Controller | Parse request, validate, call service, format response | Business logic, DB queries |
| Service | Business rules, orchestration, transaction mgmt | HTTP types (req/res), direct DB |
| Repository | Database queries, external API calls | Business logic, HTTP types |

## Configuration Management

- All config via environment variables (Twelve-Factor)
- Validate required vars at startup — fail fast
- Type-cast at config layer, not at usage sites
- Commit .env.example with dummy values
- Never hardcode secrets, URLs, or credentials

## Project Structure

- Use Feature-first organization by default
- Each feature has its own directory with controller, service, repository
- Shared utilities in `common/` or `utils/`

## Dependency Injection

- Use interfaces, not concrete implementations
- Controllers depend on service interfaces
- Services depend on repository interfaces
- Enables easy mocking for testing
