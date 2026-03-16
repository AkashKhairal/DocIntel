import React, { useState, useEffect } from 'react';
import { fetchDocuments, triggerSync } from '../services/api';
import {
    FileText,
    RefreshCw,
    Clock,
    HardDrive,
    Trash2,
    Eye,
    CheckCircle2,
    XCircle,
    Search
} from 'lucide-react';

export default function DocumentHub() {
    const [documents, setDocuments] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    const loadData = async () => {
        try {
            setIsLoading(true);
            const data = await fetchDocuments();
            setDocuments(data.documents || []);
        } catch (err) {
            console.error("Failed to load documents", err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const filteredDocs = documents.filter(doc =>
        doc.file_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatBytes = (bytes) => {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    return (
        <div className="flex flex-col h-full bg-surface-900 overflow-hidden relative">
            {/* Header */}
            <header className="px-6 py-4 border-b border-surface-800/60 bg-surface-900/90 backdrop-blur-sm z-10 flexItems-center justify-between shrink-0">
                <div>
                    <h2 className="text-xl font-semibold text-surface-50 flex items-center gap-2">
                        <HardDrive className="text-accent-400" size={24} />
                        Document Knowledge Base
                    </h2>
                    <p className="text-sm text-surface-400 mt-1">
                        Manage your indexed files. Files sync automatically from Google Drive.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500" size={16} />
                        <input
                            type="text"
                            placeholder="Search files..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-surface-800 border border-surface-700/50 rounded-lg pl-9 pr-4 py-2 text-sm text-surface-200 placeholder-surface-500 w-64 focus:outline-none focus:border-accent-500/50 transition-colors"
                        />
                    </div>
                    <button
                        onClick={loadData}
                        disabled={isLoading}
                        className="p-2.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-surface-300 transition-colors border border-surface-700/50"
                        title="Refresh list"
                    >
                        <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
                    </button>
                    <button
                        onClick={async () => {
                            await triggerSync();
                            loadData();
                        }}
                        className="px-4 py-2 rounded-lg bg-accent-500 hover:bg-accent-600 text-white font-medium text-sm transition-colors flex items-center gap-2"
                    >
                        Force Full Sync
                    </button>
                </div>
            </header>

            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
                <div className="bg-surface-800/30 border border-surface-800/60 rounded-xl overflow-hidden shadow-sm">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-surface-800/80 text-xs uppercase tracking-wider text-surface-400 font-medium">
                                <th className="px-6 py-4">File Name</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4">Size</th>
                                <th className="px-6 py-4">Indexed Date</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-800/50">
                            {isLoading ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-12 text-center text-surface-500">
                                        <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-accent-500" />
                                        Loading documents...
                                    </td>
                                </tr>
                            ) : filteredDocs.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-12 text-center text-surface-500">
                                        <div className="bg-surface-800/50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                                            <FileText size={24} className="text-surface-400" />
                                        </div>
                                        <p className="text-sm">No documents found.</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredDocs.map((doc, idx) => (
                                    <tr key={idx} className="hover:bg-surface-800/40 transition-colors group">
                                        <td className="px-6 py-4 flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-lg bg-surface-800 flex items-center justify-center flex-shrink-0 text-surface-400">
                                                <FileText size={18} />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-medium text-surface-200 truncate pr-4">
                                                    {doc.file_name}
                                                </p>
                                                <a
                                                    href={doc.drive_link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-xs text-accent-400 hover:text-accent-300 flex items-center gap-1 mt-0.5"
                                                >
                                                    View in Drive
                                                </a>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 w-max text-xs font-medium">
                                                <CheckCircle2 size={12} />
                                                Indexed
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-surface-400 font-mono">
                                            {formatBytes(doc.file_size)}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-surface-400">
                                            <div className="flex items-center gap-1.5">
                                                <Clock size={14} className="text-surface-500" />
                                                {doc.modified_time
                                                    ? new Date(doc.modified_time).toLocaleDateString()
                                                    : 'Unknown'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <a
                                                    href={doc.drive_link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="p-2 rounded hover:bg-surface-700 text-surface-400 hover:text-surface-200 transition-colors"
                                                    title="View Document"
                                                >
                                                    <Eye size={16} />
                                                </a>
                                                <button
                                                    className="p-2 rounded hover:bg-red-500/20 text-surface-400 hover:text-red-400 transition-colors"
                                                    title="Delete Index"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
