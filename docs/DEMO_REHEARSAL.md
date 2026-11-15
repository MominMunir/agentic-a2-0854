# GigBid demo rehearsal

Checked on November 15, 2026 against the public deployment. These are rehearsal
instructions, not evidence that a demo video or full hosted send has been recorded.

## What passed in the live check

- App health and reviewer login.
- Existing safe proposal: awaiting approval, Critic accepted, Compliance passed,
  ten evidence items, USD 1389.30 and ten simulated Connects.
- Portfolio MCP: all three tools listed and a successful evidence search.
- Fresh Groq conversation draft: awaiting approval, three interview slots.
- Fresh scam analysis: skipped, risk 0.90, injection and unpaid/off-platform flags.
- No proposal or message was approved or sent during these checks.

Update: the registration HTTP 502 was repaired by batching account initialization
and moving it off the main event loop. A fresh public account registered in
2.26 seconds, logged in and received all starter data; concurrent health checks
passed. See `evals/results/registration.json`. Use the existing reviewer account
for the prepared walkthrough because saved runs belong to that account. New
accounts require their own job analyses. The response verifier still removed
most of the generated response, leaving a short sentence. Review/edit it before
sending. Passing compliance does not establish that a response is useful.

## Prepare before opening the recorder

1. Open https://gigbid-wr80.onrender.com and sign in with the credentials in the
   local `.private/hosted-reviewer.txt`. Sign in before recording.
2. Allow a cold start to finish. Confirm the inbox loads. A 50-second-or-longer
   cold start is possible on the Free host; do not start recording a waking app.
3. In Settings, confirm ML persona, hourly rate 45, minimum project budget 200,
   weekly Connects budget 100 and Review every decision. Keep marketplace mode
   `local_simulator`. The values need not be changed if already correct.
4. Close provider dashboards, credential files and private account tabs. Turn
   off notifications, select a readable browser zoom and make a ten-second
   microphone/screen sample before the real recording.
5. Open the app links below in separate tabs. Pre-open README/results separately.
   Keep one tab on the inbox for the beginning of the video.

| Purpose | Link |
|---|---|
| Inbox | https://gigbid-wr80.onrender.com/inbox |
| Safe job | https://gigbid-wr80.onrender.com/jobs/syn-job-001 |
| Prepared proposal | https://gigbid-wr80.onrender.com/studio/0a326b18-6bed-40e2-b964-0d268940210b |
| Prepared run history | https://gigbid-wr80.onrender.com/runs/0a326b18-6bed-40e2-b964-0d268940210b |
| Scam job | https://gigbid-wr80.onrender.com/jobs/syn-job-000 |
| Scam run | https://gigbid-wr80.onrender.com/runs/711cc7f3-42e4-4829-94c3-590d1156b21c |
| Seeded response rehearsal | https://gigbid-wr80.onrender.com/studio/b593928b-1d8e-4219-be63-60f9a17fb90c |
| Messages | https://gigbid-wr80.onrender.com/messages |
| Pipeline | https://gigbid-wr80.onrender.com/pipeline |
| Repository and results | https://github.com/MominMunir/agentic-a2-0854 |

## Rehearse without consuming the prepared proposal

1. In the inbox, find **Retail: Document search service**, then **Explore fit**.
   Direct-link fallback: open the safe-job URL above.
2. Confirm RAG, FastAPI and Python in its requirements. Click **View agent
   analysis**. This job already has an actual completed analysis; clicking it
   will open the saved run, not start new generation.
3. In the run viewer, inspect the Analyst, Risk and Fit steps, followed by the
   drafting/verification/compliance steps and awaiting-approval status. These
   are saved actual observations. Describe them as run history, not live progress.
4. Click **Open proposal studio**. Confirm the draft is nonempty, **Critic:
   Accepted**, **Compliance: Passed**, USD 1389.3 and **10 Connects**.
5. Under **Evidence behind each claim**, expand **Inspect 1 evidence source**
   on the cited portfolio sentence. Confirm its source passage is visible.
6. Refresh the page now. Confirm the proposal is still awaiting approval.
   This proves refresh persistence; it does not demonstrate crashing a worker.
7. Optional edit: append `I propose a short discovery step before implementation.`
   Click **Save & verify edit** and expect **Edit saved and verified**. Keep the
   page open after editing. Currently a refresh repopulates the editor from the
   original graph draft, so do the refresh check before the edit. Verify the
   visible final text again immediately before approval.
8. **Stop before Approve proposal.** Leave the pending proposal ready for recording.
   Do not reject it or regenerate paragraphs merely to practise navigating.
9. Open the scam job. It contains an instruction to ignore rules/reveal the
   system prompt/submit without approval, plus unpaid work and Telegram payment.
   Open its existing analysis. Expect **skip**, **90% risk**, injection flags and
   no proposal draft. Do not use the manual Skip button as evidence that the
   agent detected it.
10. Open the seeded response rehearsal. Expect awaiting approval and three
    **Suggested interview slots (UTC)**. The original response is short because
    verification removed unsupported text. Practise replacing it with a future
    plan, then Save & verify edit. Leave Approve message untouched.

