/**
 * FraudShield AI — UI Utilities
 * Toast notifications, formatters, loaders, and shared helpers.
 */

// ── Toast ──────────────────────────────────────────────────────
function toast(msg, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300); }, duration);
}

// ── Formatters ────────────────────────────────────────────────
function fmtCurrency(n) {
  if (n === null || n === undefined) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(n);
}

function fmtPct(n, decimals = 1) {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toFixed(decimals)}%`;
}

function fmtNum(n) {
  if (n === null || n === undefined) return '—';
  return new Intl.NumberFormat('en-US').format(n);
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function fmtScore(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toFixed(4);
}

// ── Risk Badge HTML ────────────────────────────────────────────
function riskBadge(risk) {
  const map = { High: 'badge-high', Medium: 'badge-medium', Low: 'badge-low' };
  return `<span class="badge ${map[risk] || 'badge-low'}">${risk || '—'}</span>`;
}

// ── Case Status Badge ──────────────────────────────────────────
function statusBadge(status) {
  const map = {
    'Open':          'badge-open',
    'Under Review':  'badge-review',
    'Escalated':     'badge-high',
    'Resolved':      'badge-resolved',
    'False Positive':'badge-fp',
  };
  return `<span class="badge ${map[status] || 'badge-open'}">${status || '—'}</span>`;
}

// ── Loader Helpers ─────────────────────────────────────────────
function showLoader(el) {
  el.classList.add('loading');
  el._prev = el.innerHTML;
  el.innerHTML = `<span class="spinner"></span>`;
  el.disabled = true;
}
function hideLoader(el, label) {
  el.classList.remove('loading');
  el.innerHTML = label || el._prev || '';
  el.disabled = false;
}

// ── Empty State HTML ───────────────────────────────────────────
function emptyState(icon, title, desc) {
  return `<div class="empty-state">
    <div class="empty-icon">${icon}</div>
    <div class="empty-title">${title}</div>
    <div class="empty-desc">${desc}</div>
  </div>`;
}

// ── Sidebar Active Link ────────────────────────────────────────
function setActiveNav() {
  const path = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(a => {
    const href = a.getAttribute('href').split('/').pop();
    a.classList.toggle('active', href === path);
  });
}

// ── SHAP Feature Bars ──────────────────────────────────────────
function renderShapBars(features, containerId) {
  const el = document.getElementById(containerId);
  if (!el || !features || !features.length) {
    if (el) el.innerHTML = emptyState('🔬', 'No Explanation Available', 'SHAP explanations require a tree-based model.');
    return;
  }
  const maxAbs = Math.max(...features.map(f => Math.abs(f.importance)));
  el.innerHTML = features.map(f => {
    const pct = Math.abs(f.importance) / maxAbs * 100;
    const cls = f.importance > 0 ? 'positive' : 'negative';
    const dir = f.importance > 0 ? '↑ Increases risk' : '↓ Decreases risk';
    return `<div class="shap-row" title="${dir}">
      <div class="shap-name">${f.feature}</div>
      <div class="shap-bar-track"><div class="shap-bar-fill ${cls}" style="width:${pct}%"></div></div>
      <div class="shap-value">${f.importance > 0 ? '+' : ''}${f.importance.toFixed(3)}</div>
    </div>`;
  }).join('');
}

// ── Progress bar helper ────────────────────────────────────────
function progressBar(value, colorVar = 'var(--accent)') {
  const pct = Math.min(100, Math.max(0, value * 100)).toFixed(1);
  return `<div class="progress-track" style="width:120px">
    <div class="progress-fill" style="width:${pct}%;background:${colorVar}"></div>
  </div>`;
}

// ── Confusion Matrix mini table ────────────────────────────────
function renderConfusionMatrix(cm, containerId) {
  if (!cm || !cm.length) return;
  const el = document.getElementById(containerId);
  if (!el) return;
  const [[tn, fp], [fn, tp]] = cm;
  el.innerHTML = `
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:10px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase">Confusion Matrix</div>
    <table style="border-collapse:collapse;font-size:12px;width:100%">
      <thead><tr>
        <th style="padding:6px;color:var(--text-muted)"></th>
        <th style="padding:6px;color:var(--text-secondary);text-align:center">Pred: Legit</th>
        <th style="padding:6px;color:var(--text-secondary);text-align:center">Pred: Fraud</th>
      </tr></thead>
      <tbody>
        <tr>
          <td style="padding:6px;color:var(--text-secondary)">Actual: Legit</td>
          <td style="padding:10px;text-align:center;background:var(--success-bg);color:var(--success);font-weight:700;border-radius:6px">${fmtNum(tn)}</td>
          <td style="padding:10px;text-align:center;background:var(--danger-bg);color:var(--danger);font-weight:700;border-radius:6px">${fmtNum(fp)}</td>
        </tr>
        <tr>
          <td style="padding:6px;color:var(--text-secondary)">Actual: Fraud</td>
          <td style="padding:10px;text-align:center;background:var(--warning-bg);color:var(--warning);font-weight:700;border-radius:6px">${fmtNum(fn)}</td>
          <td style="padding:10px;text-align:center;background:var(--success-bg);color:var(--success);font-weight:700;border-radius:6px">${fmtNum(tp)}</td>
        </tr>
      </tbody>
    </table>`;
}

// ── Sidebar HTML (shared across pages) ────────────────────────
// Dynamically resolves paths based on whether we're in root or pages/
function getSidebarHTML() {
  // Detect depth: pages in /pages/ are one level deep
  const isInSubdir = location.pathname.includes('/pages/');
  const root  = isInSubdir ? '../'  : '';
  const pages = isInSubdir ? ''     : 'pages/';
  return `
