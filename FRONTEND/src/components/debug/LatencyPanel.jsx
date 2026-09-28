/**
 * LatencyPanel — Admin-only debug panel showing per-message latency breakdown.
 *
 * Only visible when:
 *   - User is an admin, OR
 *   - URL contains ?debug=1
 *
 * Does NOT appear in normal user chat view.
 */

import React from "react";

const LatencyPanel = ({ latency, isAdmin }) => {
  // Only show for admins or in debug mode
  const isDebugMode =
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("debug") === "1";

  if (!latency || (!isAdmin && !isDebugMode)) {
    return null;
  }

  const {
    request_id,
    selected_model,
    agent,
    routing_ms = 0,
    planning_ms = 0,
    rag_ms = 0,
    tool_ms = 0,
    llm_ms = 0,
    total_ms = 0,
    cache_hit = false,
    cache_key,
    tokens_in = 0,
    tokens_out = 0,
  } = latency;

  const barMax = Math.max(routing_ms, rag_ms, llm_ms, tool_ms, 1);

  const BarChart = ({ label, ms, color }) => {
    const width = Math.max((ms / barMax) * 100, ms > 0 ? 3 : 0);
    return (
      <div style={{ marginBottom: 4 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
          <span style={{ color: "#888" }}>{label}</span>
          <span style={{ color: "#ccc", fontFamily: "monospace" }}>
            {ms > 0 ? `${Math.round(ms)}ms` : "—"}
          </span>
        </div>
        <div
          style={{
            height: 4,
            background: "#2a2a2a",
            borderRadius: 2,
            overflow: "hidden",
            marginTop: 2,
          }}
        >
          <div
            style={{
              width: `${width}%`,
              height: "100%",
              background: color,
              borderRadius: 2,
              transition: "width 0.3s ease",
            }}
          />
        </div>
      </div>
    );
  };

  return (
    <div
      style={{
        marginTop: 8,
        padding: "10px 12px",
        background: "#141414",
        border: "1px solid #2a2a2a",
        borderRadius: 8,
        fontSize: 12,
        fontFamily: "monospace",
        color: "#aaa",
        maxWidth: 340,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 8,
          borderBottom: "1px solid #222",
          paddingBottom: 6,
        }}
      >
        <span style={{ color: "#555", fontSize: 10, letterSpacing: 1 }}>
          ⚙ LATENCY DEBUG
        </span>
        <span
          style={{
            background: cache_hit ? "#1a3a1a" : "#1a1a2a",
            color: cache_hit ? "#4caf50" : "#7986cb",
            padding: "1px 6px",
            borderRadius: 4,
            fontSize: 10,
          }}
        >
          {cache_hit ? "⚡ CACHE HIT" : "🔍 CACHE MISS"}
        </span>
      </div>

      {/* Model & Agent */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ color: "#666", fontSize: 10, marginBottom: 2 }}>MODEL</div>
        <div style={{ color: "#e0e0e0", fontSize: 12 }}>
          {selected_model || "—"}
        </div>
        {agent && (
          <div style={{ color: "#777", fontSize: 10, marginTop: 2 }}>
            agent: {agent}
          </div>
        )}
      </div>

      {/* Bar Chart */}
      <div style={{ marginBottom: 8 }}>
        <BarChart label="Routing" ms={routing_ms} color="#7986cb" />
        <BarChart label="Planning" ms={planning_ms} color="#9c27b0" />
        <BarChart label="RAG" ms={rag_ms} color="#ff9800" />
        <BarChart label="Tools" ms={tool_ms} color="#ef5350" />
        <BarChart label="LLM" ms={llm_ms} color="#26a69a" />
      </div>

      {/* Total */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          borderTop: "1px solid #222",
          paddingTop: 6,
          marginTop: 4,
        }}
      >
        <span style={{ color: "#666" }}>Total</span>
        <span
          style={{
            color: total_ms > 5000 ? "#ef5350" : total_ms > 2000 ? "#ff9800" : "#4caf50",
            fontWeight: "bold",
          }}
        >
          {Math.round(total_ms)}ms
        </span>
      </div>

      {/* Token info */}
      {(tokens_in > 0 || tokens_out > 0) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 4,
            color: "#555",
            fontSize: 10,
          }}
        >
          <span>↑{tokens_in} tok</span>
          <span>↓{tokens_out} tok</span>
          {tokens_in > 0 && llm_ms > 0 && (
            <span>
              {Math.round((tokens_out / (llm_ms / 1000)))} tok/s
            </span>
          )}
        </div>
      )}

      {/* Request ID */}
      {request_id && (
        <div style={{ marginTop: 6, color: "#333", fontSize: 9 }}>
          {request_id}
        </div>
      )}
    </div>
  );
};

export default LatencyPanel;
