/**
 * FraudShield AI — API Client & Interactive Demo Engine
 * Connects to the FastAPI backend with seamless interactive simulation fallback for live web demos.
 */

const API_BASE = window.FRAUDSHIELD_API_URL || 'http://localhost:8000';
let isDemoMode = false;

// In-memory demo store for interactive client-side usage
const demoStore = {
  stats: {
    total_transactions: 104280,
    total_suspicious: 1072,
    total_legitimate: 103208,
    fraud_detection_rate: 1.028,
    average_risk_score: 0.0485,
    high_risk_count: 846,
    medium_risk_count: 226,
    low_risk_count: 103208
  },
  recentSuspicious: [
    { id: "TXN-984210", type: "TRANSFER", amount: 350000.00, risk: "High", score: 0.9992, time: "2 mins ago", origin: "C182749102", dest: "C992817264" },
    { id: "TXN-984198", type: "CASH_OUT", amount: 185000.00, risk: "High", score: 0.9845, time: "8 mins ago", origin: "C552140921", dest: "M102938475" },
    { id: "TXN-984152", type: "TRANSFER", amount: 64200.00, risk: "High", score: 0.9412, time: "24 mins ago", origin: "C391029481", dest: "C401928374" },
    { id: "TXN-984090", type: "CASH_OUT", amount: 48900.00, risk: "Medium", score: 0.6280, time: "41 mins ago", origin: "C190283746", dest: "C772819034" },
    { id: "TXN-984012", type: "TRANSFER", amount: 12500.00, risk: "Medium", score: 0.4530, time: "1 hour ago", origin: "C662910293", dest: "C112938475" },
    { id: "TXN-983981", type: "CASH_OUT", amount: 92000.00, risk: "High", score: 0.9634, time: "2 hours ago", origin: "C449102938", dest: "C551928374" }
  ],
  investigations: [
    { id: "INV-1001", transaction_id: "TXN-984210", amount: 350000.00, risk_score: 0.9992, status: "Open", notes: "Large zero-balance transfer flagged by XGBoost & SHAP", updated_at: new Date().toISOString() },
    { id: "INV-1002", transaction_id: "TXN-984198", amount: 185000.00, risk_score: 0.9845, status: "Under Review", notes: "Rapid cash out after deposit", updated_at: new Date(Date.now() - 3600000).toISOString() },
    { id: "INV-1003", transaction_id: "TXN-984152", amount: 64200.00, risk_score: 0.9412, status: "Escalated", notes: "Anomalous destination account", updated_at: new Date(Date.now() - 7200000).toISOString() },
    { id: "INV-1004", transaction_id: "TXN-984090", amount: 48900.00, risk_score: 0.6280, status: "Resolved", notes: "Verified with customer phone confirmation", updated_at: new Date(Date.now() - 86400000).toISOString() }
  ],
  metrics: {
    model_name: "XGBoost",
    model_version: "1.0.0",
    training_date: "2026-11-11T23:07:36.566800",
    threshold: 0.1,
    precision_score: 1.0,
    recall_score: 1.0,
    f1_score: 1.0,
    roc_auc_score: 1.0,
    pr_auc_score: 1.0,
    confusion_matrix: [[9893, 0], [0, 107]],
    training_samples: 78930,
    test_samples: 10000,
    feature_columns: [
      "transaction_type_encoded", "amount", "origin_balance_before", "origin_balance_after",
      "dest_balance_before", "dest_balance_after", "balance_diff_origin", "balance_diff_dest",
      "amount_to_origin_ratio", "is_large_transfer"
    ],
    shap_feature_importance: {
      "transaction_type_encoded": 0.723,
      "amount": 2.335,
      "origin_balance_before": 0.018,
      "origin_balance_after": 2.886,
      "dest_balance_before": 0.040,
      "dest_balance_after": 0.323,
      "balance_diff_origin": 2.515,
      "balance_diff_dest": 2.793,
      "amount_to_origin_ratio": 0.336,
      "is_large_transfer": 0.0
    },
    all_models: [
      { model_name: "XGBoost", precision: 1.0, recall: 1.0, f1: 1.0, roc_auc: 1.0, pr_auc: 1.0 },
      { model_name: "Random Forest", precision: 0.985, recall: 0.942, f1: 0.963, roc_auc: 0.998, pr_auc: 0.971 },
      { model_name: "Logistic Regression", precision: 0.812, recall: 0.764, f1: 0.787, roc_auc: 0.942, pr_auc: 0.825 }
    ]
  }
};

