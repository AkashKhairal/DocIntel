import React, { useState, useEffect, useRef } from 'react';
import {
    fetchSettings,
    updateSettings,
    uploadCredentials,
    setupWebhook,
    triggerSync,
    connectGoogleDrive,
    getGoogleIntegration,
} from '../services/api';
import FolderPicker from './FolderPicker';
import {
    X,
    Key,
    Upload,
    Globe,
    CheckCircle2,
    AlertCircle,
    Loader2,
    RefreshCw,
    Webhook,
    FolderOpen,
} from 'lucide-react';

export default function SettingsModal({ isOpen, onClose }) {
    const [settings, setSettings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    // Form state
    const [cohereKey, setCohereKey] = useState('');
    const [webhookUrl, setWebhookUrl] = useState('');
    const [folderId, setFolderId] = useState('');
    const [integrationStatus, setIntegrationStatus] = useState(null);
    const [isFolderPickerOpen, setIsFolderPickerOpen] = useState(false);

    const fileInputRef = useRef(null);

    useEffect(() => {
        if (isOpen) {
            loadSettings();
        }
    }, [isOpen]);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const data = await fetchSettings();
            const integration = await getGoogleIntegration();

            setSettings(data);
            setWebhookUrl(data.webhook_url || '');
            setFolderId(data.google_drive_folder_id || '');
            setIntegrationStatus(integration);
        } catch (err) {
            showMessage('error', 'Failed to load settings');
        } finally {
            setLoading(false);
        }
    };

    const showMessage = (type, text) => {
        setMessage({ type, text });
        setTimeout(() => setMessage(null), 5000);
    };

    const handleSaveCohereKey = async () => {
        if (!cohereKey.trim()) return;
        try {
            setSaving(true);
            await updateSettings({ cohere_api_key: cohereKey });
            setCohereKey('');
            showMessage('success', 'Cohere API key saved successfully');
            loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleSaveWebhookUrl = async () => {
        if (!webhookUrl.trim()) return;
        try {
            setSaving(true);
            await updateSettings({ webhook_url: webhookUrl });
            showMessage('success', 'Webhook URL saved successfully');
            loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleSaveFolderId = async () => {
        if (!folderId.trim()) return;
        try {
            setSaving(true);
            await updateSettings({ google_drive_folder_id: folderId });
            showMessage('success', 'Drive folder ID saved successfully');
            loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleUploadCredentials = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            setSaving(true);
            const result = await uploadCredentials(file);
            showMessage(
                'success',
                `Credentials uploaded: ${result.credential_type} (${result.project_id})`
            );
            loadSettings();
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleSetupWebhook = async () => {
        try {
            setSaving(true);
            const result = await setupWebhook();
            showMessage('success', `Watch channel created: ${result.channel_id}`);
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleTriggerSync = async () => {
        try {
            setSaving(true);
            await triggerSync();
            showMessage('success', 'Full sync started! Files are being processed in the background.');
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleConnectGoogleDrive = async () => {
        try {
            setSaving(true);
            const data = await connectGoogleDrive();
            if (data.url) {
                // Use same tab redirect for production OAuth reliability
                window.location.href = data.url;
            }
        } catch (err) {
            showMessage('error', err.message);
        } finally {
            setSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto mx-4 rounded-2xl bg-surface-850 border border-surface-700/50 shadow-2xl animate-slide-up">
                {/* DEBUG BANNER */}
                <div className="bg-orange-500 text-white text-[10px] font-bold py-1 px-4 text-center uppercase tracking-widest">
                    Debug Mode: {integrationStatus ? "GOOG_CONNECTED" : "GOOG_DISCONNECTED"} | v1.2
                </div>
                {/* Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 bg-surface-850/95 backdrop-blur-sm border-b border-surface-800/50 rounded-t-2xl">
                    <h2 className="text-lg font-semibold text-surface-100 flex items-center gap-2">
                        Settings
                        <span className="text-[10px] bg-surface-800 px-1.5 py-0.5 rounded text-surface-500 font-mono">v1.1</span>
                    </h2>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 rounded-lg hover:bg-surface-800 flex items-center justify-center text-surface-400 hover:text-surface-200 transition-colors"
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Message Toast */}
                {message && (
                    <div
                        className={`mx-6 mt-4 px-4 py-3 rounded-xl flex items-center gap-2.5 text-sm animate-fade-in ${message.type === 'success'
                            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                            : 'bg-red-500/10 border border-red-500/20 text-red-400'
                            }`}
                    >
                        {message.type === 'success' ? (
                            <CheckCircle2 size={16} />
                        ) : (
                            <AlertCircle size={16} />
                        )}
                        {message.text}
                    </div>
                )}

                {loading ? (
                    <div className="flex items-center justify-center py-16">
                        <Loader2 size={24} className="text-accent-400 animate-spin" />
                    </div>
                ) : (
                    <div className="px-6 py-5 space-y-6">
                        {/* Google Credentials */}
                        <SettingsSection
                            icon={<Upload size={16} />}
                            title="Google Service Account"
                            description="Upload your Google Cloud service account JSON credentials file"
                        >
                            <div className="flex items-center gap-3">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".json"
                                    onChange={handleUploadCredentials}
                                    className="hidden"
                                    id="credentials-upload"
                                />
                                <label
                                    htmlFor="credentials-upload"
                                    className="cursor-pointer px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 border border-surface-700/50 text-sm text-surface-300 hover:text-surface-100 transition-all"
                                >
                                    Choose File
                                </label>
                                <StatusBadge
                                    set={settings?.google_credentials_set}
                                    label="Credentials"
                                />
                            </div>
                        </SettingsSection>

                        {/* Google Drive OAuth */}
                        <SettingsSection
                            icon={<Webhook size={16} />}
                            title="Google Drive (OAuth)"
                            description="Connect your account using Google OAuth (recommended for SaaS)">
                            <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-surface-400">
                                        {integrationStatus
                                            ? `Connected (${integrationStatus.scope || 'scope set'})`
                                            : 'Not connected'}
                                    </span>
                                    <button
                                        onClick={handleConnectGoogleDrive}
                                        disabled={saving}
                                        className="px-3 py-1.5 rounded-lg bg-accent-500 hover:bg-accent-600 text-xs text-white"
                                    >
                                        Connect
                                    </button>
                                </div>
                                {integrationStatus ? (
                                    <button
                                        onClick={() => setIsFolderPickerOpen(true)}
                                        className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-accent-500/10 hover:bg-accent-500/20 border border-accent-500/20 text-sm text-accent-400 hover:text-accent-300 transition-all font-semibold"
                                    >
                                        <FolderOpen size={16} />
                                        Select Sync Folders
                                        {integrationStatus.monitored_folders?.length > 0 && (
                                            <span className="ml-1 px-1.5 py-0.5 rounded-md bg-accent-500/20 text-accent-400 text-[10px] font-bold">
                                                {integrationStatus.monitored_folders.length}
                                            </span>
                                        )}
                                    </button>
                                ) : (
                                    <p className="text-[10px] text-surface-600 mt-1 italic">
                                        Note: Folder selection becomes available after connecting Drive.
                                    </p>
                                )}
                                <small className="text-xs text-surface-500">
                                    {integrationStatus
                                        ? "Choose exactly which folders you want to use for AI intelligence."
                                        : "After authorization completes, return to this settings modal and re-open to refresh status."
                                    }
                                </small>
                            </div>
                        </SettingsSection>

                        {/* Cohere API Key */}
                        <SettingsSection
                            icon={<Key size={16} />}
                            title="Cohere API Key"
                            description="Used for High-Accuracy Cross-Encoder Re-ranking"
                        >
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    value={cohereKey}
                                    onChange={(e) => setCohereKey(e.target.value)}
                                    placeholder={
                                        settings?.has_cohere_key
                                            ? 'Current Key is Set'
                                            : 'Your Cohere API Key'
                                    }
                                    className="flex-1 bg-surface-800 border border-surface-700/50 rounded-lg px-3 py-2 text-sm text-surface-200 placeholder-surface-500 input-focus outline-none"
                                    id="cohere-key-input"
                                />
                                <button
                                    onClick={handleSaveCohereKey}
                                    disabled={saving || !cohereKey.trim()}
                                    className="px-4 py-2 rounded-lg bg-accent-500 hover:bg-accent-600 disabled:bg-surface-700 disabled:cursor-not-allowed text-sm text-white font-medium transition-colors"
                                >
                                    Save
                                </button>
                            </div>
                        </SettingsSection>

                        {/* Webhook URL */}
                        <SettingsSection
                            icon={<Globe size={16} />}
                            title="Webhook Endpoint URL"
                            description="Public HTTPS URL for Google Drive push notifications (e.g. your ngrok URL)"
                        >
                            <div className="flex gap-2">
                                <input
                                    type="url"
                                    value={webhookUrl}
                                    onChange={(e) => setWebhookUrl(e.target.value)}
                                    placeholder="https://your-domain.ngrok-free.app"
                                    className="flex-1 bg-surface-800 border border-surface-700/50 rounded-lg px-3 py-2 text-sm text-surface-200 placeholder-surface-500 input-focus outline-none"
                                    id="webhook-url-input"
                                />
                                <button
                                    onClick={handleSaveWebhookUrl}
                                    disabled={saving || !webhookUrl.trim()}
                                    className="px-4 py-2 rounded-lg bg-accent-500 hover:bg-accent-600 disabled:bg-surface-700 disabled:cursor-not-allowed text-sm text-white font-medium transition-colors"
                                >
                                    Save
                                </button>
                            </div>
                        </SettingsSection>


                        {/* Actions */}
                        <div className="border-t border-surface-800/50 pt-5">
                            <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">
                                Actions
                            </h3>
                            <div className="flex flex-wrap gap-3">
                                <button
                                    onClick={handleSetupWebhook}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-surface-700/50 text-sm text-surface-300 hover:text-surface-100 transition-all disabled:opacity-50"
                                >
                                    <Webhook size={15} />
                                    Setup Watch Channel
                                </button>
                                <button
                                    onClick={handleTriggerSync}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-surface-700/50 text-sm text-surface-300 hover:text-surface-100 transition-all disabled:opacity-50"
                                >
                                    <RefreshCw size={15} />
                                    Full Sync Now
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Folder Picker Modal Overlay */}
            {isFolderPickerOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    <div
                        className="absolute inset-0 bg-black/80 backdrop-blur-md"
                        onClick={() => setIsFolderPickerOpen(false)}
                    />
                    <div className="relative w-full max-w-2xl">
                        <FolderPicker
                            onClose={() => setIsFolderPickerOpen(false)}
                            onSave={() => {
                                loadSettings();
                                handleTriggerSync(); // Automatically sync after changing folders
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

function SettingsSection({ icon, title, description, children }) {
    return (
        <div>
            <div className="flex items-center gap-2 mb-1.5">
                <span className="text-accent-400">{icon}</span>
                <h3 className="text-sm font-medium text-surface-200">{title}</h3>
            </div>
            <p className="text-xs text-surface-500 mb-3">{description}</p>
            {children}
        </div>
    );
}

function StatusBadge({ set, label }) {
    return (
        <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${set
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-surface-800/80 text-surface-500 border border-surface-700/30'
                }`}
        >
            {set ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
            {set ? `${label} Set` : `${label} Missing`}
        </span>
    );
}
