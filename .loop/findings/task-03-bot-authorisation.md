# PSR bot authorisation assessment — task-03

## Plain-language result

**The automated release account cannot complete a release under the current rules.** It is allowed to write repository content, including attempting to create a release commit and tag, but it is not allowed to change `master`, the repository's main branch. The current rule requires changes to `master` to arrive through a pull request, and grants the automated account no exception. No setting was changed for this assessment.

An administrator should not rely on direct automated pushes while this rule remains. They need to choose one of two designs: make releases through a pull request, or explicitly approve, document, and narrowly limit an exception for the release bot. This report does not make either change.

**Scope and capture time.** Read-only GitHub API queries were made on 2026-07-30 at 08:31 UTC. The checked repository is `marcellovictorino/local-whisper`, URL `https://github.com/marcellovictorino/local-whisper`, with default branch `master`. Its owner is the user account `marcellovictorino`, not an organisation.

**Terms used below.** A *token* is the temporary credential supplied to a workflow. A *ruleset* is a repository rule that controls which changes GitHub accepts. A *bypass actor* is an account explicitly exempted from such a rule. A *pull request* is GitHub's reviewed-change route into the main branch.

## Commands and responses

The following are the commands issued and their response bodies. For the two expected not-found responses, the HTTP status is retained; transport headers are omitted because they do not alter the policy result.

### Repository identity

```console
$ gh repo view marcellovictorino/local-whisper --json nameWithOwner,owner,url,defaultBranchRef
{"defaultBranchRef":{"name":"master"},"nameWithOwner":"marcellovictorino/local-whisper","owner":{"id":"MDQ6VXNlcjE4NjM2Njgw","login":"marcellovictorino"},"url":"https://github.com/marcellovictorino/local-whisper"}

$ gh api users/marcellovictorino --jq '{login,type,html_url}'
{"html_url":"https://github.com/marcellovictorino","login":"marcellovictorino","type":"User"}
```

### `master` branch protection and rulesets

```console
$ gh api -i repos/marcellovictorino/local-whisper/branches/master/protection
HTTP/2.0 404 Not Found
{"message":"Branch not protected","documentation_url":"https://docs.github.com/rest/branches/branch-protection#get-branch-protection","status":"404"}

$ gh api repos/marcellovictorino/local-whisper/rulesets
[{"id":15625854,"name":"master","target":"branch","source_type":"Repository","source":"marcellovictorino/local-whisper","enforcement":"active","node_id":"RRS_lACqUmVwb3NpdG9yec5I2eZLzgDubn4","_links":{"self":{"href":"https://api.github.com/repos/marcellovictorino/local-whisper/rulesets/15625854"},"html":{"href":"https://github.com/marcellovictorino/local-whisper/rules/15625854"}},"created_at":"2026-04-28T00:09:27.755+02:00","updated_at":"2026-04-28T00:09:56.136+02:00"}]

$ gh api repos/marcellovictorino/local-whisper/rulesets/15625854
{"id":15625854,"name":"master","target":"branch","source_type":"Repository","source":"marcellovictorino/local-whisper","enforcement":"active","conditions":{"ref_name":{"exclude":[],"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"deletion"},{"type":"non_fast_forward"},{"type":"pull_request","parameters":{"required_approving_review_count":0,"dismiss_stale_reviews_on_push":false,"required_reviewers":[],"require_code_owner_review":true,"require_last_push_approval":false,"required_review_thread_resolution":false,"allowed_merge_methods":["squash"]}},{"type":"copilot_code_review","parameters":{"review_on_push":true,"review_draft_pull_requests":false}}],"node_id":"RRS_lACqUmVwb3NpdG9yec5I2eZLzgDubn4","created_at":"2026-04-28T00:09:27.755+02:00","updated_at":"2026-04-28T00:09:56.136+02:00","bypass_actors":[],"current_user_can_bypass":"never","_links":{"self":{"href":"https://api.github.com/repos/marcellovictorino/local-whisper/rulesets/15625854"},"html":{"href":"https://github.com/marcellovictorino/local-whisper/rules/15625854"}}}

$ gh api repos/marcellovictorino/local-whisper/rules/branches/master
[{"type":"deletion","ruleset_source_type":"Repository","ruleset_source":"marcellovictorino/local-whisper","ruleset_id":15625854},{"type":"non_fast_forward","ruleset_source_type":"Repository","ruleset_source":"marcellovictorino/local-whisper","ruleset_id":15625854},{"type":"pull_request","parameters":{"required_approving_review_count":0,"dismiss_stale_reviews_on_push":false,"required_reviewers":[],"require_code_owner_review":true,"require_last_push_approval":false,"required_review_thread_resolution":false,"allowed_merge_methods":["squash"]},"ruleset_source_type":"Repository","ruleset_source":"marcellovictorino/local-whisper","ruleset_id":15625854},{"type":"copilot_code_review","parameters":{"review_on_push":true,"review_draft_pull_requests":false},"ruleset_source_type":"Repository","ruleset_source":"marcellovictorino/local-whisper","ruleset_id":15625854}]
```

