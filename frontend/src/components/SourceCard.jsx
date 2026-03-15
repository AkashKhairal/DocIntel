import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';

export default function SourceCard({ source }) {
    return (
        <a
            href={source.drive_link || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-2.5 px-3 py-2 rounded-xl glass hover:bg-surface-700/60 transition-all duration-200 cursor-pointer border border-transparent hover:border-accent-500/30"
        >
            <div className="w-7 h-7 rounded-lg bg-accent-500/15 flex items-center justify-center flex-shrink-0">
                <FileText size={14} className="text-accent-400" />
            </div>
            <div className="min-w-0">
                <p className="text-xs font-medium text-surface-200 truncate max-w-[180px]">
                    {source.file_name}
                </p>
                {source.folder_path && source.folder_path !== '/' && (
                    <p className="text-[10px] text-surface-500 truncate max-w-[180px]">
                        {source.folder_path}
                    </p>
                )}
            </div>
            <ExternalLink
                size={12}
                className="text-surface-500 group-hover:text-accent-400 transition-colors flex-shrink-0 ml-1"
            />
        </a>
    );
}
