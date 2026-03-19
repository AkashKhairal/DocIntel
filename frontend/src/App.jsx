import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import ChatArea from './components/ChatArea';
import { me, clearAccessToken, getAccessToken } from './services/api';
import Sidebar from './components/Sidebar';
import SettingsPage from './components/SettingsPage';
import DocumentHub from './components/DocumentHub';
import ProgressWidget from './components/ProgressWidget';
import IntegrationsPage from './components/IntegrationsPage';
import UsersPage from './components/UsersPage';
import LoginPage from './components/LoginPage';
import SettingsModal from './components/SettingsModal';

function Layout({ children, onOpenSettings }) {
    return (
        <div className="flex h-screen w-screen overflow-hidden bg-surface-900">
            <Sidebar onOpenSettings={onOpenSettings} />
            <main className="flex-1 flex flex-col min-w-0 overflow-hidden">{children}</main>
            <ProgressWidget />
        </div>
    );
}

function Dashboard() {
    return (
        <div className="p-6 h-full overflow-y-auto">
            <h1 className="text-3xl font-bold text-surface-100 mb-4">Enterprise Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                <div className="bg-surface-800 rounded-2xl p-5 border border-surface-700"> <h3 className="text-sm text-surface-400">Total Documents</h3> <p className="text-3xl font-bold text-amber-400">--</p> </div>
                <div className="bg-surface-800 rounded-2xl p-5 border border-surface-700"> <h3 className="text-sm text-surface-400">Indexed Vectors</h3> <p className="text-3xl font-bold text-emerald-400">--</p> </div>
                <div className="bg-surface-800 rounded-2xl p-5 border border-surface-700"> <h3 className="text-sm text-surface-400">Active Users</h3> <p className="text-3xl font-bold text-blue-400">--</p> </div>
                <div className="bg-surface-800 rounded-2xl p-5 border border-surface-700"> <h3 className="text-sm text-surface-400">Upcoming Sync</h3> <p className="text-3xl font-bold text-purple-400">--</p> </div>
            </div>

            <div className="mt-6 bg-surface-800 border border-surface-700 rounded-2xl p-5">
                <h2 className="text-lg font-semibold text-surface-100 mb-2">Release Notes</h2>
                <p className="text-sm text-surface-400">Google Drive OAuth, multi-tenant security, real-time webhook ingestion, and enterprise-grade dashboard features are active.</p>
            </div>
        </div>
    );
}

function GoogleDriveCallback() {
    const navigate = useNavigate();
    const [message, setMessage] = useState('Connecting your Google Drive...');

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('status') === 'connected') {
            setMessage('Google Drive connected successfully. Redirecting...');
            setTimeout(() => navigate('/chat', { replace: true }), 1700);
        } else {
            setMessage('Google Drive connection failed or canceled.');
        }
    }, [navigate]);

    return (
        <div className="h-screen w-screen flex items-center justify-center bg-surface-900 text-surface-100">
            <div className="bg-surface-800 border border-surface-700 rounded-xl p-8 text-center max-w-md">
                <p className="text-lg font-semibold mb-2">Google Drive OAuth</p>
                <p className="text-sm text-surface-300">{message}</p>
            </div>
        </div>
    );
}

function ErrorOverlay({ error }) {
    if (!error) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 text-white p-6">
            <div className="max-w-2xl w-full bg-surface-900/95 border border-red-500 rounded-2xl p-6">
                <h2 className="text-xl font-bold text-red-300 mb-4">Application Error</h2>
                <pre className="whitespace-pre-wrap text-sm text-surface-100 bg-black/30 rounded-lg p-4 overflow-x-auto">{error}</pre>
                <p className="mt-4 text-sm text-surface-300">Open the browser console for more details.</p>
            </div>
        </div>
    );
}

export default function App() {
    const [authChecked, setAuthChecked] = useState(false);
    const [authenticated, setAuthenticated] = useState(false);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [appError, setAppError] = useState('');

    useEffect(() => {
        const handleGlobalError = (event) => {
            const message = event?.message || event?.reason?.message || 'Unknown error';
            setAppError(message.toString());
            console.error('Global error:', event);
        };

        window.addEventListener('error', handleGlobalError);
        window.addEventListener('unhandledrejection', handleGlobalError);

        return () => {
            window.removeEventListener('error', handleGlobalError);
            window.removeEventListener('unhandledrejection', handleGlobalError);
        };
    }, []);

    useEffect(() => {
        let cancelled = false;

        (async () => {
            try {
                await me();
                if (!cancelled && getAccessToken()) {
                    setAuthenticated(true);
                } else if (!cancelled) {
                    setAuthenticated(false);
                }
            } catch {
                if (!cancelled) {
                    setAuthenticated(false);
                }
            } finally {
                if (!cancelled) {
                    setAuthChecked(true);
                }
            }
        })();

        return () => {
            cancelled = true;
        };
    }, []);

    if (!authChecked) {
        return (
            <div className="h-screen w-screen flex items-center justify-center bg-surface-900 text-surface-100">Loading authentication...</div>
        );
    }

    if (!authenticated) {
        return (
            <BrowserRouter>
                <Routes>
                    <Route
                        path="/login"
                        element={
                            <LoginPage
                                onAuthComplete={() => {
                                    setAuthenticated(true);
                                    setAuthChecked(true);
                                }}
                            />
                        }
                    />
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
                <ErrorOverlay error={appError} />
            </BrowserRouter>
        );
    }

    return (
        <BrowserRouter>
            <Layout onOpenSettings={() => setSettingsOpen(true)}>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/chat" element={<ChatArea />} />
                    <Route path="/documents" element={<DocumentHub />} />
                    <Route path="/integrations" element={<IntegrationsPage />} />
                    <Route path="/googledrive-callback" element={<GoogleDriveCallback />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/users" element={<UsersPage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>

                <div className="fixed top-4 right-4">
                    <button
                        className="px-3 py-2 rounded-lg bg-surface-900 border border-surface-700 text-surface-200 hover:bg-surface-800"
                        onClick={() => {
                            clearAccessToken();
                            setAuthenticated(false);
                            setAuthChecked(true);
                            window.location.href = '/login';
                        }}
                    >
                        Logout
                    </button>
                </div>

                <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
            </Layout>
            <ErrorOverlay error={appError} />
        </BrowserRouter>
    );
}
