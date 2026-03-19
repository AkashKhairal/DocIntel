import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchTenants, createTenant } from '../services/adminApi.js';

export default function TenantsPage() {
    const [tenants, setTenants] = useState([]);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState(null);

    const load = async () => {
        try {
            setTenants(await fetchTenants());
        } catch (err) {
            setError(err.message);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await createTenant({ name, owner_email: email });
            setName('');
            setEmail('');
            load();
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h2>Tenants</h2>
            <form onSubmit={handleCreate} className="tenant-form">
                <input
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Tenant name"
                />
                <input
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Owner email"
                    type="email"
                />
                <button type="submit">Create Tenant</button>
            </form>
            {error && <p className="error">{error}</p>}
            <table>
                <thead>
                    <tr><th>Name</th><th>Status</th><th>Users</th><th>Action</th></tr>
                </thead>
                <tbody>
                    {tenants.map((t) => (
                        <tr key={t.id}>
                            <td>{t.name}</td>
                            <td>{t.status ?? 'active'}</td>
                            <td>{t.users ?? 0}</td>
                            <td><Link to={`/tenants/${t.id}`}>View</Link></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
