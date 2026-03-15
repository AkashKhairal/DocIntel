/**
 * API service for communicating with the DocIntel backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Send a chat question and stream the response.
 * @param {string} question
 * @param {(chunk: {type: string, content: any}) => void} onChunk
 * @param {string} apiKey - optional API key
 */
export async function sendChatMessage(question, onChunk, apiKey = '') {
    const headers = {
        'Content-Type': 'application/json',
    };
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
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
}

/**
 * Fetch sync status.
 */
export async function fetchSyncStatus() {
    const res = await fetch(`${API_BASE}/sync-status`);
    if (!res.ok) throw new Error('Failed to fetch sync status');
    return res.json();
}

/**
 * Fetch current settings.
 */
export async function fetchSettings() {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
}

/**
 * Update settings.
 */
export async function updateSettings(data) {
    const res = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to update settings' }));
        throw new Error(error.detail);
    }
    return res.json();
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
    const res = await fetch(`${API_BASE}/settings/setup-webhook`, {
        method: 'POST',
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to setup webhook' }));
        throw new Error(error.detail);
    }
    return res.json();
}

/**
 * Trigger a full sync of Drive files.
 */
export async function triggerSync() {
    const res = await fetch(`${API_BASE}/settings/trigger-sync`, {
        method: 'POST',
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to trigger sync' }));
        throw new Error(error.detail);
    }
    return res.json();
}
