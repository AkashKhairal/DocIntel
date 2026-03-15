import React, { useState } from 'react';
import ChatArea from './components/ChatArea';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';

export default function App() {
    const [settingsOpen, setSettingsOpen] = useState(false);

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-surface-900">
            {/* Sidebar */}
            <Sidebar onOpenSettings={() => setSettingsOpen(true)} />

            {/* Main Chat Area */}
            <main className="flex-1 flex flex-col min-w-0">
                <ChatArea />
            </main>

            {/* Settings Modal */}
            <SettingsModal
                isOpen={settingsOpen}
                onClose={() => setSettingsOpen(false)}
            />
        </div>
    );
}