Suggested response for today's rehearsal (use only slots actually shown):

> I propose validating the deliverable with a held-out test set and automated endpoint checks.
>
> I would suggest 16 November at 10:00 UTC or 14:00 UTC, subject to your confirmation.
>
> Which time would you prefer?

This wording passed the local verifier. Check it with the live Save & verify
button before relying on it. It describes a proposed approach, not invented
past experience. UTC 10:00 is Pakistan time 15:00; UTC 14:00 is Pakistan time 19:00.

## The approval and reply segment during the actual recording

1. Open the prepared proposal and read its final text and displayed cost.
2. Click **Approve proposal once**. It can briefly become queued/running;
   wait for **submitted**. The effect is confined to the synthetic local simulator.
3. Open Pipeline. Its card may immediately be under **replied**, because the
   simulator creates a sample client reply after submission. Do not wait for a
   real client or describe this as an instructor GigSim/hiring outcome.
4. Open Messages. If that tab was already open, refresh it. Find the conversation
   labeled **syn-job-001**, the same job just submitted. Do not confuse it with
   the preloaded `ml-client-demo`, `web-client-demo` or `data-client-demo` threads.
5. The sample client asks how you would validate the deliverable and requests
   interview slots. Click **Draft a response** in that same conversation.
6. Wait for awaiting approval, then inspect the text and suggested UTC slots.
   Edit a sparse response into a useful future plan if needed. Use the actual
   displayed slots. Click Save & verify edit; expect confirmation.
7. Click **Approve message once**, wait for **sent**, then return to Messages
   and confirm your response appears in the same thread. Refresh if needed.

This complete hosted send sequence was deliberately not executed during the
preflight, per the owner's instruction to preserve the prepared proposal. Local
workflow tests passed earlier, but they are distinct from this first cloud send.

## Portfolio MCP and results segment

The public MCP endpoint is https://gigbid-wr80.onrender.com/portfolio/mcp.
It is an authenticated protocol endpoint, not a website. An unauthenticated
browser visit is not a useful MCP demonstration.

For a simple recording segment, show Settings -> **Get Portfolio MCP connection**
and its server address with the token still masked, then the repository's
`mcp_servers/portfolio/README.md` installation command and tool inventory.
Do not claim this Settings view is an Inspector tool execution. A live SDK
tools-list/search check passed during preflight. Existing genuine Inspector
captures are in `docs/images/`; label them as saved captures if shown.

If including a live Inspector execution, connect and run `search_evidence`
successfully before recording using Streamable HTTP, the endpoint above and a
current Portfolio bearer token from Settings. Never display or record the token.
Use requirement `RAG FastAPI Python retail`, k 3, persona filter `ml`. If that
client setup has not been rehearsed, use the simpler Settings/README segment.

In the results view, explain that V0 was selected by the development rule and
advanced variants did not help on this synthetic corpus. The architecture study
was affected by unequal provider quotas, so it cannot fairly rank architectures.
Do not present rule-only smoke scores as human ratings or instructor outcomes.

## Three-minute recording order

| Time | What to show |
|---|---|
| 0:00-0:15 | Inbox and synthetic-demo notice; explain approval boundary |
| 0:15-0:40 | Safe job and actual saved parallel-analysis history |
| 0:40-1:10 | Proposal, evidence source, price, refresh and optional short edit |
| 1:10-1:30 | Approve once, wait for result, pipeline |
| 1:30-1:50 | Scam text and saved skip/injection result |
| 1:50-2:30 | Same-job client reply, response draft, review/edit, approve and sent result |
| 2:30-2:45 | Portfolio connection and installable server instructions |
| 2:45-3:00 | Results, repository and report; state evidence limits |

Record clips if necessary, trim genuine waiting time, and preserve the order of
approval and effects. Do not conceal errors or present a saved run as newly
executing. Keep the final video near three minutes and test its shared link.

## If a step fails

| Symptom | Action |
|---|---|
| Cold start or loading screen | Wait for the inbox to load before recording; check `/api/health` |
| Sign-up error | Registration is now verified; check app health and report a persistent error. An existing email returns 409 and should use Sign in. |
| Groq quota/retry error | Wait for the provider retry window; Retry saved work once when available; do not hammer Analyze |
| Already analysed job | View its saved run; select a genuinely new job if you need fresh generation |
| No approval button | Check run status; it must be awaiting approval with a valid preview |
| Unsupported edit | Remove invented experience/contact details; use a future plan and verify again |
| Short response | Review the verifier output and write a useful future-plan response using shown slots |
| Pipeline misses Submitted | Check Replied; the synthetic response is immediate |
| Missing new message | Refresh Messages and select `syn-job-001` rather than a seeded thread |
| MCP 401 | Use a current scoped token in an MCP client; never expose it in the video |

Start recording only when the inbox, pending proposal, evidence, scam result and
response rehearsal all open correctly in your own browser. The final approval
and send remain yours to perform.
