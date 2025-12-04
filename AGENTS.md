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
WHO:
  [Agent Name/Version], [User Name]
  (Context: What conversation/task was this created in?)

WHAT:
  [Description of the file's purpose]
  [Inputs]
  [Outputs]
  [Side Effects]
  [How to run/invoke it]
  (Example usage should be copy-pasteable)

WHEN:
  [Created Date]
  [Last Modified Date]
  [Change Log:
    - YYYY-MM-DD: Initial creation
    - YYYY-MM-DD: Added feature X
  ]

WHERE:
  [Known usages]
  [Deployment location - or "Not deployed yet"]

WHY:
  [Reason for existence - e.g., "Playground for speaker diarization", "Fixing bug X"]
  [Design decisions/Rationale]
```

## Workflows

### Progress Tracking

- Maintain `progress.md` at the root (lowercase filename).
- Maintain a global progress log at `~/.agents/progress.md`.
- Add an entry for every significant decision, question, answer, or code change.
- **Always use the `scripts/update_progress.py` script** to append entries. Never edit progress files manually.

#### Using `update_progress.py`

**Setup:**

- Ensure `uv` and `gh` are installed.
- The script can be run directly: `./scripts/update_progress.py`
- Optionally add to PATH: `ln -s $(pwd)/scripts/update_progress.py ~/.local/bin/update_progress`

**Default Behavior:**

- **Agents MUST use the `--push` flag by default** unless the user explicitly requests otherwise.
- The `--push` flag ensures progress entries are linked to commits that include both the actual changes and the progress documentation.

**What Happens When You Run It:**

1. **Without `--push` flag:**

   - Updates `progress.md` with a new entry at the top
   - Updates `~/.agents/progress.md` with the same entry (includes project context)
   - Prints confirmation messages
   - Does NOT modify git state

2. **With `--push` flag (default for agents):**
   - Updates both progress files (local and global)
   - Stages `progress.md`
   - Amends the current commit (HEAD) to include `progress.md`
   - Updates the commit hash reference in the progress entry to point to the amended commit
   - Pushes to remote with `--force-with-lease` (safe force push)
   - Ensures the GitHub commit link shows both your changes AND the progress entry

**Example Usage:**

```bash
# Basic entry (updates files only, no git changes)
./scripts/update_progress.py --type feature --message "Added new authentication system" "Implemented OAuth2" "Added tests"

# With --push (default for agents - amends commit and pushes)
./scripts/update_progress.py --type feature --message "Added new authentication system" --push "Implemented OAuth2" "Added tests"

# Different entry types
./scripts/update_progress.py --type bug --message "Fixed memory leak" --push "Reduced memory usage by 40%"
./scripts/update_progress.py --type doc --message "Updated API documentation" --push
./scripts/update_progress.py --type decision --message "Chose React over Vue" --push "Better ecosystem support" "Team familiarity"
```

**Entry Types:**

- `feature`: ✨ New features
- `bug`: 🐛 Bug fixes
- `chore`: 🧹 Maintenance tasks
- `doc`: 📝 Documentation updates
- `wip`: 🚧 Work in progress
- `test`: ✅ Tests and verification
- `question`: ❓ Questions posed
- `answer`: 🗣️ Answers/discussions
- `decision`: 🧠 Decisions made
- `release`: 🚀 Releases/deployments

**Commit Flow:**

1. Make changes.
2. **Ask the user to verify/check changes.**
3. Commit your changes: `git add . && git commit -m "Your commit message"`
4. Update progress (with `--push` by default):
   ```bash
   ./scripts/update_progress.py --type <type> --message "Description" --push "Detail 1" "Detail 2"
   ```
5. The script automatically amends your commit to include `progress.md` and pushes.

**Important Notes:**

- The script uses human-readable dates (e.g., "December 1st, 2025 at 9:16:52 p.m.")
- Progress entries are formatted with date on first line, message on second line, commit link on third line
- Global log entries include project name and path for context
- The `--push` flag rewrites git history (amends commits). Use with caution on shared branches.

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
