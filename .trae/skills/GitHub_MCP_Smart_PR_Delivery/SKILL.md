# Skill: Smart GitHub PR Delivery (MCP-Driven)

## 1. Skill Metadata
- **Skill Name:** `GitHub_MCP_Smart_PR_Delivery`
- **Description:** Safely and idempotently delivers generated code to GitHub via MCP. It enforces deterministic branching, prevents duplicate Pull Requests, ensures code aligns with the global Knowledge Context, and elegantly handles Human-in-the-Loop (HITL) feedback.
- **Trigger Condition:** Activated when the `Coding` and `Testing` phases are complete, and the Agent decides to invoke the `RequestHumanReview` action for code review.
- **Required MCP Tools:** `list_branches`, `create_branch`, `create_commit`, `push`, `search_issues_and_pr`, `create_pull_request`, `add_issue_comment`.

## 2. Execution Protocol (Check-Before-Act Workflow)

When executing this skill, the Agent MUST follow these steps in exact order:

### Step 1: Pre-Flight Verification
Before interacting with GitHub, verify local state:
1. Ensure all code compiles and sandbox tests pass.
2. Confirm no hardcoded secrets or API keys are present.
3. Formulate the `context_id` (e.g., the issue number or a short hash of the PRD feature).

### Step 2: Deterministic Branch Resolution
Branch names MUST be predictable to ensure idempotency. 
- **Format:** `<type>/<context_id>` (e.g., `feat/user-auth-123`).
- **Action:** 1. Call MCP `list_branches`.
  2. If the branch **exists**: Checkout the branch and `pull` latest changes.
  3. If the branch **does not exist**: Call MCP `create_branch` from `main`.

### Step 3: Code Committal
- **Action:** Write generated code to the workspace.
- **Action:** Call MCP `create_commit` and `push`. 
- **Convention:** Use Conventional Commits (e.g., `feat(auth): implement JWT validation`).

### Step 4: Smart PR Management (Idempotency Check)
NEVER blindly create a Pull Request. Always check state first.
- **Action:** Call MCP `search_issues_and_pr` with query `head:<branch_name> is:open is:pr`.
- **Decision Matrix:**
  - **Case A (No open PR found):** Call MCP `create_pull_request`. Use the "PR Body Template" defined below. Save the returned PR Number to the global Knowledge Context.
  - **Case B (Open PR exists):** DO NOT create a new PR. The `push` in Step 3 already updated it. Call MCP `add_issue_comment` with: *"Code updated automatically based on latest context/review. Please re-verify."*

### Step 5: HITL Suspension
- **Action:** Suspend the current execution thread/loop. Wait for human feedback via the PR.

## 3. Handling Rejections (The Fix Loop)
If the human reviewer rejects the PR or requests changes:
1. Parse the human feedback from the Knowledge Context.
2. Generate the necessary code fixes.
3. **DO NOT change the branch.** Re-run Steps 3, 4 (Case B), and 5.

## 4. Templates

### 4.1 PR Title Template
`[<Type>] <Concise summary of the implementation>`
*(Example: `[Feature] Implement KnowledgeManager for State Accumulation`)*

### 4.2 PR Body Template
When creating a new PR via MCP, use the exact markdown structure below:

```markdown
## 🎯 Context & Objective
* **Trigger:** [State the original user requirement or system prompt]
* **Objective:** [Briefly describe what this PR achieves]

## 🧠 Knowledge Context Alignment
* **Current Phase:** Coding -> Awaiting Code Review
* **Context Updates:** [Explain how this PR updates the global Knowledge Manager state. E.g., "Added auth.go to source_code context."]

## ⚙️ Technical Implementation
* [Detail 1: e.g., Created `auth.go` to handle JWT validation]
* [Detail 2: e.g., Updated tests to cover edge cases]

## 🧪 Validation & Tests
* **Test Command Executed:** `[Insert command, e.g., go test ./...]`
* **Test Results:** [Pass / Fail summary]

## ⚠️ Human Review Request (HITL)
[List specific questions for the human architect, or write "Standard review required."]