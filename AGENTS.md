# Agents & AI Guidelines

This file serves as the primary source of truth for Agents and AI assistants working on this repository.

## Guiding Principles

1.  **Instantaneous Feedback**: Getting feedback for a piece of code should take as little time and effort as possible. Aim for instantaneous verification (like Wallaby.js).
2.  **Verify with Code**: Agents should be confident but must **verify hypotheses with code**. Do not just guess; write a script, run a test, or check the system state to confirm your assumptions.
3.  **CLI Bias**: Bias towards using tools that allow for CLI interactions. This enables agents to do more work programmatically.
4.  **Clean Git State**: Always check `git status` before starting work. Anticipate changes, perform them, and then verify the resulting `git status` matches expectations.

## Documentation Standards (Who, What, When, Where, Why)

Every source code file (Python, TypeScript, React, Scripts, etc.) MUST start with a comprehensive documentation block (Docstring in Python, Block comment in JS/TS).

**Format:**

```text
WHO:   [Agent Name/Version], [User Name]
       (Context: What conversation/task was this created in?)

WHAT:  [Description of the file's purpose]
       [Inputs]
       [Outputs]
       [Side Effects]
       [How to run/invoke it]
       (Example usage should be copy-pasteable)

WHEN:  [Created Date]
       [Last Modified Date]
       [Change Log:
        - YYYY-MM-DD: Initial creation
        - YYYY-MM-DD: Added feature X]

WHERE: [Known usages]
       [Deployment location - or "Not deployed yet"]

WHY:   [Reason for existence - e.g., "Playground for speaker diarization", "Fixing bug X"]
       [Design decisions/Rationale]
```

## Workflows

### Progress Tracking

- Maintain `PROGRESS.md` at the root.
- Maintain a global progress log at `~/.agents/progress.md`.
- Add an entry for every significant decision, question, answer, or code change.
- Use the `scripts/update_progress.py` script to append entries.
- **Setup**:
  - Ensure `uv` and `gh` are installed.
  - Add the script to your PATH or symlink it:
    ```bash
    ln -s $(pwd)/scripts/update_progress.py ~/.local/bin/update_progress
    ```
- **Commit Flow**:
  1. Make changes.
  2. **Ask the user to verify/check changes.**
  3. Update `PROGRESS.md` (using the script).
  4. Commit relevant changes.
  5. Amend commit if needed to ensure `PROGRESS.md` is included and message is correct.

### Task Management

- Maintain `TASKS.md` at the root.
- Sections: **Today**, **Short Term**, **Long Term**.
- Keep this synchronized with the Agent's internal task state.
- **Usage Guide**:
  - **Today**: Tasks for the current session.
  - **Right Now**: The single immediate focus.
  - **Short Term**: Tasks for the next few days.
  - **Long Term**: Future goals.
  - _Agents must update TASKS.md as progress is made._

## Environment & Tools

- **Python**: Use `uv` for dependency management.
- **Database**: InstantDB for everything possible.
- **React**: Use Vite for new apps.
- **Typescript**: Use bun when possible. If issues arise, use plain npm.
