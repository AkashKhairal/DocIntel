import { useEffect, useState } from 'react';
import { fetchAdminStats } from '../services/adminApi.js';

export default function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        (async () => {
            try {
                const data = await fetchAdminStats();
                setStats(data);
            } catch (err) {
                setError(err.message);
            }
        })();
    }, []);

    return (
        <div>
            <h2>Master Dashboard</h2>
            {error && <p className="error">{error}</p>}
            {stats ? (
                <div className="grid">
                    <div className="card">
                        <h3>Tenants</h3>
                        <p>{stats.total_tenants}</p>
                    </div>
                    <div className="card">
                        <h3>Organizations</h3>
                        <p>{stats.total_organizations}</p>
                    </div>
                    <div className="card">
                        <h3>Users</h3>
                        <p>{stats.total_users}</p>
                    </div>
                </div>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
}
