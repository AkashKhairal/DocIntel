import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { sendChatMessage } from '../services/api';
import { Send, Sparkles, MessageSquare } from 'lucide-react';

export default function ChatArea() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const question = input.trim();
        setInput('');

        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: question }]);
        setIsLoading(true);

        // Create placeholder for assistant response
        const assistantMsg = { role: 'assistant', content: '', sources: [] };
        setMessages(prev => [...prev, assistantMsg]);

        try {
            await sendChatMessage(question, (chunk) => {
                if (chunk.type === 'text') {
                    setMessages(prev => {
                        const updated = [...prev];
                        const lastMsg = updated[updated.length - 1];
                        if (lastMsg.role === 'assistant') {
                            lastMsg.content += chunk.content;
                        }
                        return [...updated];
                    });
                } else if (chunk.type === 'sources') {
                    setMessages(prev => {
                        const updated = [...prev];
                        const lastMsg = updated[updated.length - 1];
                        if (lastMsg.role === 'assistant') {
                            lastMsg.sources = chunk.content;
                        }
                        return [...updated];
                    });
                }
            });
        } catch (error) {
            setMessages(prev => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg.role === 'assistant') {
                    lastMsg.content = `Error: ${error.message}`;
                }
                return [...updated];
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full animate-fade-in">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-500 to-purple-600 flex items-center justify-center mb-6 shadow-xl shadow-accent-500/20">
                            <Sparkles size={28} className="text-white" />
                        </div>
                        <h2 className="text-2xl font-semibold text-surface-100 mb-2">
                            DocIntel
                        </h2>
                        <p className="text-surface-400 text-center max-w-md mb-8 leading-relaxed">
                            Ask anything about your company documents. I'll search through
                            indexed files and provide answers with sources.
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                            {[
                                'What documents were created last month?',
                                'Show me all reports for client HDFC',
                                'What work did Rahul do in February?',
                                'Summarize the latest project updates',
                            ].map((suggestion, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setInput(suggestion)}
                                    className="text-left px-4 py-3 rounded-xl glass hover:bg-surface-700/60 text-sm text-surface-300 hover:text-surface-100 transition-all duration-200 border border-transparent hover:border-accent-500/20"
                                >
                                    <MessageSquare size={14} className="inline mr-2 text-accent-400" />
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="max-w-3xl mx-auto space-y-6">
                        {messages.map((msg, idx) => (
                            <MessageBubble key={idx} message={msg} />
                        ))}

                        {/* Typing Indicator */}
                        {isLoading && messages[messages.length - 1]?.content === '' && (
                            <div className="flex gap-4 animate-fade-in">
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                                    <Sparkles size={16} className="text-white" />
                                </div>
                                <div className="glass rounded-2xl rounded-tl-md px-5 py-4">
                                    <div className="flex gap-1.5">
                                        <span className="typing-dot w-2 h-2 rounded-full bg-accent-400"></span>
                                        <span className="typing-dot w-2 h-2 rounded-full bg-accent-400"></span>
                                        <span className="typing-dot w-2 h-2 rounded-full bg-accent-400"></span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="border-t border-surface-800/50 px-6 py-4">
                <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative">
                    <div className="relative">
                        <input
                            ref={inputRef}
                            type="text"
                            id="chat-input"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask a question about your documents..."
                            disabled={isLoading}
                            className="w-full bg-surface-800/80 border border-surface-700/50 rounded-xl px-5 py-3.5 pr-14 text-sm text-surface-100 placeholder-surface-500 input-focus outline-none disabled:opacity-50"
                            autoComplete="off"
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-lg bg-accent-500 hover:bg-accent-600 disabled:bg-surface-700 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 shadow-lg shadow-accent-500/20 disabled:shadow-none"
                        >
                            <Send size={16} className="text-white" />
                        </button>
                    </div>
                    <p className="text-[11px] text-surface-500 mt-2 text-center">
                        DocIntel answers only from indexed company documents. Responses may take a moment.
                    </p>
                </form>
            </div>
        </div>
    );
}