<nav class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-icon">🛡️</div>
    <div>
      <div class="brand-name">FraudShield</div>
      <div class="brand-sub">AI Platform</div>
    </div>
  </div>
  <div class="sidebar-nav">
    <div class="nav-section-label">Analysis</div>
    <a href="${root}index.html"                     class="nav-link" id="nav-dashboard">      <span class="nav-icon">📊</span><span>Dashboard</span></a>
    <a href="${root}${pages}analyzer.html"          class="nav-link" id="nav-analyzer">      <span class="nav-icon">🔍</span><span>Transaction Analyzer</span></a>
    <a href="${root}${pages}batch.html"             class="nav-link" id="nav-batch">         <span class="nav-icon">📂</span><span>Batch Analysis</span></a>
    <div class="nav-section-label">Operations</div>
    <a href="${root}${pages}investigations.html"    class="nav-link" id="nav-investigations"><span class="nav-icon">🗂️</span><span>Investigations</span></a>
    <div class="nav-section-label">Intelligence</div>
    <a href="${root}${pages}model.html"             class="nav-link" id="nav-model">         <span class="nav-icon">🤖</span><span>Model Performance</span></a>
  </div>
  <div class="sidebar-footer">
    <span class="status-dot"><span>API Connected</span></span>
  </div>
</nav>`;
}
// Legacy alias so existing pages still work
const SIDEBAR_HTML = getSidebarHTML();

// Expose globals
window.toast = toast;
window.fmtCurrency = fmtCurrency;
window.fmtPct = fmtPct;
window.fmtNum = fmtNum;
window.fmtDate = fmtDate;
window.fmtScore = fmtScore;
window.riskBadge = riskBadge;
window.statusBadge = statusBadge;
window.showLoader = showLoader;
window.hideLoader = hideLoader;
window.emptyState = emptyState;
window.setActiveNav = setActiveNav;
window.renderShapBars = renderShapBars;
window.progressBar = progressBar;
window.renderConfusionMatrix = renderConfusionMatrix;
window.SIDEBAR_HTML = getSidebarHTML();
window.getSidebarHTML = getSidebarHTML;