function updateHealthPill(online) {
  const el = document.getElementById('health-indicator');
  if (!el) return;
  if (online) {
    el.className = 'status-dot text-success';
    el.innerHTML = '<span>● Live Backend Connected</span>';
  } else {
    el.className = 'status-dot text-warning';
    el.innerHTML = '<span title="Running with client-side interactive demo engine">⚡ Interactive Demo Mode</span>';
  }
}

const api = {
  async request(method, path, body = null) {
    if (isDemoMode) {
      return api.mockRoute(method, path, body);
    }
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);

    try {
      const res = await fetch(`${API_BASE}${path}`, opts);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        const msg = typeof err.detail === 'string' ? err.detail : err.detail?.message || JSON.stringify(err.detail);
        throw new Error(msg);
      }
      updateHealthPill(true);
      return res.json();
    } catch (e) {
      // If server unreachable or error, switch to interactive demo mode
      console.warn(`[FraudShield API] Backend unavailable at ${API_BASE}. Falling back to demo engine.`);
      isDemoMode = true;
      updateHealthPill(false);
      return api.mockRoute(method, path, body);
    }
  },

  mockRoute(method, path, body) {
    if (path.startsWith('/api/health')) {
      return Promise.resolve({ status: 'demo_mode', database: 'in_memory', model_loaded: true, model_version: '1.0.0-demo' });
    }
    if (path.startsWith('/api/dashboard/stats')) {
      return Promise.resolve(demoStore.stats);
    }
    if (path.startsWith('/api/dashboard/recent-suspicious')) {
      return Promise.resolve(demoStore.recentSuspicious);
    }
    if (path.startsWith('/api/dashboard/trend')) {
      const days = 7;
      const data = [];
      for (let i = days - 1; i >= 0; i--) {
        const d = new Date(Date.now() - i * 86400000);
        const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        data.push({
          date: dateStr,
          total: Math.floor(12000 + Math.random() * 3000),
          flagged: Math.floor(90 + Math.random() * 40)
        });
      }
      return Promise.resolve(data);
    }
    if (path.startsWith('/api/transactions')) {
      return Promise.resolve({
        total: demoStore.recentSuspicious.length,
        items: demoStore.recentSuspicious
      });
    }
    if (path.startsWith('/api/model/metrics')) {
      return Promise.resolve(demoStore.metrics);
    }
    if (path.startsWith('/api/investigations') && method === 'GET') {
      return Promise.resolve(demoStore.investigations);
    }
    if (path.startsWith('/api/investigations') && method === 'PATCH') {
      const parts = path.split('/');
      const id = parts[parts.length - 1];
      const inv = demoStore.investigations.find(item => item.id === id);
      if (inv && body) {
        Object.assign(inv, body, { updated_at: new Date().toISOString() });
        return Promise.resolve(inv);
      }
      return Promise.resolve({ success: true });
    }
    if (path.startsWith('/api/predict/batch')) {
      const txns = body?.transactions || [];
      const results = txns.map(tx => api.simulatePrediction(tx));
      return Promise.resolve({ total_processed: results.length, results });
    }
    if (path.startsWith('/api/predict')) {
      return Promise.resolve(api.simulatePrediction(body));
    }

    return Promise.resolve({});
  },

  simulatePrediction(data) {
    const amt = parseFloat(data.amount || 0);
    const type = (data.type || data.transaction_type || '').toUpperCase();
    const obBefore = parseFloat(data.origin_balance_before || data.oldbalanceOrg || 0);
    const obAfter = parseFloat(data.origin_balance_after || data.newbalanceOrig || 0);
    const dbBefore = parseFloat(data.dest_balance_before || data.oldbalanceDest || 0);
    const dbAfter = parseFloat(data.dest_balance_after || data.newbalanceDest || 0);

    let score = 0.02;

    // Fraud heuristics mirroring PaySim XGBoost learned patterns
    if (type === 'TRANSFER' || type === 'CASH_OUT') {
      score += 0.25;
      if (amt > 100000) score += 0.35;
      if (amt > 250000) score += 0.25;
      if (obAfter === 0 && obBefore > 0) score += 0.20;
      if (dbBefore === 0 && dbAfter === 0) score += 0.15;
      if (Math.abs(amt - obBefore) < 1.0) score += 0.15;
    } else {
      score = Math.min(0.08, amt / 1000000);
    }

    score = Math.max(0.001, Math.min(0.9998, score));
    const isFraud = score >= 0.5;
    const risk = score >= 0.7 ? 'High' : (score >= 0.3 ? 'Medium' : 'Low');

    const shapFeatures = [
      { feature: 'origin_balance_after', importance: (obAfter === 0 && obBefore > 0) ? 2.88 : -0.45 },
      { feature: 'balance_diff_dest', importance: (type === 'TRANSFER' && amt > 100000) ? 2.79 : 0.12 },
      { feature: 'balance_diff_origin', importance: (Math.abs(amt - obBefore) < 1.0) ? 2.51 : 0.23 },
      { feature: 'amount', importance: amt > 100000 ? 2.34 : -0.89 },
      { feature: 'transaction_type', importance: (type === 'TRANSFER' || type === 'CASH_OUT') ? 0.72 : -1.20 },
      { feature: 'amount_to_origin_ratio', importance: obBefore > 0 ? (amt / obBefore > 0.9 ? 0.34 : -0.15) : 0.05 }
    ];

    const txnId = 'TXN-' + Math.floor(100000 + Math.random() * 900000);

    // Track in demo stats if flagged
    if (isFraud) {
      demoStore.recentSuspicious.unshift({
        id: txnId,
        type: type,
        amount: amt,
        risk: risk,
        score: score,
        time: "Just now",
        origin: data.origin_account || "C" + Math.floor(100000000 + Math.random() * 900000000),
        dest: data.dest_account || "C" + Math.floor(100000000 + Math.random() * 900000000)
      });
      if (demoStore.recentSuspicious.length > 20) demoStore.recentSuspicious.pop();
    }

    return {
      transaction_id: txnId,
      fraud_probability: score,
      is_fraud: isFraud,
      risk_category: risk,
      threshold_applied: 0.1,
      shap_features: shapFeatures,
      analysis_timestamp: new Date().toISOString()
    };
  },

  get:    (path)        => api.request('GET', path),
  post:   (path, body)  => api.request('POST', path, body),
  patch:  (path, body)  => api.request('PATCH', path, body),

  // Endpoints
  health:          ()      => api.get('/api/health'),
  dashboardStats:  ()      => api.get('/api/dashboard/stats'),
  recentSuspicious:(lim=10)=> api.get(`/api/dashboard/recent-suspicious?limit=${lim}`),
  trendData:       (d=7)   => api.get(`/api/dashboard/trend?days=${d}`),
  transactions:    (s=0,l=50,risk='') => api.get(`/api/transactions?skip=${s}&limit=${l}${risk?`&risk_category=${risk}`:''}`),
  transaction:     (id)    => api.get(`/api/transactions/${id}`),
  predict:         (data)  => api.post('/api/predict', data),
  predictBatch:    (txns)  => api.post('/api/predict/batch', { transactions: txns }),
  modelMetrics:    ()      => api.get('/api/model/metrics'),
  explanation:     (id)    => api.get(`/api/explanations/${id}`),
  investigations:  (p={})  => {
    const q = new URLSearchParams(p).toString();
    return api.get(`/api/investigations${q ? '?' + q : ''}`);
  },
  updateInvestigation: (id, data) => api.patch(`/api/investigations/${id}`, data),
};

window.api = api;
