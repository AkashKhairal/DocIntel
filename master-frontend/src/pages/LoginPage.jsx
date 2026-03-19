import { useState } from 'react';
import { login } from '../services/adminApi.js';

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('admin@docintel.local');
  const [password, setPassword] = useState('Admin1234!');
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setError(null);
      const token = await login(email, password);
      window.localStorage.setItem('docintel_admin_token', token.access_token);
      onLogin();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-container">
      <h2>Master Admin Login</h2>
      <form onSubmit={handleSubmit} className="login-form">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        <button type="submit">Sign in</button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
