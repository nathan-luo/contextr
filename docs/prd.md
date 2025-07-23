Of course. Here is the complete and finalized Product Requirements Document.

# contextr Product Requirements Document (PRD)

## Goals and Background Context

### Goals (Revised)

- To evolve `contextr` from a simple file bundler into an intelligent context manager.
- To significantly improve workflow efficiency for developers who use LLMs for multiple, distinct tasks.
- To empower users to define, save, and instantly load different "Context Profiles" for various development scenarios.
- To enable switching between complex file contexts with a single, memorable command.
- To improve the maintainability and robustness of the core implementation by refactoring key components to cleanly support the new Profiles feature.

### Background Context

The current version of `contextr` successfully addresses the basic need to bundle project files for an LLM. However, its reliance on a single, static context is a significant pain point for developers who frequently switch tasks. Manually reconfiguring watched and ignored files for each new task is inefficient and can lead to providing incomplete or irrelevant context to the AI, ultimately degrading the quality of assistance.

This PRD outlines the requirements for a "Context Profiles" feature. This system will allow users to save and load named sets of file patterns, transforming `contextr` into a dynamic, task-aware tool that streamlines the developer's workflow.

### Change Log

| Date       | Version | Description       | Author    |
| :--------- | :------ | :---------------- | :-------- |
| 23/07/2025 | 1.0     | Initial PRD Draft | John (PM) |

## Requirements

### Functional

1.  **FR1:** The system must provide a CLI command to save the current context (both watched file patterns and ignore patterns) to a persistent, named profile.
2.  **FR2:** The system must provide a CLI command to load a named profile, which will clear the current context and replace it with the one from the profile.
3.  **FR3:** The system must provide a CLI command to display a list of all currently saved profiles.
4.  **FR4:** The system must provide a CLI command to delete a specified profile.
5.  **FR5:** The process of loading a profile must be idempotent; loading the same profile multiple times will result in the same context.

### Non-Functional

1.  **NFR1:** All new commands must be integrated into the existing `Typer` CLI application, following its established conventions for arguments and help text.
2.  **NFR2:** The profile storage system must be file-based and self-contained within the project's `.contextr` directory, introducing no external database dependencies.
3.  **NFR3:** The new feature must not introduce any breaking changes to the existing `watch`, `ignore`, and `sync` command workflows.
4.  **NFR4:** The implementation must align with modern Python best practices by incorporating `Ruff` for linting/formatting and `Pyright` for strict type checking.
5.  **NFR5:** The feature must maintain the existing cross-platform support for Linux, macOS, and Windows.

## Technical Assumptions

### Repository Structure: Monorepo

The project will continue to be developed within a single repository, as it is a self-contained application.

### Service Architecture: Monolithic CLI Application

The new functionality will be integrated directly into the existing monolithic application structure, primarily within the `ContextManager` and `cli.py` modules. No microservices or external services are required.

### Testing Requirements: Unit + Integration

- All new functionality must be accompanied by unit tests using **`pytest`**.
- Integration tests will be required to ensure the new `profile` commands interact correctly with the file system and the application's state.
- Before code can be merged, it must pass a full quality suite, including: `ruff format`, `ruff check`, `pyright`, and `pytest`.

### Additional Technical Assumptions and Requests

- **State Management:** Profile data will be stored in a file-based system within the `.contextr` directory, following the existing pattern for `state.json`.
- **Framework:** The `Typer` framework will be used to implement the new CLI commands, ensuring consistency with the existing interface.
- **Dependencies:** All project dependencies will be managed using `uv`. Any new libraries must be added via `uv add` and recorded in `pyproject.toml`.

## Epic 1: Project Modernization & Foundation

**Epic Goal:** This epic focuses on improving the project's long-term health and developer experience. We will integrate a comprehensive suite of modern tooling for linting, formatting, and type-checking. We will also introduce a testing framework and refactor the core `ContextManager` to make it more modular and ready for new features, ensuring that all future development is built on a stable and maintainable foundation.

### Story 1.1: Integrate Ruff for Linting and Formatting

- **As a** developer,
- **I want** `Ruff` integrated into the project,
- **so that** code formatting and linting are automated and consistent.

**Acceptance Criteria:**

1.  `Ruff` is added as a development dependency in `pyproject.toml`.
2.  A `[tool.ruff]` configuration is added to `pyproject.toml` with rules for formatting, import sorting (`I`), and core pyflakes checks (`F`).
3.  The entire existing codebase is successfully formatted and linted using the new `Ruff` configuration.
4.  The project's contribution guidelines (`CLAUDE.md` or a new `CONTRIBUTING.md`) are updated with instructions on how to use `Ruff`.

### Story 1.2: Configure Pyright for Strict Type Checking

- **As a** developer,
- **I want** `Pyright` configured for strict type checking,
- **so that** I can catch type-related errors early and improve code reliability.

**Acceptance Criteria:**

