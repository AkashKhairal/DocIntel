const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
    const token = window.localStorage.getItem('docintel_admin_token');
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
};

const handleResponse = async (res) => {
    if (!res.ok) {
        const text = await res.text();
        try {
            const json = JSON.parse(text);
            throw new Error(json.detail || json.message || text);
        } catch (err) {
            throw new Error(text || err.message);
        }
    }
    return res.json();
};

export const login = async (email, password) => {
    const body = new URLSearchParams();
    body.append('username', email);
    body.append('password', password);
    body.append('grant_type', 'password');
    body.append('scope', '');

    return fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
    }).then(handleResponse);
};

export const fetchCurrentUser = () =>
    fetch(`${API_BASE}/auth/me`, { method: 'GET', headers: getAuthHeaders() }).then(handleResponse);

export const fetchAdminStats = () =>
    fetch(`${API_BASE}/admin/stats`, { method: 'GET', headers: getAuthHeaders() }).then(handleResponse);

export const fetchTenants = () =>
    fetch(`${API_BASE}/admin/tenants`, { method: 'GET', headers: getAuthHeaders() }).then(handleResponse);

export const fetchTenant = (id) =>
    fetch(`${API_BASE}/admin/tenants/${id}`, { method: 'GET', headers: getAuthHeaders() }).then(handleResponse);

export const createTenant = (payload) =>
    fetch(`${API_BASE}/admin/tenants`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
    }).then(handleResponse);

export const updateTenant = (id, payload) =>
    fetch(`${API_BASE}/admin/tenants/${id}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
    }).then(handleResponse);
