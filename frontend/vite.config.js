import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        host: '0.0.0.0',
        proxy: {
            '/auth': 'http://localhost:8000',
            '/integrations': 'http://localhost:8000',
            '/chat': 'http://localhost:8000',
            '/documents': 'http://localhost:8000',
            '/sync-status': 'http://localhost:8000',
            '/settings': 'http://localhost:8000',
            '/drive': 'http://localhost:8000',
            '/health': 'http://localhost:8000',
        },
    },
});
