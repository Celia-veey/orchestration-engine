---
name: GitHub_PR_Delivery
description:
  Use this skill when asked to create a pull request (PR). It ensures all PRs
  follow the repository's established templates and standards.
---

# Pull Request Creator

This skill guides the creation of high-quality Pull Requests that adhere to the
repository's standards.

## Workflow

Follow these steps to create a Pull Request:

0.  **Task Branch Discovery**: Before creating or switching branches, check if a
    relevant branch already exists for the current task.
    - Extract keywords from the task description (e.g., "add user auth" →
      `user-auth`).
    - Search for existing branches:
      ```bash
      git branch -r | grep -i "<task-keyword>"
      ```
    - **Decision**:
      - **If a relevant branch exists**: Ask the user if they want to checkout
        and continue working on it.
      - **If no relevant branch found**: Proceed to Step 1.

1.  **Branch Management**: **CRITICAL:** Ensure you are NOT working on the
    `main` branch.
    - Run `git branch --show-current`.
    - If the current branch is `main`, you MUST create and switch to a new
      descriptive branch:
      ```bash
      git checkout -b <new-branch-name>
      ```
    - Branch naming convention: `<type>/<short-description>` (e.g.,
      `feat/add-user-auth`, `fix/resolve-crash`).

2.  **Commit Changes**: Verify that all intended changes are committed.
    - Run `git status` to check for unstaged or uncommitted changes.
    - If there are uncommitted changes, stage and commit them with a descriptive
      message before proceeding. NEVER commit directly to `main`.
      ```bash
      git add .
      git commit -m "type(scope): description"
      ```

3.  **Locate Template**: Search for a pull request template in the repository.
    - Check `pull_request_template.md`
    - If multiple templates exist ,
      ask the user which one to use or select the most appropriate one based on
      the context (e.g., `bug_fix.md` vs `feature.md`).

4.  **Read Template**: Read the content of the identified template file.

5.  **Draft Description**: Create a PR description that strictly follows the
    template's structure.
    - **Headings**: Keep all headings from the template.
    - **Checklists**: Review each item. Mark with `[x]` if completed. If an item
      is not applicable, leave it unchecked or mark as `[ ]` (depending on the
      template's instructions) or remove it if the template allows flexibility
      (but prefer keeping it unchecked for transparency).
    - **Content**: Fill in the sections with clear, concise summaries of your
      changes.
    - **Related Issues**: Link any issues fixed or related to this PR (e.g.,
      "Fixes #123").

6.  **Preflight Check**: Before creating the PR, run the workspace preflight
    script to ensure all build, lint, and test checks pass.
    ```bash
    npm run preflight
    ```
    If any checks fail, address the issues before proceeding to create the PR.

7.  **Push Branch**: Push the current branch to the remote repository.
    **CRITICAL SAFETY RAIL:** Double-check your branch name before pushing.
    NEVER push if the current branch is `main`.
    ```bash
    # Verify current branch is NOT main
    git branch --show-current
    # Push non-interactively
    git push -u origin HEAD
    ```

8.  **PR Idempotency Check**: Before creating a PR, verify if one already exists
    for the current branch.
    - Check for existing open PRs:
      ```bash
      gh pr list --head <current-branch> --state open --json number,title,url
      ```
    - **Decision Matrix**:
      - **Case A (No open PR found)**: Proceed to create a new PR (Step 9).
      - **Case B (Open PR exists)**: DO NOT create a new PR. Instead:
        1. Inform the user that a PR already exists with its URL.
        2. **Update PR Description**: If the changes are substantial (new files,
           significant logic changes), update the PR description to reflect the
           latest state:
           ```bash
           gh pr edit <PR_NUMBER> --body-file <updated_description_file>
           ```
        3. **Add Comment**: Notify reviewers that the PR has been updated:
           ```bash
           gh pr comment <PR_NUMBER> --body "Updated with latest changes. Summary: <brief-description>"
           ```
        4. Skip Step 9.

9.  **Create PR**: Use the `gh` CLI to create the PR. To avoid shell escaping
    issues with multi-line Markdown, write the description to a temporary file
    first.
    ```bash
    # 1. Write the drafted description to a temporary file
    # 2. Create the PR using the --body-file flag
    gh pr create --title "type(scope): succinct description" --body-file <temp_file_path>
    # 3. Remove the temporary file
    rm <temp_file_path>
    ```
    - **Title**: Ensure the title follows the
      [Conventional Commits](https://www.conventionalcommits.org/) format if the
      repository uses it (e.g., `feat(ui): add new button`,
      `fix(core): resolve crash`).

## Principles

- **Safety First**: NEVER push to `main`. This is your highest priority.
- **Compliance**: Never ignore the PR template. It exists for a reason.
- **Completeness**: Fill out all relevant sections.
- **Accuracy**: Don't check boxes for tasks you haven't done.