import { useCallback, useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCheck,
  ChevronRight,
  CircleHelp,
  Files,
  Inbox,
  Layers3,
  LogOut,
  MessageSquare,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Activity,
  BarChart3,
  Upload,
  Menu,
  X,
} from "lucide-react";
import { api, post, generatedAuth } from "../lib/api/client";
import EvidenceHover from "../components/EvidenceHover";
import ApprovalPanel from "../components/ApprovalPanel";
import RunTimeline from "../components/RunTimeline";

const errorText = (e: any) => e.message || "Something went wrong. Try again.";
const money = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n || 0);
function Status({ value }: { value: string }) {
  return (
    <span
      className={
        "badge " +
        (/skip|reject|attention/.test(value)
          ? "amber"
          : /approv|bid|submit|sent/.test(value)
            ? "green"
            : "")
      }
    >
      {value?.replaceAll("_", " ") || "new"}
    </span>
  );
}
function Notice({ error, dismiss }: { error: string; dismiss?: () => void }) {
  return error ? (
    <div role="alert" className="error">
      <ShieldCheck size={20} />
      <span>
        {error.toLowerCase().includes("unavailable")
          ? "Marketplace unavailable. Your saved work is safe. "
          : ""}
        {error}
      </span>
      {dismiss && (
        <button aria-label="Dismiss error" onClick={dismiss}>
          <X size={18} />
        </button>
      )}
    </div>
  ) : null;
}
function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="empty">
      <Files size={30} />
      <p>{children}</p>
    </div>
  );
}
function PageTitle({ eyebrow, title, detail, children }: any) {
  return (
    <header className="page-title">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        {detail && <p>{detail}</p>}
      </div>
      {children}
    </header>
  );
}

