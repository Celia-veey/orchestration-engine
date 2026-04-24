# AI Agent Pull Request Submission Guidelines (GitHub MCP)

## 1. PR Creation
- Use deterministic branch names: `<type>/<context_id>`
- Follow Conventional Commits format for commit messages
- Create a new branch for each feature or bug fix

## 2. PR Body Template
```markdown
## 🎯 Context & Objective
* **Trigger:** [State the original user requirement or system prompt]
* **Objective:** [Briefly describe what this PR achieves]

## 🧠 Knowledge Context Alignment
* **Current Phase:** Coding -> Awaiting Code Review
* **Context Updates:** [Explain how this PR updates the global Knowledge Manager state]

## ⚙️ Technical Implementation
* [Detail 1: e.g., Created `auth.go` to handle JWT validation]
* [Detail 2: e.g., Updated tests to cover edge cases]

## 🧪 Validation & Tests
* **Test Command Executed:** `[Insert command, e.g., go test ./...]`
* **Test Results:** [Pass / Fail summary]

## ⚠️ Human Review Request (HITL)
[List specific questions for the human architect, or write "Standard review required."]
```

## 3. Review Process
- PRs require at least one approval before merging
- Address all review comments promptly
- Keep PRs focused and limited to a single feature or bug fix

## 4. Merging
- Use squash merge for feature branches
- Use rebase merge for bug fixes
- Ensure all tests pass before merging