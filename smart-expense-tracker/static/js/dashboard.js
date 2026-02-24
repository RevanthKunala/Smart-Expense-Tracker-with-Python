/**
 * dashboard.js — Enhanced analytics dashboard with smart metrics, budget bars,
 * spending comparison, and Chart.js visualisations.
 */

document.addEventListener("DOMContentLoaded", () => {
  fetchAnalytics();
});

const INR = new Intl.NumberFormat("en-IN", {
  style: "currency", currency: "INR", maximumFractionDigits: 2
});

function fmt(n) { return INR.format(n); }

async function fetchAnalytics() {
  try {
    const res = await fetch("/api/analytics");
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    renderStatCards(data);
    renderSmartAnalytics(data);
    renderCharts(data);
    renderRecentTransactions(data.recent || []);
    removeShimmers();
  } catch (e) {
    console.error("Analytics load failed:", e);
    document.querySelectorAll(".shimmer").forEach(el => el.classList.remove("shimmer"));
  }
}

/* ── Stat Cards ─────────────────────────────────────────────── */
function renderStatCards(data) {
  // Month total — count-up
  const monthEl = document.getElementById("monthTotal");
  if (monthEl) countUp(monthEl, data.month_total, fmt);

  // Avg daily
  const avgEl = document.getElementById("avgDaily");
  if (avgEl) avgEl.textContent = fmt(data.smart?.avg_daily_spend ?? 0);

  // Top category
  const topCatEl = document.getElementById("topCategory");
  if (topCatEl) topCatEl.textContent = data.top_category?.name || "N/A";

  // vs Last Month
  const vsEl = document.getElementById("vsLastMonth");
  if (vsEl) {
    const pct = data.smart?.growth_pct ?? 0;
    const arrow = pct > 0 ? "↑" : pct < 0 ? "↓" : "→";
    vsEl.innerHTML = `<span class="${pct > 0 ? 'red' : pct < 0 ? 'green' : ''}">${arrow} ${Math.abs(pct)}%</span>`;
  }
}

/* ── Smart Analytics Row ────────────────────────────────────── */
function renderSmartAnalytics(data) {
  const smart = data.smart || {};

  // Predicted next month
  const predEl = document.getElementById("predicted");
  if (predEl) predEl.textContent = fmt(smart.predicted_next ?? 0);

  // Top 3 categories
  const top3El = document.getElementById("top3List");
  if (top3El && smart.top3_categories?.length) {
    const colors = ["🥇", "🥈", "🥉"];
    top3El.innerHTML = smart.top3_categories.map((cat, i) => `
      <div class="top3-item">
        <span>${colors[i]} ${cat.name}</span>
        <span class="amount-cell">${fmt(cat.total)}</span>
      </div>
    `).join("");
  } else if (top3El) {
    top3El.innerHTML = '<span style="color:var(--muted);font-size:.85rem">No data this month</span>';
  }

  // Budget status bars
  const budgetEl = document.getElementById("budgetStatus");
  if (budgetEl) {
    const budgets = data.budgets || [];
    if (budgets.length === 0) {
      budgetEl.innerHTML = `
        <p style="color:var(--muted);font-size:.82rem;margin:.25rem 0">No budgets set.</p>
        <a href="/budgets" class="btn btn-outline btn-sm" style="margin-top:.5rem">Set Budgets →</a>
      `;
    } else {
      budgetEl.innerHTML = budgets.map(b => {
        const cls = b.overspent ? "over" : b.over_80 ? "warn" : "ok";
        const icon = b.overspent ? "🔴" : b.over_80 ? "🟡" : "🟢";
        const cappedPct = Math.min(b.pct, 100);
        return `
          <div class="mini-budget">
            <div class="mini-budget-label">
              <span>${icon} ${b.label}</span>
              <span class="amount-cell" style="font-size:.78rem">${b.pct}%</span>
            </div>
            <div class="budget-bar-track mini">
              <div class="budget-bar-fill ${cls}" style="width:${cappedPct}%"></div>
            </div>
          </div>`;
      }).join("");
    }
  }
}

/* ── Charts ─────────────────────────────────────────────────── */
function renderCharts(data) {
  const PALETTE = [
    "#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#8b5cf6", "#06b6d4", "#84cc16"
  ];

  // Pie chart
  const pieCtx = document.getElementById("pieChart");
  if (pieCtx && data.category?.labels?.length) {
    new Chart(pieCtx, {
      type: "doughnut",
      data: {
        labels: data.category.labels,
        datasets: [{
          data: data.category.data, backgroundColor: PALETTE,
          borderWidth: 2, borderColor: "transparent"
        }]
      },
      options: {
        cutout: "65%",
        plugins: {
          legend: { position: "bottom", labels: { padding: 16, font: { size: 12 } } },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${fmt(ctx.parsed)}` } }
        }
      }
    });
  }

  // Line chart
  const lineCtx = document.getElementById("lineChart");
  if (lineCtx && data.monthly?.labels?.length) {
    new Chart(lineCtx, {
      type: "line",
      data: {
        labels: data.monthly.labels,
        datasets: [{
          label: "Monthly Spend",
          data: data.monthly.data,
          borderColor: "#6366f1",
          backgroundColor: "rgba(99,102,241,.1)",
          pointBackgroundColor: "#6366f1",
          pointRadius: 5,
          fill: true,
          tension: 0.35,
        }]
      },
      options: {
        scales: {
          y: {
            ticks: { callback: (v) => "₹" + v.toLocaleString("en-IN") },
            grid: { color: "rgba(100,116,139,.12)" }
          },
          x: { grid: { display: false } }
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => `₹${ctx.parsed.y.toLocaleString("en-IN")}` } }
        }
      }
    });
  }
}

/* ── Recent Transactions ─────────────────────────────────────── */
function renderRecentTransactions(recent) {
  const el = document.getElementById("recentList");
  if (!el) return;
  if (!recent?.length) {
    el.innerHTML = `<div class="empty-state" style="padding:2rem 1rem">
      <div class="empty-icon">📭</div>
      <p>No recent transactions.</p>
    </div>`;
    return;
  }

  const rows = recent.map(r => {
    const slug = (r.category || "").toLowerCase().replace(/\s+/g, "");
    const date = new Date(r.date + "T00:00:00");
    const dateStr = date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
    return `<div class="recent-row">
      <div class="recent-info">
        <span class="badge badge-${slug}">${r.category}</span>
        <span class="recent-desc">${r.description}</span>
      </div>
      <div class="recent-right">
        <span class="amount-cell">${fmt(r.amount)}</span>
        <span class="date-cell" style="margin-left:.75rem">${dateStr}</span>
      </div>
    </div>`;
  }).join("");

  el.innerHTML = `<div class="recent-list">${rows}</div>`;
}

/* ── Helpers ──────────────────────────────────────────────────── */
function removeShimmers() {
  document.querySelectorAll(".shimmer").forEach(el => el.classList.remove("shimmer"));
}

function countUp(el, target, formatter) {
  const duration = 900;
  const start = Date.now();
  const tick = () => {
    const elapsed = Date.now() - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = formatter(target * ease);
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
