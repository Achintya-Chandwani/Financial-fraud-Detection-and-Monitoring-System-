/**
 * FraudShield AI — API Client
 * Centralised fetch wrapper for all backend calls.
 */

const API_BASE = 'http://localhost:8000';

const api = {
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const msg = typeof err.detail === 'string'
        ? err.detail
        : err.detail?.message || JSON.stringify(err.detail);
      throw new Error(msg);
    }
    return res.json();
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
