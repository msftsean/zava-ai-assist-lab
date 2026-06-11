// Zava Guardrails Console — React-based tactical command-center UI
const { useState, useEffect, useRef } = React;
const { createRoot } = ReactDOM;

// ══════════════════════════════════════════════════════════════════════════════
// API HELPERS
// ══════════════════════════════════════════════════════════════════════════════

const api = (path, opts = {}) =>
  fetch(`/demo${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  }).then(async (r) => {
    if (!r.ok) {
      const text = await r.text();
      throw new Error(`${r.status}: ${text}`);
    }
    return r.json();
  });

const escapeHtml = (s) =>
  String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

// ══════════════════════════════════════════════════════════════════════════════
// VERDICT HELPERS
// ══════════════════════════════════════════════════════════════════════════════

function verdictClass(v) {
  if (v === "allowed") return "safe";
  if (v === "injection_flagged") return "warn";
  return "danger";
}

function verdictLabel(v) {
  const labels = {
    allowed: "ALLOWED",
    blocked_input: "BLOCKED · INPUT",
    blocked_output: "BLOCKED · OUTPUT",
    injection_flagged: "INJECTION FLAGGED",
    error_input_safety: "ERROR · INPUT SAFETY",
    error_output_safety: "ERROR · OUTPUT SAFETY",
    error_model: "ERROR · MODEL",
  };
  return labels[v] || v.toUpperCase();
}

function scenarioColor(expected) {
  if (expected === "allowed") return "scenario-safe";
  if (expected === "blocked_input" || expected === "malicious") return "scenario-danger";
  if (expected === "injection_flagged") return "scenario-warn";
  return "scenario-info";
}

// ══════════════════════════════════════════════════════════════════════════════
// ICONS
// ══════════════════════════════════════════════════════════════════════════════

const StatusLED = ({ status, label }) => (
  <div className="status-led">
    <span className={`led ${status}`}></span>
    <span className="led-label">{label}</span>
  </div>
);

// ══════════════════════════════════════════════════════════════════════════════
// MAIN APP
// ══════════════════════════════════════════════════════════════════════════════

function App() {
  const [activeTab, setActiveTab] = useState("live");
  const [scenarios, setScenarios] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [config, setConfig] = useState(null);
  const [lastTrace, setLastTrace] = useState(null);
  const [auditEntries, setAuditEntries] = useState([]);
  const [auditSize, setAuditSize] = useState(0);
  const [loading, setLoading] = useState(true);
  const [services, setServices] = useState({
    contentSafety: "ready",
    promptShields: "ready",
    openAI: "ready",
  });

  // Fetch initial data
  useEffect(() => {
    Promise.all([
      api("/scenarios"),
      api("/profiles"),
      api("/config"),
      api("/audit?limit=50"),
    ])
      .then(([scenariosData, profilesData, configData, auditData]) => {
        setScenarios(scenariosData.scenarios || []);
        setProfiles(profilesData.profiles || []);
        setCategories(profilesData.categories || []);
        setConfig(configData);
        setAuditEntries(auditData.entries || []);
        setAuditSize(auditData.size || 0);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Init failed:", err);
        setLoading(false);
      });
  }, []);

  const refreshAudit = async () => {
    try {
      const data = await api("/audit?limit=50");
      setAuditEntries(data.entries || []);
      setAuditSize(data.size || 0);
    } catch (err) {
      console.error("Audit refresh failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>INITIALIZING CONSOLE...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <Header services={services} />
      <TabBar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="content">
        {activeTab === "live" && (
          <LiveTestTab
            scenarios={scenarios}
            setLastTrace={setLastTrace}
            setServices={setServices}
            refreshAudit={refreshAudit}
          />
        )}
        {activeTab === "trace" && <TraceTab trace={lastTrace} categories={categories} />}
        {activeTab === "tuning" && (
          <TuningTab
            profiles={profiles}
            categories={categories}
            config={config}
            setConfig={setConfig}
          />
        )}
        {activeTab === "audit" && (
          <AuditTab
            entries={auditEntries}
            size={auditSize}
            refreshAudit={refreshAudit}
          />
        )}
        {activeTab === "architecture" && <ArchitectureTab />}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// HEADER
// ══════════════════════════════════════════════════════════════════════════════

function Header({ services }) {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-logo" aria-hidden="true">Zava</span>
        <div className="header-title">
          <h1>Zava Guardrails Console</h1>
          <p className="header-subtitle">
            Azure AI Content Safety · Prompt Shields · Azure OpenAI
          </p>
        </div>
      </div>
      <div className="header-status">
        <StatusLED status={services.contentSafety} label="CONTENT SAFETY" />
        <StatusLED status={services.promptShields} label="PROMPT SHIELDS" />
        <StatusLED status={services.openAI} label="AZURE OPENAI" />
      </div>
    </header>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB BAR
// ══════════════════════════════════════════════════════════════════════════════

function TabBar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: "live", label: "◉ LIVE TEST" },
    { id: "trace", label: "▣ TRACE" },
    { id: "tuning", label: "◎ TUNING" },
    { id: "audit", label: "▲ AUDIT" },
    { id: "architecture", label: "◈ ARCHITECTURE" },
  ];

  return (
    <nav className="tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab ${activeTab === tab.id ? "active" : ""}`}
          onClick={() => setActiveTab(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// LIVE TEST TAB
// ══════════════════════════════════════════════════════════════════════════════

function LiveTestTab({ scenarios, setLastTrace, setServices, refreshAudit }) {
  const [prompt, setPrompt] = useState("");
  const [running, setRunning] = useState(false);
  const [traceResult, setTraceResult] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [elapsed, setElapsed] = useState(0);

  React.useEffect(() => {
    if (!running) { setElapsed(0); return; }
    const start = Date.now();
    const id = setInterval(() => setElapsed(((Date.now() - start) / 1000)), 100);
    return () => clearInterval(id);
  }, [running]);

  const runPipeline = async () => {
    if (!prompt.trim()) return;
    setRunning(true);
    setTraceResult(null);
    try {
      const result = await api("/chat", {
        method: "POST",
        body: JSON.stringify({ prompt }),
      });
      setTraceResult(result);
      setLastTrace(result);
      await refreshAudit();
      // Update service status based on result
      const hasShield = result.stages?.prompt_shield?.source === "azure";
      setServices({
        contentSafety: result.stages?.input_safety?.is_safe !== undefined ? "ready" : "error",
        promptShields: hasShield ? "ready" : "fallback",
        openAI: result.stages?.model?.called ? "ready" : "ready",
      });
    } catch (err) {
      console.error("Pipeline error:", err);
      setServices((s) => ({ ...s, openAI: "error" }));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="tab-content">
      <section className="section">
        <h2 className="section-title">SCENARIO PRESETS</h2>
        <div className="scenario-chips">
          {scenarios.map((s) => (
            <button
              key={s.id}
              className={`scenario-chip ${scenarioColor(s.expected)}`}
              onClick={() => {
                setPrompt(s.prompt);
                setExplanation(`Expected: ${s.expected} — ${s.explanation}`);
              }}
              title={s.explanation}
            >
              {s.label}
            </button>
          ))}
        </div>
        {explanation && <p className="explanation">{explanation}</p>}
      </section>

      <section className="section">
        <h2 className="section-title">INPUT PROMPT</h2>
        <textarea
          className="prompt-input"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type a prompt to test the guardrails pipeline..."
          rows={4}
        />
        <button
          className="btn btn-primary"
          onClick={runPipeline}
          disabled={running || !prompt.trim()}
        >
          {running ? `⏳ RUNNING... ${elapsed.toFixed(1)}s` : "▶ RUN PIPELINE"}
        </button>
        {running && (
          <div style={{ marginTop: 12, padding: "10px 14px", background: "rgba(56,189,248,0.08)", border: "1px solid rgba(56,189,248,0.4)", borderRadius: 4, fontSize: 12, fontFamily: "var(--font-mono)", color: "#7dd3fc" }}>
            <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#38bdf8", marginRight: 8, animation: "pulse 1s ease-in-out infinite" }}></span>
            CALLING AZURE PIPELINE — Prompt Shield → Content Safety (in) → OpenAI → Content Safety (out). Typical latency: 8–20s.
          </div>
        )}
      </section>

      {traceResult && (
        <>
          <PipelineVisualization trace={traceResult} />
          <VerdictBanner verdict={traceResult.verdict} />
          {traceResult.output && (
            <section className="section">
              <h2 className="section-title">ASSISTANT OUTPUT</h2>
              <pre className="output-box">{traceResult.output}</pre>
            </section>
          )}
        </>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// PIPELINE VISUALIZATION
// ══════════════════════════════════════════════════════════════════════════════

function PipelineVisualization({ trace }) {
  const nodes = [
    { id: "input", label: "INPUT", status: "complete" },
    {
      id: "shield",
      label: "PROMPT SHIELD",
      status: trace.stages?.prompt_shield
        ? trace.stages.prompt_shield.detected
          ? "flagged"
          : "complete"
        : "skipped",
    },
    {
      id: "input_safety",
      label: "CONTENT SAFETY (IN)",
      status: trace.stages?.input_safety
        ? trace.stages.input_safety.is_safe
          ? "complete"
          : "blocked"
        : "skipped",
    },
    {
      id: "model",
      label: "AZURE OPENAI",
      status: trace.stages?.model?.called
        ? trace.stages.model.error
          ? "error"
          : "complete"
        : "skipped",
    },
    {
      id: "output_safety",
      label: "CONTENT SAFETY (OUT)",
      status: trace.stages?.output_safety
        ? trace.stages.output_safety.is_safe
          ? "complete"
          : "blocked"
        : "skipped",
    },
  ];

  return (
    <section className="section">
      <h2 className="section-title">PIPELINE FLOW</h2>
      <div className="pipeline">
        {nodes.map((node, idx) => (
          <React.Fragment key={node.id}>
            <div className={`pipeline-node ${node.status}`}>
              <div className="node-label">{node.label}</div>
              <div className="node-status">{node.status.toUpperCase()}</div>
            </div>
            {idx < nodes.length - 1 && <div className="pipeline-arrow">→</div>}
          </React.Fragment>
        ))}
      </div>
    </section>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// VERDICT BANNER
// ══════════════════════════════════════════════════════════════════════════════

function VerdictBanner({ verdict }) {
  return (
    <div className={`verdict-banner ${verdictClass(verdict)}`}>
      <div className="verdict-label">{verdictLabel(verdict)}</div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TRACE TAB
// ══════════════════════════════════════════════════════════════════════════════

function TraceTab({ trace, categories }) {
  if (!trace) {
    return (
      <div className="tab-content">
        <div className="empty-state">
          <p>No trace data yet. Run a test from the LIVE TEST tab.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tab-content">
      <TraceCard title="PROMPT SHIELD" stage={trace.stages?.prompt_shield} type="shield" />
      <TraceCard
        title="INPUT CONTENT SAFETY"
        stage={trace.stages?.input_safety}
        type="safety"
        categories={categories}
      />
      <TraceCard title="AZURE OPENAI MODEL" stage={trace.stages?.model} type="model" />
      <TraceCard
        title="OUTPUT CONTENT SAFETY"
        stage={trace.stages?.output_safety}
        type="safety"
        categories={categories}
      />
    </div>
  );
}

function TraceCard({ title, stage, type, categories }) {
  if (!stage) {
    return (
      <section className="section trace-card">
        <h2 className="section-title">{title}</h2>
        <p className="muted">Stage not executed</p>
      </section>
    );
  }

  return (
    <section className="section trace-card">
      <h2 className="section-title">{title}</h2>
      {type === "shield" && <ShieldDetails stage={stage} />}
      {type === "safety" && <SafetyDetails stage={stage} categories={categories} />}
      {type === "model" && <ModelDetails stage={stage} />}
    </section>
  );
}

function ShieldDetails({ stage }) {
  return (
    <div className="trace-details">
      <div className="trace-row">
        <span className="trace-key">Detected:</span>
        <span className={stage.detected ? "badge-danger" : "badge-safe"}>
          {stage.detected ? "YES" : "NO"}
        </span>
      </div>
      <div className="trace-row">
        <span className="trace-key">Confidence:</span>
        <span className="trace-value mono">{stage.confidence || "none"}</span>
      </div>
      <div className="trace-row">
        <span className="trace-key">Risk Score:</span>
        <span className="trace-value mono">{stage.risk_score}</span>
      </div>
      <div className="trace-row">
        <span className="trace-key">Source:</span>
        <span className="trace-value mono">{stage.source}</span>
      </div>
      {stage.patterns && stage.patterns.length > 0 && (
        <div className="trace-row">
          <span className="trace-key">Patterns:</span>
          <span className="trace-value">{stage.patterns.join(", ")}</span>
        </div>
      )}
    </div>
  );
}

function SafetyDetails({ stage, categories }) {
  return (
    <div className="trace-details">
      <div className="trace-row">
        <span className="trace-key">Safe:</span>
        <span className={stage.is_safe ? "badge-safe" : "badge-danger"}>
          {stage.is_safe ? "YES" : "NO"}
        </span>
      </div>
      <div className="trace-row">
        <span className="trace-key">Profile:</span>
        <span className="trace-value mono">{stage.profile}</span>
      </div>
      {stage.blocked_categories && stage.blocked_categories.length > 0 && (
        <div className="trace-row">
          <span className="trace-key">Blocked:</span>
          <span className="badge-danger">{stage.blocked_categories.join(", ")}</span>
        </div>
      )}
      <div className="severity-grid">
        {Object.entries(stage.severities || {}).map(([cat, sev]) => {
          const threshold =
            stage.category_details?.[cat]?.threshold ?? "—";
          const blocked = stage.blocked_categories?.includes(cat);
          return (
            <div key={cat} className={`severity-row ${blocked ? "blocked" : ""}`}>
              <div className="severity-cat">{cat}</div>
              <div className="severity-bar-wrap">
                <div className="severity-bar-bg">
                  <div
                    className={`severity-bar-fill ${blocked ? "blocked" : ""}`}
                    style={{ width: `${(sev / 6) * 100}%` }}
                  ></div>
                </div>
                <span className="severity-value mono">{sev}</span>
              </div>
              <div className="severity-threshold mono">≤ {threshold}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ModelDetails({ stage }) {
  if (!stage.called) {
    return <p className="muted">Model not called (blocked by upstream checks)</p>;
  }

  return (
    <div className="trace-details">
      <div className="trace-row">
        <span className="trace-key">Deployment:</span>
        <span className="trace-value mono">{stage.deployment}</span>
      </div>
      <div className="trace-row">
        <span className="trace-key">Latency:</span>
        <span className="trace-value mono">{stage.latency_ms} ms</span>
      </div>
      {stage.error && (
        <div className="trace-row">
          <span className="trace-key">Error:</span>
          <span className="badge-danger">{stage.error}</span>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TUNING TAB
// ══════════════════════════════════════════════════════════════════════════════

function TuningTab({ profiles, categories, config, setConfig }) {
  const [selectedProfile, setSelectedProfile] = useState(config?.profile_name || "standard");
  const [thresholds, setThresholds] = useState(config?.custom_thresholds || {});
  const [blocklist, setBlocklist] = useState((config?.blocklist || []).join("\n"));
  const [shieldEnabled, setShieldEnabled] = useState(config?.prompt_shield_enabled ?? true);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (config) {
      setSelectedProfile(config.profile_name || "standard");
      setThresholds(config.custom_thresholds || {});
      setBlocklist((config.blocklist || []).join("\n"));
      setShieldEnabled(config.prompt_shield_enabled ?? true);
    }
  }, [config]);

  const saveConfig = async () => {
    setStatus("Saving...");
    try {
      const blocklistArray = blocklist
        .split(/\r?\n/)
        .map((t) => t.trim())
        .filter(Boolean);
      const newConfig = await api("/config", {
        method: "POST",
        body: JSON.stringify({
          profile_name: selectedProfile,
          custom_thresholds: thresholds,
          blocklist: blocklistArray,
          prompt_shield_enabled: shieldEnabled,
        }),
      });
      setConfig(newConfig);
      setStatus("Saved ✓");
      setTimeout(() => setStatus(""), 2000);
    } catch (err) {
      setStatus("Error: " + err.message);
    }
  };

  const resetConfig = async () => {
    setStatus("Resetting...");
    try {
      const newConfig = await api("/config", {
        method: "POST",
        body: JSON.stringify({
          profile_name: "standard",
          custom_thresholds: {},
          blocklist: [],
          prompt_shield_enabled: true,
        }),
      });
      setConfig(newConfig);
      setStatus("Reset ✓");
      setTimeout(() => setStatus(""), 2000);
    } catch (err) {
      setStatus("Error: " + err.message);
    }
  };

  const selectedProfileObj = profiles.find((p) => p.name === selectedProfile);

  return (
    <div className="tab-content">
      <section className="section">
        <h2 className="section-title">FILTER PROFILE</h2>
        <div className="profile-grid">
          {profiles.map((p) => (
            <div
              key={p.name}
              className={`profile-card ${selectedProfile === p.name ? "active" : ""}`}
              onClick={() => setSelectedProfile(p.name)}
            >
              <div className="profile-name">{p.name.toUpperCase()}</div>
              <div className="profile-desc">{p.description}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">CUSTOM THRESHOLDS (0 = STRICTEST · 6 = PERMISSIVE)</h2>
        <div className="threshold-grid">
          {categories.map((cat) => {
            const baseValue =
              selectedProfileObj?.thresholds?.[cat] ?? thresholds[cat] ?? 2;
            const currentValue = thresholds[cat] ?? baseValue;
            return (
              <div key={cat} className="threshold-row">
                <label className="threshold-label">{cat}</label>
                <input
                  type="range"
                  min="0"
                  max="6"
                  step="1"
                  value={currentValue}
                  onChange={(e) =>
                    setThresholds({ ...thresholds, [cat]: parseInt(e.target.value, 10) })
                  }
                  className="threshold-slider"
                />
                <span className="threshold-value mono">{currentValue}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">PROMPT SHIELDS</h2>
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={shieldEnabled}
            onChange={(e) => setShieldEnabled(e.target.checked)}
            className="toggle-input"
          />
          <span className="toggle-switch"></span>
          <span className="toggle-text">
            Use Azure Prompt Shields (uncheck for regex fallback)
          </span>
        </label>
      </section>

      <section className="section">
        <h2 className="section-title">CUSTOM BLOCKLIST (one term per line)</h2>
        <textarea
          className="blocklist-input"
          value={blocklist}
          onChange={(e) => setBlocklist(e.target.value)}
          placeholder="e.g.&#10;classified&#10;internal-only"
          rows={6}
        />
      </section>

      <div className="action-row">
        <button className="btn btn-primary" onClick={saveConfig}>
          💾 SAVE
        </button>
        <button className="btn btn-secondary" onClick={resetConfig}>
          ↺ RESET
        </button>
        {status && <span className="status-text">{status}</span>}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// AUDIT TAB
// ══════════════════════════════════════════════════════════════════════════════

function AuditTab({ entries, size, refreshAudit }) {
  const [expandedId, setExpandedId] = useState(null);

  const clearAudit = async () => {
    try {
      await api("/audit", { method: "DELETE" });
      await refreshAudit();
    } catch (err) {
      console.error("Clear audit failed:", err);
    }
  };

  return (
    <div className="tab-content">
      <section className="section">
        <div className="audit-header">
          <h2 className="section-title">AUDIT LOG ({size} entries)</h2>
          <div className="audit-actions">
            <button className="btn btn-secondary" onClick={refreshAudit}>
              ⟳ REFRESH
            </button>
            <button className="btn btn-danger" onClick={clearAudit}>
              🗑 CLEAR
            </button>
          </div>
        </div>

        {entries.length === 0 ? (
          <div className="empty-state">
            <p>No audit entries yet. Run a test from the LIVE TEST tab.</p>
          </div>
        ) : (
          <div className="audit-table">
            {entries.map((entry, idx) => (
              <AuditRow
                key={entry.id || idx}
                entry={entry}
                expanded={expandedId === (entry.id || idx)}
                onToggle={() =>
                  setExpandedId(expandedId === (entry.id || idx) ? null : entry.id || idx)
                }
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function AuditRow({ entry, expanded, onToggle }) {
  const timestamp = entry.timestamp?.replace("T", " ").slice(0, 19) || "—";
  const blockedIn = entry.stages?.input_safety?.blocked_categories || [];
  const blockedOut = entry.stages?.output_safety?.blocked_categories || [];

  return (
    <div className="audit-row">
      <div className="audit-row-main" onClick={onToggle}>
        <div className="audit-col audit-time mono">{timestamp}</div>
        <div className="audit-col audit-verdict">
          <span className={`verdict-chip ${verdictClass(entry.verdict)}`}>
            {verdictLabel(entry.verdict)}
          </span>
        </div>
        <div className="audit-col audit-prompt">{entry.prompt?.slice(0, 80) || "—"}</div>
        <div className="audit-col audit-categories mono">
          {blockedIn.length > 0 ? blockedIn.join(", ") : "—"}
        </div>
      </div>
      {expanded && (
        <div className="audit-row-detail">
          <pre className="audit-json">{JSON.stringify(entry, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// ARCHITECTURE TAB
// ══════════════════════════════════════════════════════════════════════════════

function ArchitectureTab() {
  return (
    <div className="tab-content">
      <section className="section">
        <h2 className="section-title">SYSTEM ARCHITECTURE</h2>
        <div className="architecture-diagram">
          <div className="arch-box user">USER</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box service">FASTAPI ROUTER</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box azure">PROMPT SHIELDS<br /><small>(Azure / Regex Fallback)</small></div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box azure">CONTENT SAFETY<br /><small>(Input Pre-Check)</small></div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box azure">AZURE OPENAI<br /><small>(GPT-4o)</small></div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box azure">CONTENT SAFETY<br /><small>(Output Post-Check)</small></div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box service">AUDIT LOG<br /><small>(Ring Buffer)</small></div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box user">RESPONSE</div>
        </div>

        <div className="arch-annotation">
          <p className="arch-title">SECURITY POSTURE</p>
          <ul>
            <li>✓ All Azure services accessed via <strong>DefaultAzureCredential</strong></li>
            <li>✓ Keyless authentication using <strong>Entra ID (Azure AD)</strong></li>
            <li>✓ Managed Identity with RBAC-scoped permissions</li>
            <li>✓ FedRAMP-aligned Azure Government endpoints</li>
            <li>✓ Configurable severity thresholds (0–6) for 4 content categories</li>
            <li>✓ Dual-phase safety checks (pre-model + post-model)</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// RENDER
// ══════════════════════════════════════════════════════════════════════════════

const root = createRoot(document.getElementById("root"));
root.render(<App />);