1.  `Pyright` is added as a development dependency in `pyproject.toml`.
2.  A `[tool.pyright]` configuration is added to `pyproject.toml` enabling `strict` mode.
3.  All type errors in the existing codebase are resolved to satisfy the strict checking rules.
4.  The project's contribution guidelines are updated with instructions on how to run `Pyright`.

### Story 1.3: Set Up Pytest Framework

- **As a** developer,
- **I want** the `pytest` framework set up,
- **so that** I can write and run automated tests for the application.

**Acceptance Criteria:**

1.  `pytest` is added as a development dependency.
2.  A `tests/` directory is created.
3.  `pytest` can be executed successfully and discovers tests within the `tests/` directory.
4.  A simple unit test is created for a utility function (e.g., in `path_utils.py`) that passes when `pytest` is run.

### Story 1.4: Refactor ContextManager for Extensibility

- **As a** developer,
- **I want** the `ContextManager` refactored,
- **so that** its state-loading and saving logic can be easily extended to support profiles without modifying its core responsibilities.

**Acceptance Criteria:**

1.  The logic for reading from and writing to `state.json` is decoupled from the in-memory context management.
2.  The refactored `ContextManager` maintains all existing functionality.
3.  Unit tests are written for the `ContextManager`'s core state manipulation methods (e.g., `add_files`, `remove_files`).
4.  The class and its methods are documented to reflect the new internal structure.

## Epic 2: Context Profile Management

**Epic Goal:** This epic delivers the core user-facing "Context Profiles" feature. Building on the modernized foundation from Epic 1, we will implement the full lifecycle of profile management: creating, loading, listing, and deleting. The outcome will be a significantly more efficient workflow for developers, allowing them to switch between different task-specific contexts with a single command.

### Story 2.1: Save and List Context Profiles

- **As a** developer,
- **I want** to save my current context to a named profile and list all existing profiles,
- **so that** I can begin organizing and managing my different project contexts.

**Acceptance Criteria:**

1.  A new command, `ctxr profile save <profile-name>`, is implemented.
2.  Executing the `save` command creates a persistent record of the current session's `watched_patterns` and `ignore_patterns` under the given name.
3.  A new command, `ctxr profile list`, is implemented.
4.  Executing the `list` command displays a table of all saved profile names.
5.  Attempting to save a profile with a name that already exists will prompt the user for confirmation before overwriting.
6.  Unit tests are created to verify the profile saving and listing logic.

### Story 2.2: Load a Context Profile

- **As a** developer,
- **I want** to load a saved profile,
- **so that** I can instantly switch my active `contextr` configuration to match a specific task.

**Acceptance Criteria:**

1.  A new command, `ctxr profile load <profile-name>`, is implemented.
2.  Executing the `load` command first clears the application's current context (watched patterns, ignored patterns, and files).
3.  The command then populates the application's context from the specified profile.
4.  After a profile is loaded, the file list is immediately refreshed to reflect the new patterns.
5.  Executing `ctxr list` after loading a profile displays the correct set of files.
6.  The system provides a clear error message if the user tries to load a profile that does not exist.
7.  Unit tests are created to verify the profile loading mechanism.

### Story 2.3: Delete a Context Profile

- **As a** developer,
- **I want** to delete a saved profile,
- **so that** I can remove old or irrelevant contexts from my project.

**Acceptance Criteria:**

1.  A new command, `ctxr profile delete <profile-name>`, is implemented.
2.  The command prompts the user for confirmation before proceeding with the deletion.
3.  Executing the `delete` command permanently removes the specified profile.
4.  The deleted profile no longer appears in the output of `ctxr profile list`.
5.  The system provides a clear error message if the user tries to delete a profile that does not exist.
6.  Unit tests are created to verify the profile deletion logic.

## Checklist Results Report

### **Validation Summary**

- **Overall PRD Completeness:** 95%
- **MVP Scope Appropriateness:** Just Right
- **Readiness for Architecture Phase:** Ready
- **Most Critical Gaps:** None. One minor non-functional requirement could be added for completeness.

### **Category Analysis**

| Category                         | Status  | Critical Issues                                                                   |
| :------------------------------- | :------ | :-------------------------------------------------------------------------------- |
| 1. Problem Definition & Context  | PASS    | None                                                                              |
| 2. MVP Scope Definition          | PASS    | None                                                                              |
| 3. User Experience Requirements  | N/A     | Project is a CLI application.                                                     |
| 4. Functional Requirements       | PASS    | None                                                                              |
| 5. Non-Functional Requirements   | PARTIAL | No explicit security requirements for file storage (low risk, but good practice). |
| 6. Epic & Story Structure        | PASS    | None                                                                              |
| 7. Technical Guidance            | PASS    | None                                                                              |
| 8. Cross-Functional Requirements | N/A     | Self-contained CLI tool.                                                          |
| 9. Clarity & Communication       | PASS    | None                                                                              |
