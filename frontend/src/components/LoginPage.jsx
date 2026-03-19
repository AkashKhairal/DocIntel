import React, { useState } from 'react';
import { login, signup } from '../services/api';

export default function LoginPage({ onAuthComplete }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isSignup, setIsSignup] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            if (isSignup) {
                await signup(email, password);
            } else {
                await login(email, password);
            }
            onAuthComplete();
        } catch (err) {
            setError(err.message || 'Unable to authenticate');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-surface-900 text-surface-100 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-surface-800 border border-surface-700 rounded-2xl p-8 shadow-2xl">
                <h2 className="text-2xl font-bold mb-3">{isSignup ? 'Sign Up' : 'Log In'}</h2>
                <p className="text-sm mb-6 text-surface-400">
                    {isSignup
                        ? 'Create an account for DocIntel SaaS'
                        : 'Sign in to manage your organization and Google Drive integration.'}
                </p>

                {error && (
                    <div className="mb-4 rounded-lg p-3 bg-red-500/15 border border-red-400/30 text-red-200">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-surface-900 border border-surface-700 rounded-lg px-3 py-2 text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500"
                        required
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full bg-surface-900 border border-surface-700 rounded-lg px-3 py-2 text-surface-100 focus:outline-none focus:ring-2 focus:ring-accent-500"
                        required
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2 rounded-lg bg-accent-500 hover:bg-accent-400 transition-colors font-medium"
                    >
                        {loading ? 'Processing...' : isSignup ? 'Sign Up' : 'Log In'}
                    </button>
                </form>

                <p className="mt-4 text-sm text-surface-400">
                    {isSignup ? 'Already have an account?' : 'New to DocIntel?'}{' '}
                    <button
                        type="button"
                        onClick={() => setIsSignup(!isSignup)}
                        className="font-medium text-accent-300 hover:text-accent-200"
                    >
                        {isSignup ? 'Log In' : 'Sign Up'}
                    </button>
                </p>
            </div>
        </div>
    );
}
