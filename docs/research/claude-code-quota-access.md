# Claude Code: reading subscription quota locally

## Question

Can Stream Micro obtain a user's Claude Code Pro/Max usage-limit state directly
from the local CLI or a supported API, instead of scraping the Claude website or
reusing browser cookies?

## Conclusion

**Yes from the local Claude Code runtime; no through a documented public
individual-subscription REST endpoint.** Claude Code exposes the account's
five-hour and seven-day limits to a configured status-line command as structured
JSON. This is the best supported source for a local Stream Deck bridge.

The interactive `/usage` command also shows plan limits. It can be dispatched
through the Claude Agent SDK, but its local-command result is documented as a
text `content` field, not as a stable quota JSON schema. It is therefore a useful
manual or low-frequency fallback, not the preferred parser contract.

Anthropic's Admin Usage and Cost APIs are a different system: they report
organization/API usage and cost, require organization-admin credentials, and do
not expose an individual Pro/Max account's remaining rolling quota.

Checked against official Anthropic documentation on 2026-08-02.

## Supported local surfaces

### 1. Structured status-line input (recommended)

Claude Code runs the command configured at `statusLine.command` with a JSON
object on standard input. For Claude.ai Pro/Max subscribers, after the first API
response in a session, that object can contain:

```json
{
  "rate_limits": {
    "five_hour": {
      "used_percentage": 23.5,
      "resets_at": 1738425600
    },
    "seven_day": {
      "used_percentage": 41.2,
      "resets_at": 1738857600
    }
  }
}
```

The official field contract is:

- `rate_limits.five_hour.used_percentage` and
  `rate_limits.seven_day.used_percentage`: consumed percentage from 0 to 100.
- `rate_limits.five_hour.resets_at` and
  `rate_limits.seven_day.resets_at`: Unix epoch reset time.
- `rate_limits` is documented only for Claude.ai Pro/Max subscribers and is
  absent until the first API response. Either window can be independently
  absent.

