import React, { useState, useEffect } from 'react';
import { fetchSyncStatus, fetchDocuments } from '../services/api';
import {
    Database,
    FileText,
    Clock,
    Settings,
    RefreshCw,
    Cloud,
    CheckCircle2,
    AlertCircle,
    Zap,
    MessageSquare,
    Library
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar({ onOpenSettings }) {
    const [syncStatus, setSyncStatus] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const loadData = async () => {
        try {
            setIsRefreshing(true);
            const [status, docs] = await Promise.all([
                fetchSyncStatus().catch(() => null),
                fetchDocuments().catch(() => ({ documents: [] })),
            ]);
            if (status) setSyncStatus(status);
            setDocuments(docs.documents || []);
        } finally {
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const statusColor =
        syncStatus?.vector_db_status === 'green'
            ? 'text-emerald-400'
            : syncStatus?.vector_db_status === 'yellow'
                ? 'text-amber-400'
                : 'text-surface-500';

    return (
        <div className="w-72 h-full flex flex-col bg-surface-900/80 border-r border-surface-800/60">
            {/* Logo */}
            <div className="px-5 py-5 border-b border-surface-800/50">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-500 to-purple-600 flex items-center justify-center shadow-lg shadow-accent-500/20">
                        <Zap size={18} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-base font-semibold text-surface-100">DocIntel</h1>
                        <p className="text-[10px] text-surface-500 uppercase tracking-widest">
                            Document AI
                        </p>
                    </div>
                </div>
            </div>

            {/* Main Navigation */}
            <div className="px-3 py-4 space-y-1 border-b border-surface-800/50">
                <NavLink
                    to="/chat"
                    className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-all ${isActive
                            ? 'bg-accent-500/10 text-accent-400'
                            : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60'
                        }`
                    }
                >
                    <MessageSquare size={16} />
                    <span className="text-sm">Chat</span>
                </NavLink>
                <NavLink
                    to="/documents"
                    className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-all ${isActive
                            ? 'bg-accent-500/10 text-accent-400'
                            : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60'
                        }`
                    }
                >
                    <Library size={16} />
                    <span className="text-sm">Document Hub</span>
                </NavLink>
            </div>

            {/* Sync Status */}
            <div className="px-4 py-4 border-b border-surface-800/50">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">
                        System Status
                    </h3>
                    <button
                        onClick={loadData}
                        disabled={isRefreshing}
                        className="text-surface-500 hover:text-surface-300 transition-colors"
                    >
                        <RefreshCw
                            size={13}
                            className={isRefreshing ? 'animate-spin' : ''}
                        />
                    </button>
                </div>

                <div className="space-y-2.5">
                    <StatusItem
                        icon={<Cloud size={14} />}
                        label="Vector DB"
                        value={syncStatus?.vector_db_status || '—'}
                        valueClass={statusColor}
                    />
                    <StatusItem
                        icon={<Database size={14} />}
                        label="Total Vectors"
                        value={syncStatus?.total_vectors?.toLocaleString() || '0'}
                    />
                    <StatusItem
                        icon={<FileText size={14} />}
                        label="Documents"
                        value={syncStatus?.total_documents || '0'}
                    />
                </div>
            </div>

            {/* Recent Documents */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
                <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">
                    Recent Documents
                </h3>

                {documents.length === 0 ? (
                    <div className="text-center py-8">
                        <FileText size={24} className="text-surface-600 mx-auto mb-2" />
                        <p className="text-xs text-surface-500">No documents indexed yet</p>
                        <p className="text-[10px] text-surface-600 mt-1">
                            Configure Google Drive in Settings
                        </p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {documents.slice(0, 20).map((doc, idx) => (
                            <NavLink
                                key={idx}
                                to="/documents"
                                className="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-surface-800/60 transition-all duration-150 group"
                            >
                                <FileText
                                    size={14}
                                    className="text-surface-500 group-hover:text-accent-400 transition-colors flex-shrink-0"
                                />
                                <div className="min-w-0 flex-1">
                                    <p className="text-xs text-surface-300 group-hover:text-surface-100 truncate transition-colors">
                                        {doc.file_name}
                                    </p>
                                    {doc.modified_time && (
                                        <p className="text-[10px] text-surface-600 flex items-center gap-1 mt-0.5">
                                            <Clock size={9} />
                                            {new Date(doc.modified_time).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>
                            </NavLink>
                        ))}
                    </div>
                )}
            </div>

            {/* Settings Button */}
            <div className="px-4 py-3 border-t border-surface-800/50">
                <button
                    id="settings-button"
                    onClick={onOpenSettings}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl hover:bg-surface-800/60 text-surface-400 hover:text-surface-200 transition-all duration-200"
                >
                    <Settings size={16} />
                    <span className="text-sm font-medium">Settings</span>
                </button>
            </div>
        </div>
    );
}

function StatusItem({ icon, label, value, valueClass = 'text-surface-200' }) {
    return (
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-surface-400">
                {icon}
                <span className="text-xs">{label}</span>
            </div>
            <span className={`text-xs font-medium ${valueClass}`}>{value}</span>
        </div>
    );
}
