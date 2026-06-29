---
name: implement-slices
description: Implement feature slices from /to-issues. Writes code with /clean-code, runs tests, invokes /feature-slice-reviewer, commits to GitHub, updates task list.
---

Implement feature slices one by one with testing, code review, and git commits.

## ⚠️ NON-NEGOTIABLE REQUIREMENT

**GitHub commit to remote is MANDATORY after every feature slice.** After each slice passes clean code review:
1. GitHub remote MUST be configured (`git remote -v`)
2. Code MUST be committed: `git commit -m "[Slice N] <slice-title>"`
3. Commit MUST be pushed to remote: `git push origin <branch-name>`

This is a hard requirement for EVERY feature slice, with no exceptions. If GitHub is not configured, configure it before proceeding.

## Workflow

For each feature slice (in order, respecting dependencies):

1. **Show task list** - Display all slices with current status
2. **Mark in-progress** - Update task as currently being worked on
3. **Write code** - Follow /clean-code principles for implementation
4. **Run tests** - Execute relevant test suite
5. **Review** - Invoke /feature-slice-reviewer agent for code review
6. **If approved** → **COMMIT TO REMOTE GITHUB (NON-NEGOTIABLE)**, mark task completed
7. **If changes needed** → Apply feedback, re-test, and re-review

## Key Features

- **Sequential**: One slice at a time in dependency order
- **Clean code**: Applies /clean-code principles during implementation
- **Automated review**: /feature-slice-reviewer checks quality before commit
- **Task tracking**: Updates task list after each slice
- **Git integration**: Commits with slice info and test results
- **Dependency respect**: Skips blocked slices, resumes when blocker completes

## Requirements

- **GitHub repository MUST be configured** - Remote origin must be set and accessible (`git remote -v`)
- Test suite available
- requirements.txt with dependencies
- Working directory: project root

## GitHub Configuration Check

Before starting: `git remote -v` must show an origin URL. If missing, configure now:
```bash
git remote add origin https://github.com/user/repo.git
git remote -v  # verify
```