Claude Code normally invokes the status-line command on event-driven refreshes;
`refreshInterval` can re-run it at a minimum interval of one second. The command
requires workspace trust, and `disableAllHooks: true` disables it. See the
official [status-line JSON fields and rate-limit examples](https://code.claude.com/docs/en/statusline#rate-limit-usage)
and [status-line configuration](https://code.claude.com/docs/en/statusline).

For Stream Micro, the collector should atomically write only the four quota
values plus an `updated_at` timestamp to a local cache. The bridge can read that
cache as often as it needs without making network requests. The UI should mark
the data stale when no Claude Code session has supplied a recent update.

This mechanism observes active Claude Code sessions; it is not an independent
account polling endpoint. A periodic status-line refresh re-runs the collector,
but it does not guarantee that Claude Code has fetched newer server-side quota
data since the last model response.

### 2. `/usage` in Claude Code

Inside an interactive Claude Code session:

```text
/usage
```

The official command reference says `/usage` shows session cost, plan usage
limits, and activity statistics; `/cost` and `/stats` are aliases. On Pro, Max,
Team, and Enterprise it also includes feature-usage breakdowns. See the official
[`/usage` command reference](https://code.claude.com/docs/en/commands#all-commands)
and [cost tracking guide](https://code.claude.com/docs/en/costs#using-the-usage-command).

For a programmatic local invocation, the Agent SDK supports dispatching slash
commands as prompts, and its initialization message lists the commands available
in that installed version. `usage` is an official example:

```python
async for message in query(
    prompt="/usage",
    options=ClaudeAgentOptions(max_turns=1),
):
    ...
```

The CLI's `-p`/`--print` mode is the corresponding non-interactive programmatic
surface, so a bridge can equivalently launch a one-shot command such as:

```text
claude -p "/usage" --output-format stream-json --verbose
```

The bridge must confirm that `usage` appears in the session's
`system/init.slash_commands`, because only commands supported without an
interactive terminal are dispatchable. See [Slash commands in the Agent SDK](https://code.claude.com/docs/en/agent-sdk/slash-commands)
and the [`-p` CLI reference](https://code.claude.com/docs/en/cli-usage).

The SDK models `/usage` output as `SDKLocalCommandOutputMessage` with a string
`content` field. Anthropic does not document a versioned, structured schema for
the quota rows inside that string. Parsing it is therefore more brittle than
reading `statusLine.rate_limits`. See the [TypeScript Agent SDK message types](https://code.claude.com/docs/en/agent-sdk/typescript#sdklocalcommandoutputmessage).

This is a supported technical capability, but it is not the recommended Stream
Micro integration path. Anthropic requires third-party Agent SDK products to
use API-key authentication unless separately approved; a bridge must not reuse
a subscriber's OAuth credentials to launch SDK requests. The status-line feed
avoids that problem because the user's native Claude Code process invokes the
collector itself.

### 3. Agent SDK rate-limit events

The Agent SDK also emits structured `RateLimitEvent`/`SDKRateLimitEvent`
messages. The documented state includes:

- status: `allowed`, `allowed_warning`, or `rejected`;
- limit type: `five_hour`, `seven_day`, `seven_day_opus`,
  `seven_day_sonnet`, or `overage`;
- utilization from 0.0 to 1.0 and a Unix reset timestamp when available.

These are event-driven session messages: the Python reference says they are
emitted when rate-limit status changes, and the TypeScript reference describes
them as emitted when the session encounters a limit. They are useful while a
bridge already owns an SDK session, but are not documented as a standalone
read-only snapshot request. See the official [Python `RateLimitEvent` and
`RateLimitInfo` reference](https://code.claude.com/docs/en/agent-sdk/python#ratelimitevent)
and [TypeScript `SDKRateLimitEvent` reference](https://code.claude.com/docs/en/agent-sdk/typescript#sdkratelimitevent).

## Authentication and plan boundaries

- `claude auth status` reports login state as JSON and exits 0 when logged in;
  it does **not** document quota fields. It is suitable for connection health
  and login-method detection only. See the [CLI command reference](https://code.claude.com/docs/en/cli-usage#cli-commands).
- Subscription OAuth from `/login` is the default for Pro, Max, Team, and
  Enterprise. If `ANTHROPIC_API_KEY` is present and approved, it takes
  precedence and routes usage to API billing instead of the subscription.
  See [Claude Code authentication precedence](https://code.claude.com/docs/en/authentication#authentication-precedence).
- `claude setup-token` creates a long-lived token for scripts on Pro, Max,
  Team, or Enterprise, but Anthropic documents it as inference-scoped. It is
  not a published subscription-quota API credential. See [Generate a
  long-lived token](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token).
- Starting 2026-06-15, Agent SDK and `claude -p` use a separate monthly Agent
  SDK credit on subscription plans rather than the interactive Claude Code
  limit. This further argues against creating model requests merely to poll
  interactive quota. See [Use the Claude Agent SDK with your Claude plan](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).
- Anthropic states that OAuth is for native Anthropic applications and that,
  without prior approval, third-party developers may not offer Claude.ai login
  or rate limits in their products. Stream Micro should never extract the
  user's OAuth token or call undocumented account endpoints. See [Claude Code
  legal and compliance: authentication and credential use](https://code.claude.com/docs/en/legal-and-compliance#authentication-and-credential-use).

## Why the published APIs are not a Pro/Max quota source

Anthropic publishes these organization endpoints:

```text
GET /v1/organizations/usage_report/messages
GET /v1/organizations/cost_report
GET /v1/organizations/usage_report/claude_code
GET /v1/organizations/rate_limits
GET /v1/organizations/workspaces/{workspace_id}/rate_limits
```

The Messages Usage and Cost APIs report metered Claude API tokens and charges.
The Claude Code usage report returns daily organization analytics such as
sessions, token/model breakdowns, lines changed, commits, and pull requests. It
does not return remaining five-hour/seven-day capacity.

The Rate Limits API returns configured Messages API limits such as requests,
input tokens, and output tokens per minute for an organization or workspace. It
does not return a Pro/Max subscription's rolling usage percentage. Anthropic's
own guidance says to compare those configured values with the Usage and Cost
API when building organization-level alerting. See the official [Rate Limits
API](https://platform.claude.com/docs/en/manage-claude/rate-limits-api).

All require an Admin API key (`sk-ant-admin...`) in `x-api-key`, or where
supported an OAuth bearer token with `org:admin`. Anthropic explicitly says the
Admin API is unavailable for individual accounts. See the official [Admin API
authentication and account constraint](https://platform.claude.com/docs/en/manage-claude/admin-api),
[Usage and Cost API](https://platform.claude.com/docs/en/manage-claude/usage-cost-api),
and [`claude_code` usage-report schema](https://platform.claude.com/docs/en/api/admin/usage_report).

No endpoint in Anthropic's published individual Claude.ai API documentation
returns a Pro/Max user's current five-hour or weekly remaining allowance. An
internal endpoint discovered by inspecting Claude network traffic is not a
supported contract and must not be used by Stream Micro.

## Recommendation for Stream Micro

1. Add an opt-in Claude Code quota collector under the configuration tab.
2. Prefer the official `statusLine.rate_limits` JSON feed and preserve or chain
   any status-line command the user already configured.
3. Cache `five_hour` and `seven_day` percentages/reset times atomically, record
   freshness, and make the Deck renderer read that cache.
4. Use `claude auth status` only to show whether the local CLI is logged in and
   whether subscription OAuth or API-key billing is active.
5. Keep `/usage` as a user-run diagnostic. Do not integrate Agent SDK/print-mode
   subscription polling without Anthropic approval, and do not treat its display
   text as a stable API.
6. For API-key organizations, keep API usage/cost reporting as a separately
   labelled Console/API feature. Never present it as Pro/Max subscription quota.
7. Do not request browser cookies, read stored OAuth tokens, or call an
   undocumented Claude.ai endpoint.

This design gives the local bridge real quota data through a documented Claude
Code extension surface while respecting the boundary between subscription usage
and Anthropic Console API billing.
