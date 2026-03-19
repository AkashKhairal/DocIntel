/**
 * API service for communicating with the DocIntel backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

const ACCESS_TOKEN_KEY = 'docintel_access_token';

export function setAccessToken(token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function clearAccessToken() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
}

async function apiFetch(path, options = {}) {
    const token = getAccessToken();
    const headers = options.headers || {};
    headers['Content-Type'] = 'application/json';
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const result = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
    });

    if (result.status === 401) {
        clearAccessToken();
        throw new Error('Unauthorized. Please login.');
    }

    if (!result.ok) {
        const text = await result.text();
        try {
            const json = JSON.parse(text);
            throw new Error(json.detail || json.message || 'Request failed');
        } catch {
            throw new Error(text || `HTTP ${result.status}`);
        }
    }

    if (result.status === 204) {
        return null;
    }

    // may be non-json but safe attempt
    const contentType = result.headers.get('Content-Type') || '';
    if (contentType.includes('application/json')) {
        return result.json();
    }
    return result.text();
}

export async function login(username, password) {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);

    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setAccessToken(data.access_token);
    return data;
}

export async function signup(email, password) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Sign up failed' }));
        throw new Error(err.detail || 'Sign up failed');
    }
    const data = await res.json();
    setAccessToken(data.access_token);
    return data;
}

export async function me() {
    return apiFetch('/auth/me');
}

/**
 * Send a chat question and stream the response.
 * @param {string} question
 * @param {(chunk: {type: string, content: any}) => void} onChunk
 * @param {string} apiKey - optional API key
 */
export async function sendChatMessage(question, onChunk, apiKey = '') {
    const token = getAccessToken();
    const headers = {
        'Content-Type': 'application/json',
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (apiKey) {
        headers['X-API-Key'] = apiKey;
    }

    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ question }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.trim()) {
                try {
                    const chunk = JSON.parse(line);
                    onChunk(chunk);
                } catch {
                    // skip malformed lines
                }
            }
        }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
        try {
            const chunk = JSON.parse(buffer);
            onChunk(chunk);
        } catch {
            // skip
        }
    }
}

/**
 * Fetch list of indexed documents.
 */
export async function fetchDocuments() {
    return apiFetch('/documents');
}

/**
 * Fetch sync status.
 */
export async function fetchSyncStatus() {
    return apiFetch('/sync-status');
}

/**
 * Fetch current settings.
 */
export async function fetchSettings() {
    return apiFetch('/settings');
}

/**
 * Update settings.
 */
export async function updateSettings(data) {
    return apiFetch('/settings', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

/**
 * Upload Google credentials file.
 */
export async function uploadCredentials(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/settings/upload-credentials`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to upload credentials' }));
        throw new Error(error.detail);
    }

    return res.json();
}

/**
 * Set up the Google Drive webhook.
 */
export async function setupWebhook() {
    return apiFetch('/settings/setup-webhook', {
        method: 'POST',
    });
}

/**
 * Trigger a full sync of Drive files.
 */
export async function triggerSync() {
    return apiFetch('/settings/trigger-sync', {
        method: 'POST',
    });
}

export async function deleteDocument(fileId) {
    return apiFetch(`/documents/${encodeURIComponent(fileId)}`, {
        method: 'DELETE',
    });
}

export async function connectGoogleDrive() {
    return apiFetch('/integrations/google/connect');
}

export async function getGoogleIntegration() {
    try {
        return await apiFetch('/integrations/google/status');
    } catch (err) {
        return null;
    }
}

/**
 * Fetch folders from Google Drive for a parent ID.
 */
export async function fetchGoogleFolders(parentId = 'root') {
    return apiFetch(`/integrations/google/folders?parent_id=${parentId}`);
}

/**
 * Update the list of monitored folders.
 */
export async function updateMonitoredFolders(folderIds) {
    return apiFetch('/integrations/google/monitored-folders', {
        method: 'PATCH',
        body: JSON.stringify({ folder_ids: folderIds }),
    });
}

export async function fetchUsers() {
    return apiFetch('/users');
}

export async function createUser(email, password, role = 'viewer') {
    return apiFetch('/users', {
        method: 'POST',
        body: JSON.stringify({ email, password, role }),
    });
}
