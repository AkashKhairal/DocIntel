import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage.jsx';
import TenantsPage from './pages/TenantsPage.jsx';
import TenantDetailPage from './pages/TenantDetailPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import { fetchCurrentUser } from './services/adminApi.js';

const navLinkClass = ({ isActive }) =>
    isActive
        ? 'nav-item active'
        : 'nav-item';

function AppRouter({ onLogout }) {
    return (
        <BrowserRouter>
            <div className="app">
                <aside className="sidebar">
                    <h1>DocIntel SaaS Admin</h1>
                    <nav>
                        <NavLink to="/" className={navLinkClass} end>
                            Dashboard
                        </NavLink>
                        <NavLink to="/tenants" className={navLinkClass}>
                            Tenants
                        </NavLink>
                        <button type="button" className="logout-button" onClick={onLogout}>
                            Logout
                        </button>
                    </nav>
                </aside>
                <main className="content">
                    <Routes>
                        <Route path="/" element={<DashboardPage />} />
                        <Route path="/tenants" element={<TenantsPage />} />
                        <Route path="/tenants/:tenantId" element={<TenantDetailPage />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            const token = window.localStorage.getItem('docintel_admin_token');
            if (!token) {
                setIsAuthenticated(false);
                setLoading(false);
                return;
            }

            try {
                await fetchCurrentUser();
                setIsAuthenticated(true);
            } catch {
                window.localStorage.removeItem('docintel_admin_token');
                setIsAuthenticated(false);
            } finally {
                setLoading(false);
            }
        };

        checkAuth();
    }, []);

    const handleLogin = () => setIsAuthenticated(true);
    const handleLogout = () => {
        window.localStorage.removeItem('docintel_admin_token');
        setIsAuthenticated(false);
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
        return <LoginPage onLogin={handleLogin} />;
    }

    return <AppRouter onLogout={handleLogout} />;
}
