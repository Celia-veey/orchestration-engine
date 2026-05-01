# ADR 模板 (Architecture Decision Records)

## ADR Template

```markdown
# ADR-{number}: {Title}

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[Describe the situation and forces at play. What is the problem?
What constraints exist? What are we trying to achieve?]

## Decision
[State the decision clearly. What are we going to do?]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Drawback 1]
- [Drawback 2]

## Alternatives Considered
[What other options were evaluated and why were they rejected?]
```

### ADR Naming Convention

```
docs/
└── adr/
    ├── 0001-use-postgresql-database.md
    ├── 0002-adopt-microservices.md
    └── README.md
```

### ADR Status Flow

```
Proposed → Accepted → (Deprecated | Superseded)
```

- **Proposed**: Decision is under review
- **Accepted**: Decision is approved and implemented
- **Deprecated**: Decision is no longer recommended
- **Superseded**: Replaced by a newer ADR
