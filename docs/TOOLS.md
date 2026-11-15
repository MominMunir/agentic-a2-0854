# MCP tool inventory

| Tool | Owner/server | Access | Annotations | Authentication |
| --- | --- | --- | --- | --- |
| search_jobs | marketplace | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| get_job | marketplace | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| get_client_history | marketplace | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| get_connects_balance | marketplace | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| list_messages | marketplace | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| create_proposal_draft | marketplace | write | destructiveHint=False / idempotentHint=True / openWorldHint=True / readOnlyHint=False | tenant bearer / scoped stdio |
| submit_proposal | marketplace | write | destructiveHint=False / idempotentHint=True / openWorldHint=True / readOnlyHint=False | tenant bearer / scoped stdio |
| send_message | marketplace | write | destructiveHint=False / idempotentHint=True / openWorldHint=True / readOnlyHint=False | tenant bearer / scoped stdio |
| search_evidence | portfolio | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| get_case_study | portfolio | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| list_skills | portfolio | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| free_calendar_slots | workspace | read | destructiveHint=False / idempotentHint=True / openWorldHint=False / readOnlyHint=True | tenant bearer / scoped stdio |
| create_interview_hold | workspace | write | destructiveHint=False / idempotentHint=True / openWorldHint=True / readOnlyHint=False | tenant bearer / scoped stdio |
| create_email_draft | workspace | write | destructiveHint=False / idempotentHint=True / openWorldHint=True / readOnlyHint=False | tenant bearer / scoped stdio |

Schemas and descriptions: `tests/contract/tool_schemas.json`. Every write accepts an idempotency key and dry-run preview; non-preview effects require an exact content-bound approval capability. Audit rows redact PII and exclude capability tokens.

## Third-party trust

- [Official Upwork MCP](https://www.upwork.com/ai/mcp): operated by the marketplace; OAuth scopes and explicit draft-only mapping constrain authority. Account validation is pending.
- [Official GitHub MCP](https://github.com/github/github-mcp-server): operated by GitHub; used only for read-only repository files, with code treated as data.

Only per-role named tools are exposed to graph code. Client timeouts and retries are bounded. Missing endpoints produce saved retry/attention states.
