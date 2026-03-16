import React, { useState, useEffect } from 'react';
import { fetchSyncStatus } from '../services/api';
import {
    CloudLightning,
    CheckCircle2,
    Loader2,
    ChevronUp,
    ChevronDown,
    X
} from 'lucide-react';

export default function ProgressWidget() {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isVisible, setIsVisible] = useState(true);
    const [status, setStatus] = useState(null);

    // In a real app with WebSockets, this would listen to live Celery events.
    // For now, we poll the /sync-status API endpoint to simulate progress observation.
    useEffect(() => {
        const loadStatus = async () => {
            try {
                const data = await fetchSyncStatus();
                setStatus(data);
            } catch (err) {
                // Silently drop errors to prevent widget spam
            }
        };

        loadStatus();
        const interval = setInterval(loadStatus, 15000);
        return () => clearInterval(interval);
    }, []);

    if (!isVisible || !status) return null;

    // Simulate "Activity" - if total vectors changes, we assume an upload is happening.
    const isSyncing = status.vector_db_status === 'yellow';

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
            {/* Expanded Details Panel */}
            <div
                className={`mb-3 bg-surface-800 border border-surface-700/60 shadow-xl shadow-black/40 rounded-xl overflow-hidden transition-all duration-300 transform origin-bottom-right ${isExpanded ? 'scale-100 opacity-100 pointer-events-auto w-72 h-80' : 'scale-95 opacity-0 pointer-events-none w-0 h-0'
                    }`}
            >
                <div className="p-4 border-b border-surface-700/50 flex items-center justify-between bg-surface-900">
                    <h4 className="text-sm font-semibold text-surface-200 flex items-center gap-2">
                        <CloudLightning size={16} className="text-accent-400" />
                        Sync Center
                    </h4>
                    <button
                        onClick={() => setIsExpanded(false)}
                        className="text-surface-500 hover:text-surface-300"
                    >
                        <X size={16} />
                    </button>
                </div>

                <div className="p-4">
                    <div className="mb-4">
                        <div className="flex justify-between text-xs mb-1.5">
                            <span className="text-surface-400">Total Vectors</span>
                            <span className="text-surface-200 font-mono text-[11px] bg-surface-900 px-1.5 rounded">
                                {status.total_vectors.toLocaleString()}
                            </span>
                        </div>
                        <div className="flex justify-between text-xs mb-1.5">
                            <span className="text-surface-400">Total Documents</span>
                            <span className="text-surface-200 font-mono text-[11px] bg-surface-900 px-1.5 rounded">
                                {status.total_documents}
                            </span>
                        </div>
                        <div className="flex justify-between text-xs">
                            <span className="text-surface-400">Last Synced</span>
                            <span className="text-surface-200 text-[10px]">
                                {new Date(status.last_checked).toLocaleTimeString()}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Minimized Pill Toggle */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className={`flex items-center gap-2.5 px-4 py-2.5 rounded-full shadow-lg border transition-all duration-300 ${isSyncing
                        ? 'bg-accent-500/10 border-accent-500/30 text-accent-400 hover:bg-accent-500/20'
                        : 'bg-surface-800 border-surface-700 text-surface-400 hover:text-surface-200 hover:bg-surface-700'
                    }`}
            >
                {isSyncing ? (
                    <Loader2 size={16} className="animate-spin" />
                ) : (
                    <CheckCircle2 size={16} className="text-emerald-500" />
                )}
                <span className="text-sm font-medium">
                    {isSyncing ? 'Syncing...' : 'All files synced'}
                </span>
                {isExpanded ? <ChevronDown size={14} className="ml-1 opacity-50" /> : <ChevronUp size={14} className="ml-1 opacity-50" />}
            </button>
        </div>
    );
}
