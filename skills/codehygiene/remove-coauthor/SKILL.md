---
name: remove-coauthor
description: Remove Co-authored-by trailers from git commits. Use when the user asks to "remove co-author", "strip coauthor", "clean up commit trailers", or "remove AI co-author lines".
---

# Remove Co-authored-by from commits

Strip `Co-authored-by` trailer lines from git commit messages without affecting the code changes.

## Check scope

First, check whether there are any Co-authored-by lines to remove, and how many commits are affected:

```bash
git log main..HEAD --format="%H %B" | grep -B1 "^Co-authored-by:" | grep -c "^[0-9a-f]\{40\}"
```

If the count is 0, there's nothing to do — **stop here**.

To see which commits and which co-author lines:

```bash
git log main..HEAD --format="%h %s%n%B" | grep -B1 "^Co-authored-by:"
```

Review the output. Confirm this is the right range and the right set of commits before proceeding.

## Pre-flight checks

Before rewriting any history, run these checks:

### 1. Clean worktree

The worktree must be clean — no uncommitted changes, no staged files:

```bash
git status --porcelain
```

If this produces any output, **stop**. Commit or stash changes first.

### 2. Check for merge commits in the range

Rewriting merge commits can linearize history and break the merge topology. Check first:

```bash
git log --merges --oneline main..HEAD
```

If this shows any merge commits, **warn the user**: rewriting will change merge commit hashes and may linearize the branch history. The user should decide whether to proceed. If they only want to clean non-merge commits, use `--commit-filter` instead (see "Skipping merge commits" below).

### 3. Record tree hashes for verification

Save tree hashes before rewriting so you can verify only messages changed:

```bash
git log --format="%H %T" main..HEAD > /tmp/pre-rewrite-trees.txt
```

## Last commit only

```bash
git log -1 --format="%B" | sed '/^Co-authored-by:/d' | git commit --amend -F -
```

## Multiple commits on a branch

```bash
git filter-branch --msg-filter 'sed "/^Co-authored-by:/d"' main..HEAD
```

Or with `git-filter-repo` (faster, recommended for larger histories):

```bash
git filter-repo --message-callback 'return b"\n".join(l for l in message.splitlines() if not l.startswith(b"Co-authored-by:"))' --refs main..HEAD --force
```

## Skipping merge commits

To only rewrite non-merge commits (preserving merge topology exactly):

```bash
git filter-branch --msg-filter '
if [ "$GIT_COMMIT" = "$(git rev-parse --verify $GIT_COMMIT^2 2>/dev/null && echo merge || echo "")" ]; then
    cat
else
    sed "/^Co-authored-by:/d"
fi
' main..HEAD
```

Or more simply, rewrite only and let merge commits pass through unchanged — `filter-branch` preserves merge structure by default as long as you don't use `--commit-filter`. The concern is when parent hashes change, the merge commit gets a new hash too. This is cosmetic — the tree content is preserved.

## All commits in the repo

```bash
git filter-branch --msg-filter 'sed "/^Co-authored-by:/d"' -- --all
```

## Post-rewrite verification

After rewriting, verify that only commit messages changed and no code was affected:

### 1. Check worktree is still clean

```bash
git status --porcelain
```

Must produce no output.

### 2. Verify tree hashes are identical

Every commit's tree hash (the snapshot of files) must be the same before and after. Only the commit hashes should differ:

```bash
git log --format="%H %T" main..HEAD > /tmp/post-rewrite-trees.txt
diff <(awk '{print $2}' /tmp/pre-rewrite-trees.txt) <(awk '{print $2}' /tmp/post-rewrite-trees.txt)
```

If `diff` produces no output, the rewrite only touched messages. If it shows differences, something went wrong — restore from the backup refs.

### 3. Verify Co-authored-by lines are gone

```bash
git log main..HEAD --format="%B" | grep -c "^Co-authored-by:" 
```

Should return 0.

## Important

- These commands **rewrite history** — commit hashes will change.
- If the branch has already been pushed, you'll need `git push --force-with-lease` afterward.
- Only do this on branches you own. Don't rewrite shared/main branch history without coordinating with your team.
- `git filter-branch` leaves backup refs in `refs/original/`. Clean up with `git update-ref -d refs/original/refs/heads/<branch>` if needed.
- To restore if something went wrong: `git reset --hard refs/original/refs/heads/<branch>`
