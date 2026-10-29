# SyncnextSkill Repository Contract

## Repository Role

This is the passive publication repository for `qoli/syncnext-control`. The
maintained source is [`../Syncnext/Skills/syncnext-control`](../Syncnext/Skills/syncnext-control).
Follow [`../Syncnext/AGENTS.md`](../Syncnext/AGENTS.md) when working on that source.

`SKILL.md`, `README.md`, `references/`, and `scripts/` are synchronized publication
outputs. Do not maintain a second implementation or documentation source here.

## Changes and Commits

- Handle Skill issues, client fixes, API documentation, and wording changes in the
  Syncnext source directory, including requests originating from this repository's
  GitHub issues.
- A routine request to modify, fix, validate, or `git commit` a Skill change applies
  to the source repository. It does not authorize editing the synchronized output
  here or creating a second manual commit in this repository.
- Do not manually copy, stage, commit, or push synchronized files here as part of
  routine source maintenance. Use the owning publication workflow when publication
  is authorized.
- Direct repository maintenance requires an explicit request identifying that
  work. This `AGENTS.md` is repository-owned policy and may be maintained here when
  requested; that exception does not authorize changes to synchronized content.

## Publication

The owning publisher is
[`../Syncnext/Scripts/publish_syncnext_skill.py`](../Syncnext/Scripts/publish_syncnext_skill.py).
Run it from the Syncnext repository only when the user has authorized publication.
It copies the App's Git-tracked Skill files, tests a candidate, synchronizes the
destination, and creates a commit when content changes. Its commit message is
`🔄 chore(skill): sync from Syncnext <App HEAD>`.

The publisher always attempts to push to the destination's configured upstream,
even when no new commit is needed. It is not a read-only check or dry run. Fastlane
`ios release` and `ios test` also invoke it; neither lane is routine validation.

The destination must be clean and have an upstream. Preserve and report local
changes or publication failures; do not create manual commits, discard work, or
rewrite history merely to make publication proceed. See [README.md](README.md#維護)
for the maintained publication instructions.

## Validation

Run relevant checks in the Syncnext source repository:

- Client behavior: `python3 Tests/LocalAgent/test_client.py`.
- Publication behavior: `python3 Scripts/test_publish_syncnext_skill.py`, which uses
  temporary Git repositories and local remotes.

Validation does not authorize publication or an additional commit here.
