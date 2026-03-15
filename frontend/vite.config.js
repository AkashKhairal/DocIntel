import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        host: '0.0.0.0',
        proxy: {
            '/chat': 'http://backend:8000',
            '/documents': 'http://backend:8000',
            '/sync-status': 'http://backend:8000',
            '/settings': 'http://backend:8000',
            '/drive': 'http://backend:8000',
            '/health': 'http://backend:8000',
        },
    },
});
