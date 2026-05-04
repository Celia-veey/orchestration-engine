# Git 规范 (Branch/Commit/PR)

## Branch Naming Convention

```
feature/[description]-[date]     # New feature
fix/[description]-[date]         # Bug fix
refactor/[description]-[date]    # Refactoring
chore/[description]-[date]       # Maintenance task
hotfix/[description]-[date]      # Emergency fix

Examples:
feature/order-management-20240115
fix/payment-validation-20240115
```

## Commit Message Convention

```
<type>(<scope>): <description>

[optional body]

[optional footer]

Type:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation changes
  style:    Code formatting (no code behavior change)
  refactor: Refactoring (neither feature nor fix)
  test:     Test related
  chore:    Build process or auxiliary tool changes

Examples:
feat(order): add order creation endpoint
fix(payment): resolve timeout issue with retry logic
docs(api): update OpenAPI spec for v2
```

## PR Description Template

```markdown
## Change Overview
Brief description of this PR's purpose and main changes

## Change Type
- [ ] New feature
- [ ] Bug fix
- [ ] Performance optimization
- [ ] Refactoring
- [ ] Documentation update
- [ ] Dependency update

## Test Status
- Unit test coverage: XX%
- Tests passed: XX/XX
- Code review score: X/10

## Architecture Changes
- Describe any architecture-level changes

## Security Impact
- Describe any security-related changes

## Changed Files List
- `path/to/file1.ts` - Change description
- `path/to/file2.ts` - Change description

## Related Documents
- Requirements: [template-report.md](link)
- Technical plan: [plan.md](link)
- Review report: [eval-template-report.md](link)

## Notes
Other notes, known issues, follow-up plans, etc.
```

## Safety Rules

- NEVER push to `main` — this is the highest priority
- Never ignore the PR template
- Don't check boxes for tasks not done
- Always rebase on latest main before creating PR
