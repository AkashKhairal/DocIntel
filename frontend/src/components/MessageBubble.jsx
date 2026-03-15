import React from 'react';
import ReactMarkdown from 'react-markdown';
import SourceCard from './SourceCard';
import { Bot, User } from 'lucide-react';

export default function MessageBubble({ message }) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-4 animate-slide-up ${isUser ? 'justify-end' : 'justify-start'}`}>
            {/* Avatar */}
            {!isUser && (
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-accent-500 to-purple-500 flex items-center justify-center shadow-lg">
                    <Bot size={18} className="text-white" />
                </div>
            )}

            <div className={`max-w-[75%] ${isUser ? 'order-first' : ''}`}>
                {/* Message Bubble */}
                <div
                    className={`rounded-2xl px-5 py-3.5 ${isUser
                            ? 'bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-tr-md'
                            : 'glass rounded-tl-md text-surface-200'
                        }`}
                >
                    {isUser ? (
                        <p className="text-sm leading-relaxed">{message.content}</p>
                    ) : (
                        <div className="markdown-content text-sm leading-relaxed">
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                    )}
                </div>

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 space-y-2">
                        <p className="text-xs text-surface-400 font-medium uppercase tracking-wider px-1">
                            Sources
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {message.sources.map((source, idx) => (
                                <SourceCard key={idx} source={source} />
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {isUser && (
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-surface-700 flex items-center justify-center">
                    <User size={18} className="text-surface-300" />
                </div>
            )}
        </div>
    );
}
