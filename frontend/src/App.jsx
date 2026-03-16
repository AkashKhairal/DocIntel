import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ChatArea from './components/ChatArea';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';
import DocumentHub from './components/DocumentHub';
import ProgressWidget from './components/ProgressWidget';

function Layout({ children }) {
    const [settingsOpen, setSettingsOpen] = useState(false);

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-surface-900">
            {/* Sidebar */}
            <Sidebar onOpenSettings={() => setSettingsOpen(true)} />

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0">
                {children}
            </main>

            {/* Global floating components */}
            <ProgressWidget />

            {/* Settings Modal */}
            <SettingsModal
                isOpen={settingsOpen}
                onClose={() => setSettingsOpen(false)}
            />
        </div>
    );
}

export default function App() {
    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/chat" element={<ChatArea />} />
                    <Route path="/documents" element={<DocumentHub />} />
                    <Route path="/" element={<Navigate to="/chat" replace />} />
                </Routes>
            </Layout>
        </BrowserRouter>
    );
}
