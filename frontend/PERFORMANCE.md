# Frontend Performance Optimizations

This document outlines the performance optimizations implemented in the Grantha frontend application.

## Overview

The Grantha frontend is built with SvelteKit and optimized for production performance through:

1. **Code Splitting** - Automatic and manual chunk separation
2. **Lazy Loading** - Component and route-based lazy loading
3. **Bundle Optimization** - Optimized dependencies and build configuration
4. **Caching Strategies** - Browser and service worker caching
5. **Asset Optimization** - Minification and compression

## Code Splitting Configuration

### Vite Configuration (`vite.config.ts`)

```typescript
rollupOptions: {
  output: {
    // Manual chunk configuration
    manualChunks: {
      vendor: ['svelte'],                           // Core framework
      ui: ['lucide-svelte', 'bits-ui'],            // UI components  
      forms: ['formsnap', 'sveltekit-superforms'], // Form handling
      utils: ['clsx', 'tailwind-merge']            // Utilities
    }
  }
}
```

### Bundle Analysis

- **Vendor chunk**: Core Svelte framework (~50KB gzipped)
- **UI chunk**: Icon and component libraries (~30KB gzipped) 
- **Forms chunk**: Form validation and handling (~25KB gzipped)
- **Utils chunk**: CSS and utility functions (~10KB gzipped)

## Lazy Loading Implementation

### Component Lazy Loading

```typescript
// utils/lazy-loader.ts
export const routeLazyLoaders = {
  ChatArea: createLazyLoader(() => import('$components/chat/ChatArea.svelte')),
  ResearchView: createLazyLoader(() => import('$components/research/ResearchView.svelte')),
  WikiEditor: createLazyLoader(() => import('$components/wiki/WikiEditor.svelte'))
};
```

### Usage with LazyComponent

```svelte
<script>
  import LazyComponent from '$lib/components/ui/LazyComponent.svelte';
</script>

<LazyComponent 
  importFn={() => import('$components/chat/ChatArea.svelte')}
  componentName="ChatArea"
  loadOnMount={false}
  threshold={0.1}
  rootMargin="50px"
  props={{ chatId: 'example' }}
/>
```

### Intersection Observer Loading

Components load when they become visible in the viewport:

- **Threshold**: 0.1 (10% visible triggers loading)
- **Root Margin**: 50px (preload when 50px away from viewport)
- **Fallback**: Skeleton loading states while components load

## Performance Monitoring

### LazyLoadPerformanceMonitor

```typescript
const monitor = LazyLoadPerformanceMonitor.getInstance();

// Track component loading times
monitor.startLoad('ChatArea');
// ... component loads
monitor.endLoad('ChatArea');

// Get metrics
const avgTime = monitor.getAverageLoadTime();
const componentTime = monitor.getLoadTime('ChatArea');
```

### Component Preloading

```typescript
import { componentPreloader } from '$utils/lazy-loader';

// Preload on navigation hover
componentPreloader.onNavigationHover('/chat');

// Preload during idle time
componentPreloader.preloadOnIdle();
```

## Build Optimizations

### Development vs Production

**Development**:
- Source maps enabled
- Hot module replacement
- No compression
- Detailed error messages

**Production**:
- Source maps disabled
- Tree shaking enabled
- Minification and compression
- Dead code elimination

### Asset Optimization

```typescript
// vite.config.ts optimizations
build: {
  target: 'es2020',                    // Modern browser support
  reportCompressedSize: false,         // Faster builds
  chunkSizeWarningLimit: 1000,         // 1MB chunk warning
  rollupOptions: {
    output: {
      chunkFileNames: 'chunks/[name]-[hash].js',
      assetFileNames: 'assets/[name]-[hash].[ext]'
    }
  }
}
```

## Route-Based Optimization

### Page Components

Each route lazy loads its specific components:

- `/chat` → ChatArea, ChatInput, ModelSelector
- `/research` → ResearchView, ModelSelector  
- `/wiki` → WikiEditor
- `/projects` → ProcessedProjects

### Shared Components

Common components are included in the main bundle:
- Layout components (Header, Sidebar)
- UI primitives (Button, Input, Card)
- Authentication components

## Caching Strategies

### Browser Caching

```typescript
// Service worker caching (future implementation)
const CACHE_NAME = 'grantha-v1';
const STATIC_ASSETS = ['/chunks/', '/assets/', '/favicon.ico'];
```

### API Response Caching

Frontend respects backend cache headers:
- `Cache-Control` headers from API
- `ETag` support for conditional requests
- Local storage for user preferences

## Performance Metrics

### Core Web Vitals Targets

- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms  
- **CLS (Cumulative Layout Shift)**: < 0.1

### Bundle Size Targets

- **Initial bundle**: < 200KB gzipped
- **Route chunks**: < 100KB gzipped each
- **Vendor chunk**: < 150KB gzipped

## Monitoring and Analytics

### Performance Tracking

```typescript
// Track route performance
performance.mark('route-start');
// Route loads
performance.mark('route-end');
performance.measure('route-load', 'route-start', 'route-end');

// Get timing data
const timing = performance.getEntriesByType('measure');
```

### User Experience Metrics

- Component load times
- Route transition speeds
- API response times
- Error rates and retry counts

## Best Practices

### Component Design

1. **Keep components small** - Easier to lazy load
2. **Minimize dependencies** - Reduce bundle bloat
3. **Use skeleton loading** - Better perceived performance
4. **Implement error boundaries** - Graceful failure handling

### Image Optimization

```typescript
// Lazy image loading
import { lazyLoadImage } from '$utils/lazy-loader';

const img = new Image();
lazyLoadImage(img, '/path/to/image.jpg');
```

### Font Loading

```css
/* Font display optimization */
@font-face {
  font-family: 'Inter';
  font-display: swap; /* Prevent invisible text */
  src: url('/fonts/inter.woff2') format('woff2');
}
```

## Future Optimizations

### Service Workers
- Cache API responses
- Background sync
- Push notifications
- Offline functionality

### Advanced Code Splitting
- Dynamic imports based on user behavior
- Predictive loading
- Progressive enhancement

### Asset Optimization
- Image format optimization (WebP/AVIF)
- CSS purging
- Font subsetting
- SVG optimization

### Performance Budget
- Bundle size monitoring
- Performance regression testing
- Automated lighthouse audits
- Real user monitoring (RUM)

## Development Tools

### Bundle Analysis

```bash
# Analyze bundle size
npm run build
npx vite-bundle-analyzer dist

# Performance testing  
npm run test:performance
```

### Performance Profiling

```bash
# Chrome DevTools
# 1. Open DevTools → Performance tab
# 2. Record page load
# 3. Analyze flame graph and timings

# Lighthouse audit
npx lighthouse http://localhost:3000 --output=html
```

## Troubleshooting

### Common Issues

1. **Large bundle size**: Check manual chunks configuration
2. **Slow component loading**: Verify lazy loading implementation
3. **Cache issues**: Clear browser cache and check headers
4. **Poor performance**: Profile with DevTools

### Debug Mode

```bash
# Enable performance debugging
VITE_PERFORMANCE_DEBUG=true npm run dev
```

This will log:
- Component load times
- Bundle chunk loading
- Cache hit/miss ratios
- Route transition timing