The older branch-protection mechanism is absent, but that does not make `master` writable. The evaluated branch rules and active ruleset show that the repository ruleset applies to `~DEFAULT_BRANCH` (`master`), requires a pull request and lists no bypass actor. A direct bot push to `master` cannot meet that rule.

### Actions and `GITHUB_TOKEN` policy

```console
$ gh api repos/marcellovictorino/local-whisper/actions/permissions
{"enabled":true,"allowed_actions":"all","sha_pinning_required":false}

$ gh api repos/marcellovictorino/local-whisper/actions/permissions/workflow
{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}

$ gh api -i orgs/marcellovictorino/actions/permissions
HTTP/2.0 404 Not Found
{"message":"Not Found","documentation_url":"https://docs.github.com/rest/actions/permissions#get-github-actions-permissions-for-an-organization","status":"404"}
```

The organisation endpoint is unavailable because the repository owner is a `User`, as the identity response shows; no organisation Actions policy can govern this user-owned repository. There is no unqueried parent-organisation policy limitation in this ownership model.

The repository enables Actions and permits all actions. Its default `GITHUB_TOKEN` permission is `read`, but the release workflow records a job-level `contents: write` override and supplies that token to the release action. The following local Git command reproduces the exact workflow configuration assessed at the task's base commit. The base commit is local to this assessment branch and is not available from the public repository API, so `gh api .../contents?ref=239e93ce…` returns `404`; this is a retrieval limitation, not an unrecorded policy assumption.

```console
$ git show 239e93ce5293800fe5bec9eda5fda315ee24344d:.github/workflows/ci.yml
```

```yaml
  release:
    needs: ci
    if: github.event_name == 'push' && github.ref == 'refs/heads/master'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Release
        uses: python-semantic-release/python-semantic-release@39dd2052f2ce8282a5d932c31d58a2ca06d2550e # v10.6.1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          git_committer_name: "github-actions[bot]"
          git_committer_email: "github-actions[bot]@users.noreply.github.com"
```

This establishes the workflow-to-account chain: GitHub supplies `secrets.GITHUB_TOKEN`; the workflow passes it as `github_token` to Python Semantic Release; and the release commit is configured with the `github-actions[bot]` name and email. The job-level declaration overrides the read default for this job, so token scope is not the blocker. `can_approve_pull_request_reviews: false` is unrelated because the job attempts a git push, not a pull-request approval.

## Authorisation decision

`github-actions[bot]` **cannot push the release commit to `master` under the recorded configuration**. The job's `contents: write` authorises repository-content writes, but it does not bypass the active pull-request ruleset; `bypass_actors` is empty. The bot therefore cannot complete the PSR release commit-and-tag sequence. A tag is not itself a `master` branch update, but that does not make the sequence viable when its required release-commit push is refused.

This conclusion comes from the recorded ruleset and token-policy evidence alone; no workflow failure is used to attribute a cause.

No branch-protection, ruleset, bypass, Actions-permission, or repository-permission setting was changed. All GitHub evidence collection used `gh repo view` and `gh api` GET requests.
