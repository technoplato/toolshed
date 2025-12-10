# Agents & AI Guidelines

This file serves as the primary source of truth for Agents and AI assistants working on this repository.

## Guiding Principles

1.  **Instantaneous Feedback**: Getting feedback for a piece of code should take as little time and effort as possible. Aim for instantaneous verification (like Wallaby.js).
2.  **Verify with Code**: Agents should be confident but must **verify hypotheses with code**. Do not just guess; write a script, run a test, or check the system state to confirm your assumptions.
3.  **CLI Bias**: Bias towards using tools that allow for CLI interactions. This enables agents to do more work programmatically.
4.  **Clean Git State**: Always check `git status` before starting work. Anticipate changes, perform them, and then verify the resulting `git status` matches expectations.

## Documentation Standards (Who, What, When, Where, Why, How)

Every source code file (Python, TypeScript, React, Scripts, etc.) MUST start with a comprehensive documentation block (Docstring in Python, Block comment in JS/TS).

**Crucial:** Do not just fill in the blanks. Write for the next developer (or future you) who has zero context.

**Format:**

````text
HOW:
  [Quick Start / Usage command]
  (e.g., `uv run my_script.py --arg value`)

  [Inputs]
  - [Argument 1]: [Description]
  - [Environment Variable]: [Description]

  [Outputs]
  - [File/Console Output]: [Description]

  [Side Effects]
  - [Network calls, File system changes, etc.]

WHO:
  [Agent Name], [User Name]
  (Context: [Brief context of creation, e.g. "Refactoring Auth"])

WHAT:
  [High-level summary of the file's purpose]
  [Detailed description of what it does]

WHEN:
  [Created Date (YYYY-MM-DD)]
  Last Modified: [Date]
  [Change Log:
    - [Date]: [Change description]
  ]

WHERE:
  [File Path]

WHY:
  [The "Why". Why does this exist? What problem does it solve?]
  [Design Rationale / Trade-offs]
### Examples: The Good, The Bad, and The Ugly

**❌ The Bad (Lazy, Unhelpful):**
```text
WHO:  Antigravity
WHAT: Uploads a file.
WHEN: 2025-12-05
WHERE: utils/upload.py
WHY:  To upload things.
````

**❌ The Ugly (Incomplete):**

```text
WHO:  Antigravity, User
WHAT: Helper for S3.
      [Inputs] - file
      [Outputs] - url
WHEN: 2025-12-05
WHERE: utils/upload.py
WHY:  Need S3 support.
```

**✅ The Good (Gold Standard):**

```text
HOW:
  `uv run utils/s3_uploader.py --bucket my-bucket data/image.png`

  [Inputs]
  - file_path: Path to the local file to upload.
  - --bucket: Target S3 bucket name.
  - AWS_ACCESS_KEY_ID (env): Required for auth.

  [Outputs]
  - Prints the public URL of the uploaded file to stdout.
  - Returns exit code 0 on success, 1 on failure.

  [Side Effects]
  - Uploads a file to AWS S3.
  - Generates a public URL.

WHO:
  Antigravity, User
  (Context: Implementing User Avatar Upload feature)

WHAT:
  A standalone utility to upload files to S3 with content-type detection.
  It handles authentication via environment variables and supports different regions.

WHEN:
  2025-12-05
  Last Modified: 2025-12-05
  [Change Log:
    - 2025-12-05: Initial creation with basic S3 support.
  ]

WHERE:
  utils/s3_uploader.py

WHY:
  To provide a unified way to handle file uploads without duplicating boto3 logic across services.
  We chose boto3 directly over a wrapper library for better control over retries.
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

## Code Style Guidelines

### Comment Placement

Comments MUST be placed **ABOVE** the code they describe, **NEVER to the right**.

Use multi-line `/** */` style comments for detailed explanations. Include examples where helpful.

**❌ BAD (Comments to the right):**

```typescript
start_time: i.number().indexed(),  // For range queries
embedding_id: i.string().optional(), // Links to Postgres
```

**✅ GOOD (Comments above):**

```typescript
/**
 * Start time of the segment in seconds.
 * Indexed to enable range queries like:
 *   where: { start_time: { $lte: currentTime } }
 */
start_time: i.number().indexed(),

/**
 * Reference to the voice embedding in PostgreSQL (pgvector).
 * Used for speaker identification by comparing to known speaker centroids.
 */
embedding_id: i.string().optional(),
```

### Schema Documentation

When defining database schemas:

1. Add a header section explaining design principles and entity relationships
2. Document each entity with its relationships inline
3. Include business logic explanations where relevant
4. Provide concrete examples in link documentation

## Environment & Tools

- **Python**: Use `uv` for dependency management.
- **Database**: InstantDB for everything possible.
- **React**: Use Vite for new apps.
- **Typescript**: Use bun when possible. If issues arise, use plain npm.

## Reference Libraries (Submodules)

The `references/` directory contains git submodules of external libraries that agents can explore for documentation, patterns, and implementation details.

### Available References

| Library                           | Path                                        | Description                                                                                                   |
| --------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **swift-composable-architecture** | `references/swift-composable-architecture/` | Point-Free's TCA library for building Swift applications with composition, testing, and ergonomics.           |
| **swift-sharing**                 | `references/swift-sharing/`                 | Point-Free's library for sharing state across features in a composable way.                                   |
| **swift-dependencies**            | `references/swift-dependencies/`            | Point-Free's dependency injection library with `@Dependency` macro for live/test/preview environments.        |
| **isowords**                      | `references/isowords/`                      | Point-Free's open-source word game showcasing TCA, swift-sharing, and swift-dependencies in a production app. |
| **apple-speech-to-text-sample**   | `references/apple-speech-to-text-sample/`   | Apple's sample code for "Bringing Advanced Speech-to-Text Capabilities to Your App".                          |

### How to Use

Agents can read local documentation and source code from these submodules:

```bash
# Explore TCA documentation
ls references/swift-composable-architecture/Sources/
cat references/swift-composable-architecture/README.md

# Explore swift-sharing
ls references/swift-sharing/Sources/
cat references/swift-sharing/README.md

# Explore swift-dependencies
ls references/swift-dependencies/Sources/
cat references/swift-dependencies/README.md

# Explore isowords (production TCA app)
ls references/isowords/Sources/
cat references/isowords/README.md

# Explore Apple's Speech-to-Text sample
ls references/apple-speech-to-text-sample/SwiftTranscriptionSampleApp/
cat references/apple-speech-to-text-sample/README.md
```

### Key Documentation Locations

- **TCA**: `references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/`
- **Sharing**: `references/swift-sharing/Sources/Sharing/Documentation.docc/`
- **Dependencies**: `references/swift-dependencies/Sources/Dependencies/Documentation.docc/`
- **isowords**: `references/isowords/` (full production app with TCA patterns)
- **Apple Speech Sample**: `references/apple-speech-to-text-sample/SwiftTranscriptionSampleApp/` (source code with inline documentation)

These references are useful when working on Swift projects that use TCA patterns or need state sharing solutions.