export default function App() {
  const [user, setUser] = useState<any>(null),
    [ready, setReady] = useState(false),
    [mobile, setMobile] = useState(false);
  useEffect(() => {
    api("/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);
  if (!ready)
    return (
      <main className="initial" role="status">
        Opening your workspace…
      </main>
    );
  if (!user) return <SignIn onSuccess={setUser} />;
  const nav = [
    ["/inbox", Inbox, "Job inbox"],
    ["/pipeline", Layers3, "Pipeline"],
    ["/messages", MessageSquare, "Messages"],
    ["/runs", Activity, "Agent runs"],
    ["/analytics", BarChart3, "Analytics"],
    ["/settings", Settings2, "Settings"],
  ] as const;
  return (
    <div className="shell">
      <button
        className="mobile-menu"
        aria-label="Open navigation"
        onClick={() => setMobile(!mobile)}
      >
        <Menu />
      </button>
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <Link className="brand" to="/inbox">
          <span className="brand-icon">
            <BriefcaseBusiness size={23} />
          </span>
          gigbid<span className="brand-dot">.</span>
        </Link>
        <div className="workspace-tag">YOUR FREELANCE WORKSPACE</div>
        <nav>
          {nav.map(([path, Icon, label]) => (
            <NavLink key={path} to={path} onClick={() => setMobile(false)}>
              <Icon size={19} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">
          <ShieldCheck size={21} />
          <strong>You have the final say.</strong>
          <p>Every proposal and message waits for your approval.</p>
        </div>
        <div className="user-card">
          <span className="avatar">{user.email[0].toUpperCase()}</span>
          <div>
            <strong>My workspace</strong>
            <small>{user.email}</small>
          </div>
          <button
            aria-label="Sign out"
            onClick={async () => {
              await post("/auth/logout");
              setUser(null);
            }}
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <div className="topbar">
          <span>
            Workspace <ChevronRight size={14} /> <strong>GigBid Copilot</strong>
          </span>
          <span className="top-status">
            <span /> Human approval enabled
          </span>
        </div>
        <main>
          <Routes>
            <Route path="/inbox" element={<JobInbox />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/studio/:id" element={<RunPage studio />} />
            <Route path="/runs/:id" element={<RunPage />} />
            <Route path="/runs" element={<Runs />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/messages" element={<Messages />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route
              path="/settings"
              element={<Settings user={user} onUpdate={setUser} />}
            />
            <Route
              path="/onboarding"
              element={<Settings user={user} onUpdate={setUser} onboarding />}
            />
            <Route path="*" element={<Navigate to="/inbox" />} />
          </Routes>
        </main>
        <footer>
          Built around evidence. Guided by you.
          <span>GigBid · local simulation data is labeled</span>
        </footer>
      </div>
    </div>
  );
}

function SignIn({ onSuccess }: { onSuccess: (user: any) => void }) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [create, setCreate] = useState(false),
    [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  return (
    <main className="auth">
      <div className="auth-story">
        <div className="brand">gigbid.</div>
        <span className="eyebrow">LESS SCROLLING. MORE GOOD WORK.</span>
        <h1>
          Your next opportunity.
          <br />
          <em>Backed by proof.</em>
        </h1>
        <p>
          A thoughtful copilot for finding freelance work, showing your fit, and
          writing proposals that earn a second look.
        </p>
        <div className="auth-proof">
          <ShieldCheck />
          <span>
            Real evidence. Clear decisions.
            <br />
            You approve every action.
          </span>
        </div>
      </div>
      <form
        className="auth-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            const user = await generatedAuth[create ? "register" : "login"]({
              email,
              password,
            });
            onSuccess(user);
            window.location.assign(create ? "/onboarding" : "/inbox");
          } catch (e) {
            setError(errorText(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        <span className="eyebrow">WELCOME TO YOUR WORKSPACE</span>
        <h2>{create ? "Make room for better work." : "Good to see you."}</h2>
        <p>
          {create
            ? "Create your account and choose a portfolio."
            : "Sign in to pick up where you left off."}
        </p>
        <Notice error={error} />
        <label>
          Email address
          <input
            type="email"
            autoComplete="email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete={create ? "new-password" : "current-password"}
            minLength={12}
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="primary" disabled={busy}>
          {busy ? "Opening workspace…" : create ? "Create account" : "Sign in"}
          <ArrowUpRight size={17} />
        </button>
        <button
          type="button"
          className="text-button"
          onClick={() => setCreate(!create)}
        >
          {create
            ? "Already have an account? Sign in"
            : "New here? Create an account"}
        </button>
      </form>
    </main>
  );
}

function JobInbox() {
  const [jobs, setJobs] = useState<any[]>([]),
    [query, setQuery] = useState(""),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [filter, setFilter] = useState("all");
  const load = useCallback(() => {
    setLoading(true);
    api("/jobs?query=" + encodeURIComponent(query))
      .then((d) => {
        setJobs(d.jobs);
        setError("");
      })
      .catch((e) => setError(errorText(e)))
      .finally(() => setLoading(false));
  }, [query]);
  useEffect(() => {
    load();
  }, []);
  const visible = jobs.filter(
    (j) =>
      filter === "all" ||
      (filter === "fit" ? j.preliminary_fit >= 0.6 : j.run_status === "new"),
  );
  return (
    <>
      <PageTitle
        eyebrow="YOUR NEXT CHAPTER"
        title="Find work worth your time."
        detail="A focused inbox of opportunities. Your portfolio brings the proof."
      >
        <button className="primary" onClick={load}>
          <Sparkles size={17} />
          Refresh opportunities
        </button>
      </PageTitle>
      <div className="stats">
        <div>
          <span>Opportunities</span>
          <strong>
            {jobs.length}
            <small>in your inbox</small>
          </strong>
        </div>
        <div>
          <span>Strong preliminary fit</span>
          <strong>
            {jobs.filter((j) => j.preliminary_fit >= 0.6).length}
            <small>ready to explore</small>
          </strong>
        </div>
        <div>
          <span>In progress</span>
          <strong>
            {jobs.filter((j) => j.run_id).length}
            <small>agent analyses</small>
          </strong>
        </div>
      </div>
      <section className="opportunity-banner">
        <div className="banner-icon">
          <Sparkles size={25} />
        </div>
        <div>
          <strong>Specific experience is your advantage.</strong>
          <p>
            Open an opportunity to connect each requirement to evidence from
            your portfolio.
          </p>
        </div>
        <span className="pill">EVIDENCE FIRST</span>
      </section>
      <Notice error={error} dismiss={() => setError("")} />
      <div className="inbox-toolbar">
        <div className="tabs">
          {[
            ["all", "All opportunities"],
            ["fit", "Strong fit"],
            ["new", "New"],
          ].map(([id, title]) => (
            <button
              className={filter === id ? "active" : ""}
              onClick={() => setFilter(id)}
              key={id}
            >
              {title}
            </button>
          ))}
        </div>
        <form
          className="search"
          onSubmit={(e) => {
            e.preventDefault();
            load();
          }}
        >
          <Search size={17} />
          <input
            aria-label="Search jobs"
            placeholder="Search opportunities…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>
      </div>
      <div className="section-heading">
        <h2>
          Opportunity inbox <span>{visible.length}</span>
        </h2>
        <small>Ranked by preliminary skill overlap</small>
      </div>
      {loading ? (
        <p role="status">Loading opportunities…</p>
      ) : visible.length ? (
        <div className="job-grid">
          {visible.map((job) => (
            <article className="job-card" key={job.id}>
              <div className="job-card-top">
                <span className="category">
                  {job.category === "ml"
                    ? "AI & MACHINE LEARNING"
                    : job.category === "web"
                      ? "WEB DEVELOPMENT"
                      : job.category === "data"
                        ? "DATA & ANALYTICS"
                        : "FREELANCE OPPORTUNITY"}
                </span>
                <Status value={job.synthetic ? "synthetic" : "real Kaggle"} />
              </div>
              <Link to={"/jobs/" + job.id}>
                <h3>{job.title}</h3>
              </Link>
              <p className="job-excerpt">{job.description}</p>
              <div className="skills">
                {job.required_skills.slice(0, 4).map((s: string) => (
                  <span key={s}>{s}</span>
                ))}
              </div>
              <div className="job-numbers">
                <div>
                  <small>Project budget</small>
                  <strong>{money(job.budget_max)}</strong>
                </div>
                <div>
                  <small>
                    Connects{job.connects_estimated ? " (estimate)" : ""}
                  </small>
                  <strong>{job.connects_cost}</strong>
                </div>
                <div>
                  <small>Skill overlap</small>
                  <strong className="fit">
                    {Math.round(job.preliminary_fit * 100)}%
                  </strong>
                </div>
              </div>
              <div className="job-card-bottom">
                <Status value={job.run_status} />
                <Link to={"/jobs/" + job.id}>
                  Explore fit <ArrowUpRight size={16} />
                </Link>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty>No opportunities match this filter. Try another search.</Empty>
      )}
    </>
  );
}

function JobDetail() {
  const { id } = useParams(),
    navigate = useNavigate();
  const [data, setData] = useState<any>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [team, setTeam] = useState<any>(null);
  useEffect(() => {
    api("/jobs/" + id)
      .then(setData)
      .catch((e) => setError(errorText(e)));
  }, [id]);
  const state = data?.analysis;
  return (
    <>
      <Link className="back" to="/inbox">
        ← Opportunity inbox
      </Link>
      <Notice error={error} />
      {data && (
        <>
          <PageTitle
            eyebrow={
              data.job.synthetic
                ? "SYNTHETIC OPPORTUNITY"
                : "REAL KAGGLE RECORD"
            }
            title={data.job.title}
            detail={`${money(data.job.budget_min)}–${money(data.job.budget_max)} · ${data.job.connects_cost} Connects`}
          >
            <button
              className="primary"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  const run = await post("/jobs/" + id + "/analyze");
                  navigate("/runs/" + run.id);
                } catch (e) {
                  setError(errorText(e));
                  setBusy(false);
                }
              }}
            >
              {data.run_id ? "View agent analysis" : "Analyze this opportunity"}
              <Sparkles size={17} />
            </button>
          </PageTitle>
          <div className="detail-grid">
            <section className="panel">
              <h2>The brief</h2>
              <p className="preserve">{data.job.description}</p>
              <div className="skills">
                {data.job.required_skills.map((s: string) => (
                  <span key={s}>{s}</span>
                ))}
              </div>
              <button
                onClick={async () => {
                  await post("/jobs/" + id + "/skip");
                  navigate("/inbox");
                }}
              >
                Skip opportunity
              </button>
            </section>
            <section className="panel">
              <h2>Fit & risk assessment</h2>
              <button
                onClick={async () => {
                  try {
                    setTeam(await api(`/jobs/${id}/agency`));
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              >
                Compare team fit
              </button>
              {team && (
                <div>
                  <h3>
                    Agency recommendation:{" "}
                    {team.selected || "No supported match"}
                  </h3>
                  {team.candidates.map((c: any) => (
                    <div className="matrix-row" key={c.persona}>
                      <strong>{c.persona.toUpperCase()}</strong>
                      <span>{Math.round(c.score * 100)}% evidenced fit</span>
                    </div>
                  ))}
                  {team.selected && !data.run_id && (
                    <button
                      className="primary"
                      onClick={async () => {
                        const r = await post(`/jobs/${id}/analyze?agency=true`);
                        navigate(`/runs/${r.id}`);
                      }}
                    >
                      Analyze with recommended member
                    </button>
                  )}
                </div>
              )}
              {state?.fit ? (
                <>
                  <Status value={state.decision?.action} />
                  <p>{state.decision?.reasons?.join(". ")}</p>
                  <p>
                    Fit: {Math.round(state.fit.score * 100)}% · Risk:{" "}
                    {Math.round(state.risk.score * 100)}%
                  </p>
                  <p>{state.risk.explanation}</p>
                  {state.fit.matrix.map((r: any) => (
                    <div className="matrix-row" key={r.requirement}>
                      <strong>{r.requirement}</strong>
                      <div>
                        {r.evidence_ids.length ? (
                          <details>
                            <summary>
                              {r.evidence_ids.length} supporting items
                            </summary>
                            {r.evidence_ids.map((eid: string) => {
                              const source = state.evidence.find(
                                (e: any) => e.id === eid,
                              );
                              return source ? (
                                <div className="claim" key={eid}>
                                  <strong>{source.title}</strong>
                                  <p>{source.text}</p>
                                  <small>{source.source}</small>
                                </div>
                              ) : null;
                            })}
                          </details>
                        ) : (
                          "No portfolio support"
                        )}
                      </div>
                    </div>
                  ))}
                  <p>{state.price?.rationale}</p>
                  <Link className="button" to={"/studio/" + data.run_id}>
                    Open proposal studio
                  </Link>
                </>
              ) : (
                <Empty>
                  Run an analysis to see verified fit, client risks, evidence
                  and a price recommendation.
                </Empty>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}

function RunPage({ studio = false }: { studio?: boolean }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState<any>(null),
    [events, setEvents] = useState<any[]>([]),
    [text, setText] = useState(""),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false),
    [checkpoints, setCheckpoints] = useState<any[]>([]),
    [checkpoint, setCheckpoint] = useState(""),
    [replayStage, setReplayStage] = useState("writer");
  const load = useCallback(async () => {
    try {
      const d = await api("/runs/" + id);
      setRun(d);
      setText((t) => t || d.state.draft?.cover_letter || "");
    } catch (e) {
      setError(errorText(e));
    }
  }, [id]);
  useEffect(() => {
    setText("");
    load();
    const timer = setInterval(load, 2000);
    const stream = new EventSource(`/api/runs/${id}/events`, {
      withCredentials: true,
    });
    api(`/runs/${id}/trace`)
      .then(setEvents)
      .catch(() => {});
    stream.onmessage = (event) => {
      const value = JSON.parse(event.data);
      setEvents((old) =>
        old.some((e) => e.id === value.id) ? old : [...old, value],
      );
      load();
    };
    return () => {
      clearInterval(timer);
      stream.close();
    };
  }, [id]);
  const state = run?.state;
  return (
    <>
      <PageTitle
        eyebrow={studio ? "WRITE WITH PROOF" : "A CLEAR VIEW OF EVERY STEP"}
        title={studio ? "Proposal studio" : "Your agents at work."}
        detail={state?.job?.title || "Client conversation"}
      >
        {run && <Status value={run.status} />}
      </PageTitle>
      <Notice error={error} dismiss={() => setError("")} />
      {run && (
        <>
          <div className="actions">
            <Link className="button" to={(studio ? "/runs/" : "/studio/") + id}>
              {studio ? "View agent run" : "Open proposal studio"}
            </Link>
            {/queued|running/.test(run.status) && (
              <span role="status">
                Progress appears below as each agent finishes.
              </span>
            )}
            {/attention|retry_queued/.test(run.status) && (
              <button
                onClick={async () => {
                  await post(`/runs/${id}/retry`);
                  await load();
                }}
              >
                Retry saved work
              </button>
            )}
          </div>
          {run.error && <Notice error={run.error} />}
          <div className="detail-grid">
            <section className="panel">
              <div className="section-heading">
                <h2>{studio ? "Your proposal" : "Live workflow"}</h2>
                <span className="badge">{state?.steps || 0} steps</span>
              </div>
              {studio && state?.draft ? (
                <>
                  <label>
                    Draft editor
                    <textarea
                      aria-label="Draft editor"
                      rows={15}
                      value={text}
                      onChange={(e) => {
                        setText(e.target.value);
                        setSaved(false);
                      }}
                      disabled={run.status !== "awaiting_approval"}
                    />
                  </label>
                  <div className="actions">
                    <button
                      disabled={run.status !== "awaiting_approval"}
                      onClick={async () => {
                        try {
                          await api(`/runs/${id}/draft`, {
                            method: "PATCH",
                            body: JSON.stringify({ text }),
                          });
                          setSaved(true);
                        } catch (e) {
                          setError(errorText(e));
                        }
                      }}
                    >
                      Save & verify edit
                    </button>
                    {saved && (
                      <span role="status">Edit saved and verified</span>
                    )}
                  </div>
                  <h3>Screening answers</h3>
                  {state.draft.screening_answers?.map(
                    (a: string, i: number) => (
                      <p key={i}>{a}</p>
                    ),
                  )}
                  <h3>Evidence behind each claim</h3>
                  {state.verification?.claims
                    .filter((c: any) => c.status === "supported")
                    .map((c: any, i: number) => (
                      <EvidenceHover
                        key={i}
                        claim={c}
                        evidence={state.evidence || []}
                      />
                    ))}
                  {run.status === "awaiting_approval" && (
                    <div className="actions">
                      <label>
                        Paragraph to regenerate
                        <select id="paragraph-index">
                          {text.split("\n\n").map((_: string, i: number) => (
                            <option value={i} key={i}>
                              Paragraph {i + 1}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button
                        onClick={async () => {
                          try {
                            await post(`/runs/${id}/regenerate`, {
                              paragraph_index: Number(
                                (
                                  document.getElementById(
                                    "paragraph-index",
                                  ) as HTMLSelectElement
                                ).value,
                              ),
                            });
                            setText("");
                            load();
                          } catch (e) {
                            setError(errorText(e));
                          }
                        }}
                      >
                        Regenerate paragraph
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <RunTimeline events={events} />
              )}
            </section>
            <div>
              <section className="panel">
                <h2>Decision notes</h2>
                <p>
                  {state?.decision?.reasons?.join(". ") ||
                    state?.intent ||
                    "Analysis in progress"}
                </p>
                {state?.risk && (
                  <p>
                    Risk: {Math.round(state.risk.score * 100)}% ·{" "}
                    {state.risk.flags.join(", ") || "No known rule flags"}
                  </p>
                )}
                <p>{state?.price?.rationale}</p>
                {state?.critique && (
                  <p>
                    Critic:{" "}
                    {state.critique.accepted
                      ? "Accepted"
                      : state.critique.reasons.join(". ")}
                  </p>
                )}
                {state?.compliance && (
                  <p>
                    Compliance:{" "}
                    {state.compliance.allowed
                      ? "Passed"
                      : state.compliance.violations.join(". ")}
                  </p>
                )}
                {state?.slots?.length > 0 && (
                  <>
                    <h3>Suggested interview slots (UTC)</h3>
                    {state.slots.map((s: any) => (
                      <div key={s.start}>
                        <p>
                          {s.start} → {s.end}
                        </p>
                        <button
                          onClick={async () => {
                            try {
                              const hold = await post("/workspace/hold", {
                                start: s.start,
                                end: s.end,
                                title: "Tentative client interview",
                                confirmed: true,
                              });
                              setSaved(hold.status === "created");
                            } catch (e) {
                              setError(errorText(e));
                            }
                          }}
                        >
                          Approve tentative local hold
                        </button>
                      </div>
                    ))}
                  </>
                )}
              </section>
              {run.status === "awaiting_approval" && (
                <ApprovalPanel
                  run={run}
                  text={text || state.draft.cover_letter}
                  onDone={load}
                  onError={setError}
                />
              )}
              <section className="panel">
                <h3>Run receipt</h3>
                {run.kind === "bid" && (
                  <details>
                    <summary>Replay from a saved step</summary>
                    <p className="muted">
                      A replay creates a new draft and requires a new approval.
                    </p>
                    <button
                      onClick={async () => {
                        try {
                          const list = await api(`/runs/${id}/history`);
                          setCheckpoints(list);
                          setCheckpoint(list[0]?.checkpoint_id || "");
                        } catch (e) {
                          setError(errorText(e));
                        }
                      }}
                    >
                      Load checkpoints
                    </button>
                    {checkpoints.length > 0 && (
                      <>
                        <label>
                          Saved checkpoint
                          <select
                            value={checkpoint}
                            onChange={(e) => setCheckpoint(e.target.value)}
                          >
                            {checkpoints.map((c) => (
                              <option
                                key={c.checkpoint_id}
                                value={c.checkpoint_id}
                              >
                                {c.created_at} ·{" "}
                                {c.next.join(", ") || "completed"}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Restart at
                          <select
                            value={replayStage}
                            onChange={(e) => setReplayStage(e.target.value)}
                          >
                            {[
                              "analysis",
                              "pricing",
                              "writer",
                              "verifier",
                              "critic",
                              "compliance_guard",
                            ].map((stage) => (
                              <option value={stage} key={stage}>
                                {stage.replaceAll("_", " ")}
                              </option>
                            ))}
                          </select>
                        </label>
                        <button
                          onClick={async () => {
                            try {
                              const next = await post(`/runs/${id}/replay`, {
                                checkpoint_id: checkpoint,
                                stage: replayStage,
                              });
                              navigate("/runs/" + next.id);
                            } catch (e) {
                              setError(errorText(e));
                            }
                          }}
                        >
                          Replay for review
                        </button>
                      </>
                    )}
                  </details>
                )}
                <small className="mono">{id}</small>
                <p>
                  {state?.usage?.reduce(
                    (sum: number, u: any) =>
                      sum + u.input_tokens + u.output_tokens,
                    0,
                  ) || 0}{" "}
                  tokens ·{" "}
                  {money(
                    state?.usage?.reduce(
                      (sum: number, u: any) => sum + u.usd_estimate,
                      0,
                    ),
                  )}{" "}
                  estimated inference cost
                </p>
                <a
                  href={`/api/runs/${id}/trace`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open full trace <ArrowUpRight size={14} />
                </a>
              </section>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function Runs() {
  const [runs, setRuns] = useState<any[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    api("/runs")
      .then(setRuns)
      .catch((e) => setError(errorText(e)));
  }, []);
  return (
    <>
      <PageTitle
        eyebrow="VISIBLE BY DESIGN"
        title="Every decision has a trail."
        detail="Open a run to inspect agent progress, evidence, usage and approval history."
      />
      <Notice error={error} />
      <div className="panel">
        {runs.length ? (
          runs.map((run) => (
            <Link className="list-row" to={"/runs/" + run.id} key={run.id}>
              <div>
                <strong>{run.state.job?.title || "Client conversation"}</strong>
                <small>{run.created}</small>
              </div>
              <Status value={run.status} />
              <ArrowUpRight size={17} />
            </Link>
          ))
        ) : (
          <Empty>Analyze an opportunity to start your first run.</Empty>
        )}
      </div>
    </>
  );
}

function Pipeline() {
  const [data, setData] = useState<any>({ runs: [], proposals: [] }),
    [error, setError] = useState("");
  useEffect(() => {
    api("/pipeline")
      .then(setData)
      .catch((e) => setError(errorText(e)));
  }, []);
  const columns = [
    "drafted",
    "submitted",
    "viewed",
    "replied",
    "interview",
    "hired",
    "lost",
  ];
  return (
    <>
      <PageTitle
        eyebrow="THE BIGGER PICTURE"
        title="From first draft to good work."
        detail="Track your proposals and record confirmed outcomes to improve future decisions."
      />
      <Notice error={error} />
      <div className="kanban">
        {columns.map((column) => (
          <section key={column}>
            <h3>
              {column}
              <span>
                {
                  data.runs.filter(
                    (r: any) =>
                      (r.state.outcome?.local_outcome ||
                        (r.status === "awaiting_approval"
                          ? "drafted"
                          : r.status)) === column,
                  ).length
                }
              </span>
            </h3>
            {data.runs
              .filter(
                (r: any) =>
                  (r.state.outcome?.local_outcome ||
                    (r.status === "awaiting_approval"
                      ? "drafted"
                      : r.status)) === column,
              )
              .map((r: any) => (
                <Link
                  className="pipeline-card"
                  to={"/studio/" + r.id}
                  key={r.id}
                >
                  <span className="category">{r.state.job?.category}</span>
                  <strong>{r.state.job?.title}</strong>
                  <span>{money(r.state.price?.amount)}</span>
                </Link>
              ))}
          </section>
        ))}
      </div>
      <section className="panel">
        <h3>Record a confirmed outcome</h3>
        <form
          className="actions"
          onSubmit={async (e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            try {
              const run = data.runs.find((r: any) => r.id === f.get("run"));
              await post("/jobs/" + run.job_id + "/outcome", {
                category: run.state.job.category,
                outcome: f.get("outcome"),
              });
              setError("");
            } catch (e) {
              setError(errorText(e));
            }
          }}
        >
          <select name="run" aria-label="Proposal outcome job" required>
            <option value="">Select a job</option>
            {data.runs.map((r: any) => (
              <option key={r.id} value={r.id}>
                {r.state.job?.title || r.job_id}
              </option>
            ))}
          </select>
          <select name="outcome" aria-label="Confirmed outcome">
            {["replied", "hired", "ignored", "lost"].map((o) => (
              <option key={o}>{o}</option>
            ))}
          </select>
          <button>Save outcome</button>
        </form>
        <p className="muted">
          Local simulated replies are labeled and are not instructor GigSim
          results.
        </p>
      </section>
    </>
  );
}

function Messages() {
  const [messages, setMessages] = useState<any[]>([]),
    [error, setError] = useState(""),
    navigate = useNavigate();
  useEffect(() => {
    api("/messages")
      .then((d) => setMessages(d.messages))
      .catch((e) => setError(errorText(e)));
  }, []);
  const conversations = [...new Set(messages.map((m) => m.conversation_id))];
  return (
    <>
      <PageTitle
        eyebrow="KEEP THE CONVERSATION MOVING"
        title="Thoughtful replies. Your approval."
        detail="Your liaison can suggest a response and interview slots. You decide what leaves."
      />
      <Notice error={error} />
      {conversations.length ? (
        conversations.map((cid) => (
          <section className="panel" key={cid}>
            <span className="eyebrow">{cid}</span>
            {messages
              .filter((m) => m.conversation_id === cid)
              .map((m) => (
                <div className={"message " + m.role} key={m.id}>
                  <strong>
                    {m.role || "you"}{" "}
                    {m.synthetic && <span className="badge">synthetic</span>}
                  </strong>
                  <p>{m.text}</p>
                </div>
              ))}
            <button
              className="primary"
              onClick={async () => {
                try {
                  const r = await post("/messages/" + cid + "/draft");
                  navigate("/studio/" + r.id);
                } catch (e) {
                  setError(errorText(e));
                }
              }}
            >
              <Sparkles size={17} />
              Draft a response
            </button>
          </section>
        ))
      ) : (
        <Empty>No client messages yet.</Empty>
      )}
    </>
  );
}

function Analytics() {
  const [data, setData] = useState<any>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/analytics")
      .then(setData)
      .catch((e) => setError(errorText(e)));
  }, []);
  return (
    <>
      <PageTitle
        eyebrow="LEARN FROM THE WORK"
        title="A clearer view of your progress."
        detail="Observed usage and confirmed outcomes, with room for the story behind the numbers."
      />
      <Notice error={error} />
      {data && (
        <>
          <div className="stats">
            <div>
              <span>Connects spent</span>
              <strong>
                {data.wallet.weekly_spent}
                <small>{data.wallet.balance} remaining</small>
              </strong>
            </div>
            <div>
              <span>Confirmed reply rate</span>
              <strong>
                {data.reply_rate === null
                  ? "-"
                  : Math.round(data.reply_rate * 100) + "%"}
                <small>{data.outcomes.length} recorded outcomes</small>
              </strong>
            </div>
            <div>
              <span>Confirmed hire rate</span>
              <strong>
                {data.hire_rate === null
                  ? "-"
                  : Math.round(data.hire_rate * 100) + "%"}
                <small>user-confirmed data</small>
              </strong>
            </div>
          </div>
          <div className="detail-grid">
            <section className="panel">
              <h2>Agent performance</h2>
              <div className="matrix-row">
                <span>Median run latency</span>
                <strong>{data.p50_seconds?.toFixed(2) ?? "-"} s</strong>
              </div>
              <div className="matrix-row">
                <span>95th percentile latency</span>
                <strong>{data.p95_seconds?.toFixed(2) ?? "-"} s</strong>
              </div>
              <div className="matrix-row">
                <span>Tokens measured</span>
                <strong>{data.tokens.toLocaleString()}</strong>
              </div>
              <div className="matrix-row">
                <span>Estimated inference cost</span>
                <strong>${data.usd_estimate.toFixed(5)}</strong>
              </div>
            </section>
            <section className="panel">
              <h2>Outcomes by category</h2>
              {["ml", "web", "data"].map((category) => {
                const count = data.outcomes.filter(
                  (o: any) => o.category === category,
                ).length;
                return (
                  <div className="chart-row" key={category}>
                    <span>{category.toUpperCase()}</span>
                    <div>
                      <i
                        style={{
                          width:
                            Math.max(
                              2,
                              (count / Math.max(data.outcomes.length, 1)) * 100,
                            ) + "%",
                        }}
                      />
                    </div>
                    <strong>{count}</strong>
                  </div>
                );
              })}
              <p className="muted">{data.source}</p>
            </section>
          </div>
        </>
      )}
    </>
  );
}

function Settings({ user, onUpdate, onboarding = false }: any) {
  const [profile, setProfile] = useState<any>(user.profile),
    [data, setData] = useState<any>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [portfolio, setPortfolio] = useState<any[]>([]),
    [evidenceFilter, setEvidenceFilter] = useState(""),
    [mcpConnection, setMcpConnection] = useState<any>(null);
  const load = () =>
    Promise.all([api("/settings"), api("/portfolio")])
      .then(([settings, items]) => {
        setData(settings);
        setPortfolio(items.items);
      })
      .catch((e) => setError(errorText(e)));
  useEffect(() => {
    load();
  }, []);
  const change = (key: string, value: any) =>
    setProfile((p: any) => ({ ...p, [key]: value }));
  return (
    <>
      <PageTitle
        eyebrow={onboarding ? "MAKE IT YOURS" : "YOUR WORK, YOUR RULES"}
        title={onboarding ? "Set up your workspace." : "Settings & memory"}
        detail="Choose your portfolio, set boundaries, and see what your copilot has learned."
      />
      <Notice error={error} />
      {message && (
        <div className="success" role="status">
          {message}
        </div>
      )}
      <div className="detail-grid">
        <section className="panel">
          <h2>Profile & preferences</h2>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                const updated = await api("/settings", {
                  method: "PATCH",
                  body: JSON.stringify(profile),
                });
                onUpdate(updated);
                setMessage("Workspace preferences saved.");
                load();
              } catch (e) {
                setError(errorText(e));
              }
            }}
          >
            <label>
              Portfolio persona
              <select
                aria-label="Portfolio persona"
                value={profile.persona}
                onChange={(e) => change("persona", e.target.value)}
              >
                <option value="ml">Alex · AI / ML Engineer (synthetic)</option>
                <option value="web">
                  Sam · Full-stack Developer (synthetic)
                </option>
                <option value="data">Jordan · Data Analyst (synthetic)</option>
                <option value="own">My own portfolio</option>
              </select>
            </label>
            {[
              ["hourly_rate", "Hourly rate (USD)"],
              ["minimum_project_budget", "Minimum project budget (USD)"],
              ["weekly_connects_budget", "Weekly Connects budget"],
            ].map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  type="number"
                  min={key === "weekly_connects_budget" ? 0 : 1}
                  value={profile[key]}
                  onChange={(e) => change(key, Number(e.target.value))}
                />
              </label>
            ))}
            <label>
              Saved search
              <input
                value={profile.saved_search}
                onChange={(e) => change("saved_search", e.target.value)}
              />
            </label>
            <label>
              Autonomy
              <select
                value={profile.autonomy}
                onChange={(e) => change("autonomy", e.target.value)}
              >
                <option value="review">Review every decision</option>
                <option value="auto_skip">
                  Allow low-fit skips · always approve sends
                </option>
              </select>
            </label>
            <button className="primary">Save preferences</button>
          </form>
        </section>
        <div>
          <section className="panel">
            <h2>Bring your own evidence</h2>
            <p>
              Upload a CV, case study, README or code file. Up to 5 MB; text is
              indexed incrementally.
            </p>
            <label className="upload">
              <Upload size={22} />
              Choose portfolio file
              <input
                aria-label="Upload portfolio"
                type="file"
                accept=".pdf,.md,.txt,.json,.py,.ts,.tsx,.js,.sql"
                onChange={async (e) => {
                  if (!e.target.files?.[0]) return;
                  const form = new FormData();
                  form.append("file", e.target.files[0]);
                  try {
                    const d = await api("/portfolio/upload", {
                      method: "POST",
                      body: form,
                    });
                    setMessage(`${d.chunks} portfolio chunks indexed.`);
                    load();
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              />
            </label>
            <details>
              <summary>Manage portfolio evidence ({portfolio.length})</summary>
              <p className="muted">
                Removing a source forces pending drafts to pass verification
                again.
              </p>
              <input
                aria-label="Find portfolio evidence"
                placeholder="Find evidence…"
                value={evidenceFilter}
                onChange={(e) => setEvidenceFilter(e.target.value)}
              />
              {portfolio
                .filter((item) =>
                  (item.title + " " + item.id)
                    .toLowerCase()
                    .includes(evidenceFilter.toLowerCase()),
                )
                .slice(0, 30)
                .map((item) => (
                  <div className="matrix-row" key={item.id}>
                    <div>
                      <strong>{item.title}</strong>
                      <small>
                        {item.type} · {item.provenance}
                      </small>
                    </div>
                    <button
                      onClick={async () => {
                        try {
                          await api("/portfolio/" + item.id, {
                            method: "DELETE",
                          });
                          setMessage(
                            "Evidence removed. Drafts will be checked against the current portfolio.",
                          );
                          load();
                        } catch (e) {
                          setError(errorText(e));
                        }
                      }}
                    >
                      Remove source
                    </button>
                  </div>
                ))}
            </details>
          </section>
          <section className="panel">
            <h2>Connected accounts</h2>
            <p>
              Marketplace: <strong>{data?.marketplace || "loading"}</strong>
            </p>
            <button
              onClick={async () => {
                try {
                  const d = await api("/accounts/upwork/connect");
                  window.location.assign(d.authorization_url);
                } catch (e) {
                  setError(errorText(e));
                }
              }}
            >
              Connect Upwork with OAuth <ArrowUpRight size={16} />
            </button>
            <p className="muted">
              Live actions create drafts for final confirmation on Upwork.
            </p>
            <button
              onClick={async () => {
                try {
                  setMcpConnection(await post("/portfolio/access-token"));
                } catch (e) {
                  setError(errorText(e));
                }
              }}
            >
              Get Portfolio MCP connection
            </button>
            {mcpConnection && (
              <div>
                <p>Server: {mcpConnection.server_url}</p>
                <label>
                  Private read-only token · expires in one hour
                  <input type="password" readOnly value={mcpConnection.token} />
                </label>
                <button
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(mcpConnection.token);
                      setMessage(
                        "Private Portfolio token copied. Share it only with your chosen MCP host.",
                      );
                    } catch (e) {
                      setError(errorText(e));
                    }
                  }}
                >
                  Copy private token
                </button>
              </div>
            )}
          </section>
          <section className="panel">
            <h2>What your copilot remembers</h2>
            <p>
              Style rules require repeated edits. Outcome patterns need three
              distinct confirmed jobs.
            </p>
            {["style", "outcome"].map((kind) => (
              <div key={kind}>
                <h3>
                  {kind === "style" ? "Writing style" : "Outcome patterns"}
                </h3>
                {data?.[kind + "_memory"]?.length ? (
                  data[kind + "_memory"].map((m: any) => (
                    <div className="matrix-row" key={m.key}>
                      <span>{m.rule || JSON.stringify(m.counts)}</span>
                      <button
                        onClick={async () => {
                          await api(`/memory/${kind}/${m.key}`, {
                            method: "DELETE",
                          });
                          load();
                        }}
                      >
                        Forget
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="muted">Nothing promoted yet.</p>
                )}
              </div>
            ))}
          </section>
        </div>
      </div>
    </>
  );
}
