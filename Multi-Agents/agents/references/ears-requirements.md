# EARS 需求格式规范

## EARS (Easy Approach to Requirements Syntax)

所有功能需求必须使用 EARS 格式编写。

### Pattern Types

| Type | Structure | Example |
|------|-----------|---------|
| Ubiquitous | The system shall [action] | The system shall encrypt all passwords using bcrypt |
| Event-Driven | When [trigger], the system shall [action] | When the user clicks "Submit", the system shall save the form data |
| State-Driven | While [state], the system shall [action] | While the user is logged in, the system shall display the dashboard |
| Conditional | While [state], when [trigger], the system shall [action] | While the cart contains items, when the user clicks "Checkout", the system shall navigate to payment |
| Optional | Where [feature enabled], the system shall [action] | Where two-factor authentication is enabled, the system shall require a verification code |

### EARS Requirement ID Convention

- `FR-{MODULE}-{NNN}`: Functional Requirement (e.g., `FR-AUTH-001`, `FR-ORDER-002`)
- Each requirement must be testable and unambiguous

---

## Acceptance Criteria Format (Given-When-Then)

所有验收标准必须使用 Given-When-Then 格式。

### Structure

```markdown
### AC-{NNN}: [Scenario Name]
Given [context/precondition]
When [action taken]
Then [expected result]
And [additional expected result]
```

### Scenario Types

| Type | Given | When | Then |
|------|-------|------|------|
| Happy path | Valid state | Valid action | Success result |
| Error | Invalid state/input | Action | Error message |
| Edge case | Boundary condition | Action | Graceful handling |
| Authorization | User role | Protected action | Appropriate access response |

### INVEST Criteria

Good acceptance criteria follow INVEST:
- **I**ndependent: Can be tested alone
- **N**egotiable: Details can be discussed
- **V**aluable: Delivers user value
- **E**stimable: Effort can be estimated
- **S**mall: Testable in one session
- **T**estable: Pass/fail is clear
