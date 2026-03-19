import React, { useState, useEffect } from 'react';
import {
    fetchSettings,
    updateSettings,
    uploadCredentials,
    setupWebhook,
    triggerSync,
    connectGoogleDrive,
    getGoogleIntegration,
} from '../services/api';
import { X, Key, Upload, Globe, CheckCircle2, AlertCircle, Webhook, FolderOpen, RefreshCw } from 'lucide-react';

const tabNames = ['General', 'Integrations', 'Security', 'Audit'];

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('General');
    const [settings, setSettings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [integrationStatus, setIntegrationStatus] = useState(null);

    const [formState, setFormState] = useState({
        cohereKey: '',
        webhookUrl: '',
        folderId: '',
    });

    useEffect(() => {
        loadSettings();
    }, []);

    const showMessage = (type, text) => {
        setMessage({ type, text });
        setTimeout(() => setMessage(null), 5000);
    };

    const loadSettings = async () => {
        setLoading(true);
        try {
            const s = await fetchSettings();
            const integration = await getGoogleIntegration();
            setSettings(s);
            setIntegrationStatus(integration);
            setFormState({
                cohereKey: '',
                webhookUrl: s.webhook_url || '',
                folderId: s.google_drive_folder_id || '',
            });
        } catch (err) {
            showMessage('error', err.message || 'Failed to load settings');
        } finally {
            setLoading(false);
        }
    };

    const updateField = (key, value) => setFormState((prev) => ({ ...prev, [key]: value }));

    const handleSaveSetting = async (key, value) => {
        try {
            setSaving(true);
            await updateSettings({ [key]: value });
            showMessage('success', `${key} updated`);
            await loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        try {
            setSaving(true);
            await uploadCredentials(file);
            showMessage('success', 'Google credentials uploaded');
            await loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleConnectGoogle = async () => {
        setSaving(true);
        try {
            const data = await connectGoogleDrive();
            window.location.href = data.url;
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleAction = async (action) => {
        setSaving(true);
        try {
            if (action === 'webhook') {
                const res = await setupWebhook();
                showMessage('success', `Webhook channel created: ${res.channel_id}`);
            } else if (action === 'fullsync') {
                await triggerSync();
                showMessage('success', 'Full sync started.');
            }
            await loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="p-6 h-full overflow-y-auto text-surface-100">
            <header className="mb-4 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Settings</h1>
                    <p className="text-sm text-surface-400">Configure platform, OAuth, secrets, and security.</p>
                </div>
            </header>

            <div className="flex gap-3">
                <aside className="w-72 bg-surface-800 rounded-2xl border border-surface-700 p-3">
                    {tabNames.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`w-full text-left px-4 py-2 rounded-lg mb-1 ${activeTab === tab ? 'bg-accent-500/20 text-accent-200' : 'hover:bg-surface-700 text-surface-300'}`}
                        >
                            {tab}
                        </button>
                    ))}
                </aside>

                <main className="flex-1 bg-surface-800 rounded-2xl border border-surface-700 p-5">
                    {message && (
                        <div className={`mb-4 p-3 rounded-lg ${message.type === 'success' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-red-500/10 text-red-300'}`}>
                            {message.text}
                        </div>
                    )}

                    {loading ? (
                        <p>Loading settings...</p>
                    ) : activeTab === 'General' ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="p-4 bg-surface-900 rounded-xl border border-surface-700">
                                    <h3 className="text-sm font-semibold text-surface-100">Webhook URL</h3>
                                    <input
                                        type="url"
                                        value={formState.webhookUrl}
                                        onChange={(e) => updateField('webhookUrl', e.target.value)}
                                        className="w-full mt-2 p-2 rounded-lg border border-surface-700 bg-surface-900 text-surface-100"
                                        placeholder="https://example.ngrok.app"
                                    />
                                    <button onClick={() => handleSaveSetting('webhook_url', formState.webhookUrl)} disabled={saving} className="mt-2 px-3 py-1.5 rounded-lg bg-accent-500 hover:bg-accent-600 text-sm">
                                        Save
                                    </button>
                                </div>

                                <div className="p-4 bg-surface-900 rounded-xl border border-surface-700">
                                    <h3 className="text-sm font-semibold text-surface-100">Drive Folder ID</h3>
                                    <input
                                        type="text"
                                        value={formState.folderId}
                                        onChange={(e) => updateField('folderId', e.target.value)}
                                        className="w-full mt-2 p-2 rounded-lg border border-surface-700 bg-surface-900 text-surface-100"
                                        placeholder="1a2b3c..."
                                    />
                                    <button onClick={() => handleSaveSetting('google_drive_folder_id', formState.folderId)} disabled={saving} className="mt-2 px-3 py-1.5 rounded-lg bg-accent-500 hover:bg-accent-600 text-sm">
                                        Save
                                    </button>
                                </div>
                            </div>

                            <div className="mt-4 flex gap-2 items-center">
                                <button onClick={() => handleAction('webhook')} disabled={saving} className="px-3 py-2 rounded-lg border border-surface-700 hover:bg-surface-700 text-surface-200">
                                    <Webhook size={14} className="inline mr-2" /> Setup Watch Channel
                                </button>
                                <button onClick={() => handleAction('fullsync')} disabled={saving} className="px-3 py-2 rounded-lg border border-surface-700 hover:bg-surface-700 text-surface-200">
                                    <RefreshCw size={14} className="inline mr-2" /> Full Sync
                                </button>
                            </div>
                        </div>
                    ) : activeTab === 'Integrations' ? (
                        <div className="space-y-4">
                            <div className="p-4 bg-surface-900 rounded-xl border border-surface-700">
                                <h3 className="text-sm font-semibold text-surface-100">Google OAuth</h3>
                                <p className="text-xs text-surface-400">Current status: {integrationStatus ? 'Connected' : 'Not connected'}</p>
                                <p className="text-xs text-surface-400">Scope: {integrationStatus?.scope || 'n/a'}</p>
                                <button onClick={handleConnectGoogle} disabled={saving} className="mt-2 px-3 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white">
                                    {integrationStatus ? 'Reconnect' : 'Connect'} Google Drive
                                </button>
                            </div>

                            <div className="p-4 bg-surface-900 rounded-xl border border-surface-700">
                                <p className="text-sm text-surface-100">Service account JSON upload is deprecated. Use OAuth connect flow above.</p>
                            </div>
                        </div>
                    ) : activeTab === 'Security' ? (
                        <div className="p-4 bg-surface-900 rounded-xl border border-surface-700">
                            <h3 className="text-sm font-semibold text-surface-100">API Keys</h3>
                            <p className="text-xs text-surface-400 mt-3">
                                OpenAI and Gemini API keys are now configured via environment variables only (e.g. GEMINI_API_KEY). Manual entry in app settings is disabled.
                            </p>
                            <p className="text-xs text-surface-400 mt-2">
                                Cohere re-ranking is still configurable via settings here.
                            </p>
                        </div>
                    ) : (
                        <div className="p-4 bg-surface-900 rounded-xl border border-surface-700">
                            <h3 className="text-sm font-semibold text-surface-100">Audit Logs</h3>
                            <p className="text-xs text-surface-400">No audit log storage currently available in this build.</p>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
