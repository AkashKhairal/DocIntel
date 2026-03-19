import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchTenant, updateTenant } from '../services/adminApi.js';

export default function TenantDetailPage() {
    const { tenantId } = useParams();
    const [tenant, setTenant] = useState(null);
    const [error, setError] = useState('');
    const [plan, setPlan] = useState('');

    useEffect(() => {
        (async () => {
            try {
                const data = await fetchTenant(tenantId);
                setTenant(data);
                setPlan(data.plan || 'standard');
            } catch (err) {
                setError(err.message);
            }
        })();
    }, [tenantId]);

    const updateTenantStatus = async () => {
        try {
            await updateTenant(tenantId, { status: tenant.status || 'active' });
            setError('');
            const data = await fetchTenant(tenantId);
            setTenant(data);
        } catch (err) {
            setError(err.message);
        }
    };

    if (!tenant) return <div>Loading</div>;

    return (
        <div>
            <h2>Tenant: {tenant.name}</h2>
            {error && <p className="error">{error}</p>}
            <div className="card">
                <p><strong>ID:</strong> {tenant.id}</p>
                <p><strong>Status:</strong> {tenant.status}</p>
                <p><strong>Organizations:</strong> {tenant.organizations?.length ?? 0}</p>
                <p><strong>Users:</strong> {tenant.users?.length ?? 0}</p>
            </div>
            <div className="card">
                <h3>Tenant controls</h3>
                <select value={tenant.status || 'active'} onChange={(e) => setTenant((prev) => ({ ...prev, status: e.target.value }))}>
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="archived">Archived</option>
                </select>
                <button onClick={updateTenantStatus}>Save Status</button>
            </div>
        </div>
    );
}
