# merge-babysitter-action

 Q: Why this and not native github auto-merge pool or existing merge actions?
 
 A: Testing takes time and github workflow has limited time budget - no point wasting it on active sleep.
   All I want is to rebase oldest labeled PR and let the github to the merge

# How this works
Out of all `approved` PR with ``ready for merge`` label pick the oldest which:
- Is ready to merge (mergeStateStatus is CLEAN) and merge it using `gh pr merge --rebase --auto`. Existing auto-merge setting is respected (so github should merge it fist).
This sets the 'Enable auto-merge (rebase)' so repo configuration is taken into account (required checks passing, resolved comments ...)

- Othewise rebases oldest PR (mergeStateStatus is BEHIND)
- Do nothing if any of above can be found

# Why this way?

1. The biggest pain/time consumer is to 'rebase' the PR and wait for test results. Automates that part.
2. The branch protection lives is same for the merge-babysitter as well as for people merging manually
3. One can set 'Enable auto-merge' manually (e.g to squash commits) and still use this action to do the rebase.

# How to use it in workflow?

Since this updates PR (rebase, automerge flag) this action needs token with 'write' permission.
You can either:
- Provide personal TOKEN with write permission
- Change repository Workflow permissions to 'Read and write' (Settings->Actions->General)

Then create worfklow yaml file in `.github/workflows/` and change the 'OWNER/REPO' to yours.

```yaml

name: Merge babysitter
on:
    pull_request:
        types:
        - labeled
        - opened
        - synchronize
        - review_request_
        - auto_merge_enabled
jobs:
    merge_or_rebase:
        runs-on: ubuntu-latest
        steps:
            - name: Set the auto-merge or rebase the PR
              uses: lukaszachy/merge-babysitter-action@v1
              env:
                GH_TOKEN: ${{ github.token }}
                REPO: "OWNER/REPO"
```

