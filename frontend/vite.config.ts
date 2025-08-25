import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
	// Load env file from project root (unified .env)
	const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
	
	const frontendPort = parseInt(env.FRONTEND_PORT || '3000');
	const apiPort = parseInt(env.API_PORT || '8000');
	const serverBaseUrl = env.SERVER_BASE_URL || `http://localhost:${apiPort}`;

	return {
		plugins: [sveltekit()],
		resolve: {
			alias: {
				$lib: path.resolve('./src/lib'),
				$components: path.resolve('./src/lib/components'),
				$types: path.resolve('./src/lib/types'),
				$api: path.resolve('./src/lib/api'),
				$stores: path.resolve('./src/lib/stores'),
				$utils: path.resolve('./src/lib/utils')
			}
		},
		server: {
			proxy: {
				'/api': {
					target: serverBaseUrl,
					changeOrigin: true,
					secure: false,
					ws: true,
					rewrite: (path: string) => path.replace(/^\/api/, '/api')
				},
				'/ws': {
					target: serverBaseUrl.replace('http', 'ws'),
					ws: true,
					changeOrigin: true
				}
			},
			host: env.FRONTEND_HOST === '0.0.0.0' ? true : env.FRONTEND_HOST || 'localhost',
			port: frontendPort,
			strictPort: true
		},
		preview: {
			port: frontendPort,
			host: env.FRONTEND_HOST === '0.0.0.0' ? true : env.FRONTEND_HOST || 'localhost'
		},
		build: {
			target: 'es2020',
			sourcemap: mode === 'development',
			rollupOptions: {
				output: {
					manualChunks: {
						vendor: ['svelte', '@sveltejs/kit'],
						ui: ['lucide-svelte', 'tailwind-merge', 'clsx'],
						utils: ['zod']
					}
				}
			}
		},
		optimizeDeps: {
			include: ['svelte', 'lucide-svelte']
		},
		define: {
			// Pass environment variables to the client
			__APP_VERSION__: JSON.stringify(env.APP_VERSION || '1.0.0'),
			__BUILD_TIME__: JSON.stringify(new Date().toISOString())
		}
	};
});