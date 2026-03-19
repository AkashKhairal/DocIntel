import React, { useState, useEffect } from 'react';
import { fetchGoogleFolders, updateMonitoredFolders } from '../services/api';
import { 
    Folder, 
    ChevronRight, 
    ChevronLeft, 
    Check, 
    Search, 
    Loader2, 
    AlertCircle,
    Info
} from 'lucide-react';

export default function FolderPicker({ onSave, onClose }) {
    const [currentFolders, setCurrentFolders] = useState([]);
    const [selectedFolders, setSelectedFolders] = useState([]);
    const [path, setPath] = useState([{ id: 'root', name: 'My Drive' }]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isSaving, setIsSaving] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const currentParent = path[path.length - 1];

    useEffect(() => {
        loadFolders(currentParent.id);
    }, [currentParent.id]);

    const loadFolders = async (parentId) => {
        try {
            setIsLoading(true);
            setError(null);
            const data = await fetchGoogleFolders(parentId);
            setCurrentFolders(data.folders || []);
            setSelectedFolders(data.selected_folders || []);
        } catch (err) {
            console.error("Failed to load folders", err);
            setError("Could not load folders. Please ensure your Drive is connected.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleFolderClick = (folder) => {
        setPath([...path, { id: folder.id, name: folder.name }]);
        setSearchQuery('');
    };

    const handleBack = () => {
        if (path.length > 1) {
            setPath(path.slice(0, -1));
            setSearchQuery('');
        }
    };

    const toggleFolderSelection = (folderId) => {
        setSelectedFolders(prev => 
            prev.includes(folderId) 
                ? prev.filter(id => id !== folderId)
                : [...prev, folderId]
        );
    };

    const handleSave = async () => {
        try {
            setIsSaving(true);
            await updateMonitoredFolders(selectedFolders);
            if (onSave) onSave(selectedFolders);
            onClose();
        } catch (err) {
            console.error("Failed to save changes", err);
            setError("Failed to save selection. Please try again.");
        } finally {
            setIsSaving(false);
        }
    };

    const filteredFolders = currentFolders.filter(f => 
        f.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex flex-col h-[500px] w-full max-w-2xl bg-surface-900 rounded-xl border border-surface-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="px-6 py-4 border-b border-surface-800 flex items-center justify-between bg-surface-900/50 backdrop-blur-md">
                <div>
                    <h3 className="text-lg font-semibold text-surface-50">Select Folders to Sync</h3>
                    <p className="text-xs text-surface-400 mt-1">Files in these folders will be indexed for intelligence.</p>
                </div>
                <button 
                    onClick={onClose}
                    className="p-1.5 rounded-lg hover:bg-surface-800 text-surface-400 transition-colors"
                >
                    <AlertCircle size={20} className="rotate-45" />
                </button>
            </div>

            {/* Path Navigation */}
            <div className="px-6 py-2 bg-surface-800/30 flex items-center gap-2 overflow-x-auto whitespace-nowrap scrollbar-hide border-b border-surface-800/50">
                {path.map((p, i) => (
                    <React.Fragment key={p.id}>
                        {i > 0 && <ChevronRight size={14} className="text-surface-600 shrink-0" />}
                        <button 
                            onClick={() => setPath(path.slice(0, i + 1))}
                            className={`text-xs font-medium transition-colors ${i === path.length - 1 ? 'text-accent-400' : 'text-surface-400 hover:text-surface-200'}`}
                        >
                            {p.name}
                        </button>
                    </React.Fragment>
                ))}
            </div>

            {/* Search and Selection Status */}
            <div className="p-4 flex items-center gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500" size={16} />
                    <input 
                        type="text" 
                        placeholder="Search folders..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-surface-800 border border-surface-700/50 rounded-lg pl-9 pr-4 py-2 text-sm text-surface-200 placeholder-surface-500 focus:outline-none focus:border-accent-500/50 transition-colors"
                    />
                </div>
                <div className="text-xs font-medium text-surface-400 px-3 py-2 bg-surface-800/50 rounded-lg">
                    {selectedFolders.length} <span className="text-surface-500">Selected</span>
                </div>
            </div>

            {/* Folder List */}
            <div className="flex-1 overflow-y-auto px-4 pb-4">
                {isLoading ? (
                    <div className="h-full flex flex-col items-center justify-center text-surface-500 gap-3">
                        <Loader2 className="animate-spin text-accent-500" size={32} />
                        <p className="text-sm">Fetching folders...</p>
                    </div>
                ) : error ? (
                    <div className="h-full flex flex-col items-center justify-center text-red-400 gap-3 text-center px-10">
                        <AlertCircle size={32} />
                        <p className="text-sm font-medium">{error}</p>
                    </div>
                ) : filteredFolders.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-surface-500 gap-3">
                        <Folder size={32} className="opacity-20" />
                        <p className="text-sm">No folders found in this directory.</p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {path.length > 1 && (
                            <button 
                                onClick={handleBack}
                                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-surface-800 text-surface-400 transition-colors text-sm font-medium"
                            >
                                <ChevronLeft size={18} />
                                Back to parent
                            </button>
                        )}
                        {filteredFolders.map(folder => {
                            const isSelected = selectedFolders.includes(folder.id);
                            return (
                                <div 
                                    key={folder.id}
                                    className={`group flex items-center justify-between px-3 py-2.5 rounded-lg transition-all border ${isSelected ? 'bg-accent-500/10 border-accent-500/30' : 'hover:bg-surface-800/60 border-transparent hover:border-surface-700/50'}`}
                                >
                                    <div 
                                        className="flex-1 flex items-center gap-3 cursor-pointer overflow-hidden"
                                        onClick={() => handleFolderClick(folder)}
                                    >
                                        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${isSelected ? 'bg-accent-500/20 text-accent-400' : 'bg-surface-800 text-surface-400'}`}>
                                            <Folder size={18} />
                                        </div>
                                        <span className={`text-sm font-medium truncate pr-4 ${isSelected ? 'text-surface-100' : 'text-surface-300'}`}>
                                            {folder.name}
                                        </span>
                                    </div>
                                    <button 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            toggleFolderSelection(folder.id);
                                        }}
                                        className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all ${isSelected ? 'bg-accent-500 text-white shadow-lg shadow-accent-500/20' : 'bg-surface-800 text-surface-500 hover:text-surface-200 hover:bg-surface-700 border border-surface-700/50'}`}
                                    >
                                        {isSelected ? <Check size={16} /> : <div className="w-4 h-4 border-2 border-surface-600 rounded-sm" />}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-surface-800 bg-surface-900/80 backdrop-blur-md flex items-center justify-between">
                <div className="flex items-center gap-2 text-surface-500">
                    <Info size={14} />
                    <span className="text-[10px] uppercase tracking-wider font-semibold">Only folders are shown here</span>
                </div>
                <div className="flex items-center gap-3">
                    <button 
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-surface-400 hover:text-surface-200 transition-colors"
                    >
                        Cancel
                    </button>
                    <button 
                        onClick={handleSave}
                        disabled={isSaving || selectedFolders.length === 0}
                        className="px-6 py-2 bg-accent-500 hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-all flex items-center gap-2 shadow-lg shadow-accent-500/25"
                    >
                        {isSaving && <Loader2 size={16} className="animate-spin" />}
                        Apply Selection
                    </button>
                </div>
            </div>
        </div>
    );
}
