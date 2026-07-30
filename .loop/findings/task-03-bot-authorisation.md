# PSR bot authorisation assessment — task-03

## Plain-language result

**The configured automated release cannot complete a release under the current rules.** Its `GITHUB_TOKEN` is allowed to write repository content, including attempting to create a release commit and tag, but it is not allowed to change `master`, the repository's main branch. The current rule requires changes to `master` to arrive through a pull request, and grants no bypass exception. No setting was changed for this assessment.

An administrator should not rely on direct automated pushes while this rule remains. They need to choose one of two designs: make releases through a pull request, or explicitly approve, document, and narrowly limit an exception for the release bot. This report does not make either change.

**Scope and capture time.** Read-only GitHub API queries were made on 2026-07-30 at 08:43 UTC. The checked repository is `marcellovictorino/local-whisper`, URL `https://github.com/marcellovictorino/local-whisper`, with default branch `master`. Its owner is the user account `marcellovictorino`, not an organisation.

**Terms used below.** Python Semantic Release (PSR) is the action that creates the version change. A *workflow job* is one isolated set of automated steps. `GITHUB_TOKEN` is GitHub's temporary credential for that job. A *release commit* records the generated version and changelog; a *tag* is Git's named reference to that release commit. A *ruleset* is a repository rule that controls which changes GitHub accepts. A *bypass actor* is an account explicitly exempted from such a rule. A *pull request* is GitHub's reviewed-change route into the main branch.

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

The repository enables Actions and permits all actions. Its default `GITHUB_TOKEN` permission is `read`, but the release workflow records a job-level `contents: write` override and supplies that token to the release action. The following local Git command reproduces the exact workflow configuration assessed at the task's base commit.

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

The job-level declaration overrides the read default for this job, so token scope is not the blocker. `can_approve_pull_request_reviews: false` is unrelated because the job attempts a git push, not a pull-request approval.

The base commit is local to this assessment branch and unavailable from the public repository API. The recorded retrieval result is a limitation only; the local Git output above remains the workflow evidence.

```console
$ gh api -i repos/marcellovictorino/local-whisper/contents/.github/workflows/ci.yml?ref=239e93ce5293800fe5bec9eda5fda315ee24344d
HTTP/2.0 404 Not Found
{"message":"No commit found for the ref 239e93ce5293800fe5bec9eda5fda315ee24344d","documentation_url":"https://docs.github.com/v3/repos/contents/","status":"404"}
```

### Authenticated principal and PSR push credential

The configured commit name and email are Git metadata, not proof of the credential used to push. The following primary-source evidence establishes the credential path separately.

GitHub's documentation says that `GITHUB_TOKEN` authenticates on behalf of GitHub Actions and may be passed to an action as an input:

```console
$ gh api repos/github/docs/contents/content/actions/tutorials/authenticate-with-github_token.md --jq .content | base64 --decode | grep '^intro:'
intro: Learn how to use the `GITHUB_TOKEN` to authenticate on behalf of {% data variables.product.prodname_actions %}.

$ gh api repos/github/docs/contents/content/actions/tutorials/authenticate-with-github_token.md --jq .content | base64 --decode | sed -n '29,38p'
This tutorial leads you through how to use the `GITHUB_TOKEN` for authentication in {% data variables.product.prodname_actions %} workflows, including examples for passing the token to actions, making API requests, and configuring permissions for secure automation.

For reference information, see [AUTOTITLE](/actions/reference/workflows-and-actions/workflow-syntax#permissions).

## Using the `GITHUB_TOKEN` in a workflow

You can use the `GITHUB_TOKEN` by using the standard syntax for referencing secrets: {% raw %}`${{ secrets.GITHUB_TOKEN }}`{% endraw %}. Examples of using the `GITHUB_TOKEN` include passing the token as an input to an action, or using it to make an authenticated {% data variables.product.github %} API request.

> [!IMPORTANT]
> An action can access the `GITHUB_TOKEN` through the `github.token` context even if the workflow does not explicitly pass the `GITHUB_TOKEN` to the action. As a good security practice, you should always make sure that actions only have the minimum access they require by limiting the permissions granted to the `GITHUB_TOKEN`. For more information, see [AUTOTITLE](/actions/reference/workflows-and-actions/workflow-syntax#permissions).
```

The GitHub Actions app and its bot account resolve to the same app page:

```console
$ gh api apps/github-actions --jq '{id,slug,name,html_url}'
{"html_url":"https://github.com/apps/github-actions","id":15368,"name":"GitHub Actions","slug":"github-actions"}

$ gh api 'users/github-actions%5Bbot%5D' --jq '{login,type,html_url}'
{"html_url":"https://github.com/apps/github-actions","login":"github-actions[bot]","type":"Bot"}
```

The pinned PSR action declares that its required `github_token` input pushes release notes and new commits and tags. Its pinned entrypoint exports that same input as `GH_TOKEN` before it runs PSR.

```console
$ gh api repos/python-semantic-release/python-semantic-release/contents/action.yml?ref=39dd2052f2ce8282a5d932c31d58a2ca06d2550e --jq .content | base64 --decode | sed -n '/  github_token:/,/^$/p'
  github_token:
    required: true
    description: GitHub token used to push release notes and new commits/tags

$ gh api repos/python-semantic-release/python-semantic-release/contents/src/gh_action/action.sh?ref=39dd2052f2ce8282a5d932c31d58a2ca06d2550e --jq .content | base64 --decode | grep -F 'export GH_TOKEN='
export GH_TOKEN="${INPUT_GITHUB_TOKEN}"
```

The workflow passes `secrets.GITHUB_TOKEN` to that required `github_token` input. Together with the GitHub Actions app and bot responses above, this establishes that the PSR push is authenticated by GitHub Actions as `github-actions[bot]`; the configured committer fields are corroborative metadata only.

## Authorisation decision

`github-actions[bot]` **cannot push the PSR release commit to `master` under the recorded configuration**. The job's `contents: write` authorises repository-content writes, but it does not bypass the active pull-request ruleset; `bypass_actors` is empty. The PSR action uses that `GITHUB_TOKEN` to push its release commit and tag, so it cannot complete the release commit-and-tag sequence when the required `master` update is refused. A tag is not itself a `master` branch update; this assessment does not claim that the ruleset independently rejects the tag.

This conclusion concerns the configured `GITHUB_TOKEN` path only. It does not assume whether an unconfigured personal access token or other credential could have a bypass. No workflow failure is used to attribute a cause.

No branch-protection, ruleset, bypass, Actions-permission, or repository-permission setting was changed. All GitHub evidence collection used `gh repo view` and `gh api` GET requests.
