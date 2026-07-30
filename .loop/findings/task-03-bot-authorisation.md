# PSR bot authorisation assessment — task-03

**Conclusion: blocked.** `github-actions[bot]` receives `contents: write` in the release job, despite the repository default being read-only. It therefore has token permission to create the release commit and tag. It cannot update `master`: the active repository ruleset applies a pull-request rule to the default branch and has no bypass actors. The attempted release job already failed at its Release step. No setting was changed for this assessment.

**Scope and capture time.** Read-only GitHub API queries were made on 2026-07-30 at 08:31 UTC. The checked repository is `marcellovictorino/local-whisper`, URL `https://github.com/marcellovictorino/local-whisper`, with default branch `master`. Its owner is the user account `marcellovictorino`, not an organisation.

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

The repository enables Actions and permits all actions. Its default `GITHUB_TOKEN` permission is `read`, but the checked workflow at commit `239e93ce5293800fe5bec9eda5fda315ee24344d` explicitly requests a job-level override:

```yaml
release:
  if: github.event_name == 'push' && github.ref == 'refs/heads/master'
  permissions:
    contents: write
```

That job-level declaration reconciles the read default: the release job has the requested repository-contents write scope, so token scope is not the blocker. `can_approve_pull_request_reviews: false` is unrelated because the job attempts a git push, not a pull-request approval.

## Authorisation decision

`github-actions[bot]` **cannot push the release commit to `master` under the recorded configuration**. The job's `contents: write` authorises repository-content writes, but it does not bypass the active `pull_request` ruleset; `bypass_actors` is empty. The bot cannot complete the PSR release push, so it cannot complete the release commit-and-tag publication sequence. A tag is not itself a `master` branch update, but that does not make the release sequence viable when its required release-commit push is rejected.

This conclusion is consistent with the observed release job from workflow run `30523425017`: job `90809308080` completed with `conclusion: failure`, and its `Release` step failed. The API job query was:

```console
$ gh api repos/marcellovictorino/local-whisper/actions/runs/30523425017/jobs --paginate --jq '.jobs[] | select(.name == "release") | {id, name, conclusion, started_at, completed_at, steps}'
{"completed_at":"2026-07-30T07:38:56Z","conclusion":"failure","id":90809308080,"name":"release","started_at":"2026-07-30T07:38:09Z","steps":[{"completed_at":"2026-07-30T07:38:10Z","conclusion":"success","name":"Set up job","number":1,"started_at":"2026-07-30T07:38:09Z","status":"completed"},{"completed_at":"2026-07-30T07:38:50Z","conclusion":"success","name":"Build python-semantic-release/python-semantic-release@39dd2052f2ce8282a5d932c31d58a2ca06d2550e","number":2,"started_at":"2026-07-30T07:38:10Z","status":"completed"},{"completed_at":"2026-07-30T07:38:51Z","conclusion":"success","name":"Run actions/checkout@11d5960a326750d5838078e36cf38b85af677262","number":3,"started_at":"2026-07-30T07:38:50Z","status":"completed"},{"completed_at":"2026-07-30T07:38:54Z","conclusion":"failure","name":"Release","number":4,"started_at":"2026-07-30T07:38:51Z","status":"completed"},{"completed_at":"2026-07-30T07:38:54Z","conclusion":"success","name":"Post Run actions/checkout@11d5960a326750d5838078e36cf38b85af677262","number":8,"started_at":"2026-07-30T07:38:54Z","status":"completed"},{"completed_at":"2026-07-30T07:38:55Z","conclusion":"success","name":"Complete job","number":9,"started_at":"2026-07-30T07:38:55Z","status":"completed"}]}
```

No branch-protection, ruleset, bypass, Actions-permission, or repository-permission setting was changed. All evidence collection used `gh repo view` and `gh api` GET requests.
