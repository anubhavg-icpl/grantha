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
			// Optimize build output
			rollupOptions: {
				output: {
					// Code splitting configuration
					manualChunks: {
						// Separate vendor libraries
						vendor: ['svelte'],
						ui: ['lucide-svelte', 'bits-ui', 'mode-watcher'],
						forms: ['formsnap', 'sveltekit-superforms', 'zod'],
						utils: ['clsx', 'tailwind-merge', 'tailwind-variants']
					},
					// Optimize chunk naming
					chunkFileNames: 'chunks/[name]-[hash].js',
					assetFileNames: 'assets/[name]-[hash].[ext]'
				}
			},
			// Build optimizations
			reportCompressedSize: false, // Faster builds
			chunkSizeWarningLimit: 1000 // Increase chunk size warning limit
		},
		optimizeDeps: {
			include: [
				'svelte', 
				'lucide-svelte',
				'bits-ui',
				'clsx',
				'tailwind-merge'
			],
			exclude: [
				// Exclude large libraries from pre-bundling if they're only used in specific routes
				'@tailwindcss/typography'
			]
		},
		define: {
			// Pass environment variables to the client
			__APP_VERSION__: JSON.stringify(env.APP_VERSION || '1.0.0'),
			__BUILD_TIME__: JSON.stringify(new Date().toISOString())
		}
	};
});