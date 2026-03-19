import React, { useState, useEffect } from 'react';
import { fetchUsers, createUser } from '../services/api';
import { UserPlus, Users, ShieldCheck } from 'lucide-react';

export default function UsersPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [newUser, setNewUser] = useState({ email: '', password: '' });

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetchUsers();
            setUsers(res.users || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            await createUser(newUser.email, newUser.password);
            setNewUser({ email: '', password: '' });
            await loadUsers();
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="p-6 h-full overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h2 className="text-2xl font-bold text-surface-100">User Management</h2>
                    <p className="text-sm text-surface-400">Add users and manage roles for your organization.</p>
                </div>
                <div className="inline-flex items-center gap-2 text-surface-300">
                    <Users size={18} />
                    <span>{users.length} users</span>
                </div>
            </div>

            <form onSubmit={handleCreateUser} className="mb-5 grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                    type="email"
                    required
                    placeholder="Email"
                    value={newUser.email}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, email: e.target.value }))}
                    className="px-3 py-2 rounded-lg border border-surface-700 bg-surface-800 text-surface-100 focus:ring-2 focus:ring-accent-500"
                />
                <input
                    type="password"
                    required
                    placeholder="Password"
                    value={newUser.password}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, password: e.target.value }))}
                    className="px-3 py-2 rounded-lg border border-surface-700 bg-surface-800 text-surface-100 focus:ring-2 focus:ring-accent-500"
                />
                <button
                    type="submit"
                    className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:opacity-90"
                >
                    <UserPlus size={16} /> Add user
                </button>
            </form>

            {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

            <div className="rounded-2xl border border-surface-700 bg-surface-800 p-4">
                <div className="grid grid-cols-4 text-xs text-surface-500 uppercase tracking-wider font-semibold mb-2">
                    <div>Email</div>
                    <div>Role</div>
                    <div>Status</div>
                    <div>Created</div>
                </div>
                {loading ? (
                    <p className="text-sm text-surface-400">Loading...</p>
                ) : users.length === 0 ? (
                    <p className="text-sm text-surface-400">No users registered yet.</p>
                ) : (
                    users.map((user) => (
                        <div key={user.id} className="grid grid-cols-4 py-2 border-t border-surface-700 text-sm text-surface-100">
                            <div>{user.email}</div>
                            <div>{user.role}</div>
                            <div>{user.is_active ? 'Active' : 'Disabled'}</div>
                            <div>{new Date(user.created_at).toLocaleDateString()}</div>
                        </div>
                    ))
                )}
            </div>

            <div className="mt-5 text-xs text-surface-500 flex items-center gap-2">
                <ShieldCheck size={14} />
                Role-based access control is enforced by the API.
            </div>
        </div>
    );
}
