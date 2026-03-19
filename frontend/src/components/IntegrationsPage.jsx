import React, { useState, useEffect } from 'react';
import { getGoogleIntegration, connectGoogleDrive, setupWebhook, triggerSync } from '../services/api';
import { CheckCircle2, AlertCircle, Cloud, RefreshCw, Settings, Link } from 'lucide-react';

export default function IntegrationsPage() {
    const [integration, setIntegration] = useState(null);
    const [loading, setLoading] = useState(true);
    const [actionStatus, setActionStatus] = useState('');

    useEffect(() => {
        (async () => {
            await loadIntegration();
        })();
    }, []);

    const loadIntegration = async () => {
        setLoading(true);
        try {
            const data = await getGoogleIntegration();
            setIntegration(data);
        } catch {
            setIntegration(null);
        } finally {
            setLoading(false);
        }
    };

    const handleConnect = async () => {
        setActionStatus('Redirecting to Google OAuth...');
        try {
            const data = await connectGoogleDrive();
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (err) {
            setActionStatus(err.message);
        }
    };

    const handleSetupWebhook = async () => {
        setActionStatus('Setting up webhook...');
        try {
            const res = await setupWebhook();
            setActionStatus(`Webhook created: ${res.channel_id}`);
        } catch (err) {
            setActionStatus(err.message);
        }
        await loadIntegration();
    };

    const handleFullSync = async () => {
        setActionStatus('Starting full sync...');
        try {
            await triggerSync();
            setActionStatus('Full sync started.');
        } catch (err) {
            setActionStatus(err.message);
        }
    };

    return (
        <div className="mx-6 my-4 p-4 bg-surface-800 border border-surface-700 rounded-2xl shadow-sm">
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-3">
                <div>
                    <h2 className="text-xl font-semibold text-surface-100">Integrations</h2>
                    <p className="text-sm text-surface-400">Manage your Google Drive OAuth and webhook connection.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <button onClick={handleConnect} className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:opacity-90 transition">
                        <Link size={14} className="mr-2 inline" /> Connect Google Drive
                    </button>
                    <button onClick={handleSetupWebhook} className="px-4 py-2 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 hover:bg-surface-800 transition">
                        <Cloud size={14} className="mr-2 inline" /> Setup Webhook
                    </button>
                    <button onClick={handleFullSync} className="px-4 py-2 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 hover:bg-surface-800 transition">
                        <RefreshCw size={14} className="mr-2 inline" /> Full Sync
                    </button>
                </div>
            </div>

            <div className="mt-4">
                {loading ? (
                    <p className="text-sm text-surface-400">Loading integration status...</p>
                ) : integration ? (
                    <div className="space-y-2 text-surface-100">
                        <p className="text-sm">
                            <CheckCircle2 className="inline mr-2 text-emerald-400" /> Connected
                        </p>
                        <p className="text-xs text-surface-400">Scope: {integration.scope || 'n/a'}</p>
                        <p className="text-xs text-surface-400">Webhook channel: {integration.webhook_channel_id || 'Not set'}</p>
                        <p className="text-xs text-surface-400">Expires: {integration.expiry ? new Date(integration.expiry).toLocaleString() : 'not set'}</p>
                    </div>
                ) : (
                    <div className="text-surface-400">
                        <AlertCircle className="inline mr-2" /> No integration configured yet.
                    </div>
                )}
            </div>

            {actionStatus && <div className="mt-4 text-sm text-surface-300">{actionStatus}</div>}
        </div>
    );
}
