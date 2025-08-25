import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
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
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false,
				ws: true
			}
		},
		host: true,
		port: 3000
	},
	preview: {
		port: 3000
	},
	build: {
		target: 'es2020',
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
	}
});