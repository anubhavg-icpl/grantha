/**
 * Lazy loading utilities for optimizing component loading
 */

import type { ComponentType, SvelteComponent } from "svelte";

// Types for lazy loading
export interface LazyComponentProps {
  loading?: boolean;
  error?: string | null;
}

export interface LazyLoadOptions {
  delay?: number; // Delay before loading in ms
  threshold?: number; // Intersection observer threshold
  rootMargin?: string; // Intersection observer root margin
}

// Default lazy loading options
const DEFAULT_OPTIONS: Required<LazyLoadOptions> = {
  delay: 0,
  threshold: 0.1,
  rootMargin: "50px",
};

/**
 * Create a lazy loader for dynamic imports
 */
export function createLazyLoader<
  T extends Record<string, any> = Record<string, any>,
>(
  importFn: () => Promise<{ default: ComponentType<SvelteComponent<T>> }>,
  options: LazyLoadOptions = {},
) {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let loadingPromise: Promise<ComponentType<SvelteComponent<T>>> | null = null;

  return async (): Promise<ComponentType<SvelteComponent<T>>> => {
    if (loadingPromise) {
      return loadingPromise;
    }

    loadingPromise = new Promise((resolve, reject) => {
      setTimeout(async () => {
        try {
          const module = await importFn();
          resolve(module.default);
        } catch (error) {
          console.error("Failed to load component:", error);
          reject(error);
        }
      }, opts.delay);
    });

    return loadingPromise;
  };
}

/**
 * Intersection Observer based lazy loading
 */
export function createIntersectionLazyLoader<
  T extends Record<string, any> = Record<string, any>,
>(
  importFn: () => Promise<{ default: ComponentType<SvelteComponent<T>> }>,
  options: LazyLoadOptions = {},
) {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let isLoaded = false;
  let component: ComponentType<SvelteComponent<T>> | null = null;

  return {
    async loadWhenVisible(
      element: HTMLElement,
    ): Promise<ComponentType<SvelteComponent<T>>> {
      if (isLoaded && component) {
        return component;
      }

      return new Promise((resolve, reject) => {
        const observer = new IntersectionObserver(
          async (entries) => {
            const [entry] = entries;
            if (entry.isIntersecting) {
              observer.disconnect();
              try {
                setTimeout(async () => {
                  const module = await importFn();
                  component = module.default;
                  isLoaded = true;
                  resolve(component);
                }, opts.delay);
              } catch (error) {
                console.error("Failed to load component:", error);
                reject(error);
              }
            }
          },
          {
            threshold: opts.threshold,
            rootMargin: opts.rootMargin,
          },
        );

        observer.observe(element);
      });
    },

    get isLoaded() {
      return isLoaded;
    },

    get component() {
      return component;
    },
  };
}

/**
 * Route-based code splitting helper
 */
export const routeLazyLoaders = {
  // Chat components - heavy AI interaction
  ChatArea: createLazyLoader(
    () => import("$components/chat/ChatArea.svelte") as any,
    { delay: 100 },
  ),

  ChatInput: createLazyLoader(
    () => import("$components/chat/ChatInput.svelte"),
    { delay: 50 },
  ),

  // Research components - data intensive (placeholder - component doesn't exist yet)
  // ResearchView: createLazyLoader(
  //	() => import('$components/research/ResearchView.svelte'),
  //	{ delay: 150 }
  // ),

  // Wiki components - content heavy (placeholder - component doesn't exist yet)
  // WikiEditor: createLazyLoader(
  //	() => import('$components/wiki/WikiEditor.svelte'),
  //	{ delay: 200 }
  // ),

  // Model selector - API heavy
  ModelSelector: createLazyLoader(
    () => import("$components/models/ModelSelector.svelte") as any,
    { delay: 100 },
  ),

  // Project components - file system heavy
  ProcessedProjects: createLazyLoader(
    () => import("$components/projects/ProcessedProjects.svelte") as any,
    { delay: 150 },
  ),
};

/**
 * Preload components based on user interaction hints
 */
export class ComponentPreloader {
  private loadedComponents = new Set<string>();
  private preloadPromises = new Map<string, Promise<any>>();

  constructor(
    private loaders: Record<string, ReturnType<typeof createLazyLoader>>,
  ) {}

  /**
   * Preload a component
   */
  async preload(componentName: string): Promise<void> {
    if (this.loadedComponents.has(componentName)) {
      return;
    }

    if (this.preloadPromises.has(componentName)) {
      return this.preloadPromises.get(componentName);
    }

    const loader = this.loaders[componentName];
    if (!loader) {
      console.warn(`No loader found for component: ${componentName}`);
      return;
    }

    const promise = loader().then(() => {
      this.loadedComponents.add(componentName);
    });

    this.preloadPromises.set(componentName, promise);
    return promise;
  }

  /**
   * Preload components when user hovers over navigation
   */
  onNavigationHover(routeName: string): void {
    const componentsToPreload = this.getComponentsForRoute(routeName);
    componentsToPreload.forEach((component) => {
      setTimeout(() => this.preload(component), 100); // Small delay to avoid blocking UI
    });
  }

  /**
   * Preload components on idle
   */
  preloadOnIdle(): void {
    if ("requestIdleCallback" in window) {
      requestIdleCallback(() => {
        const componentsToPreload = [
          "ChatArea",
          "ModelSelector",
          "ProcessedProjects",
        ];
        componentsToPreload.forEach((component) => this.preload(component));
      });
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(() => {
        const componentsToPreload = ["ChatArea", "ModelSelector"];
        componentsToPreload.forEach((component) => this.preload(component));
      }, 2000);
    }
  }

  private getComponentsForRoute(routeName: string): string[] {
    const routeComponentMap: Record<string, string[]> = {
      "/chat": ["ChatArea", "ChatInput", "ModelSelector"],
      "/research": ["ModelSelector"], // ResearchView doesn't exist yet
      "/wiki": [], // WikiEditor doesn't exist yet
      "/projects": ["ProcessedProjects"],
    };

    return routeComponentMap[routeName] || [];
  }
}

// Global preloader instance
export const componentPreloader = new ComponentPreloader(routeLazyLoaders);

/**
 * Image lazy loading with intersection observer
 */
export function lazyLoadImage(img: HTMLImageElement, src: string): void {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const image = entry.target as HTMLImageElement;
          image.src = src;
          image.onload = () => {
            image.classList.add("loaded");
          };
          observer.unobserve(image);
        }
      });
    },
    {
      rootMargin: "50px",
    },
  );

  observer.observe(img);
}

/**
 * Performance monitoring for lazy loading
 */
export class LazyLoadPerformanceMonitor {
  private static instance: LazyLoadPerformanceMonitor;
  private loadTimes = new Map<string, number>();

  static getInstance(): LazyLoadPerformanceMonitor {
    if (!LazyLoadPerformanceMonitor.instance) {
      LazyLoadPerformanceMonitor.instance = new LazyLoadPerformanceMonitor();
    }
    return LazyLoadPerformanceMonitor.instance;
  }

  startLoad(componentName: string): void {
    this.loadTimes.set(`${componentName}_start`, performance.now());
  }

  endLoad(componentName: string): void {
    const startTime = this.loadTimes.get(`${componentName}_start`);
    if (startTime) {
      const duration = performance.now() - startTime;
      console.log(`Lazy loaded ${componentName} in ${duration.toFixed(2)}ms`);
      this.loadTimes.set(componentName, duration);
    }
  }

  getLoadTime(componentName: string): number | undefined {
    return this.loadTimes.get(componentName);
  }

  getAverageLoadTime(): number {
    const times = Array.from(this.loadTimes.values()).filter(
      (time) => typeof time === "number",
    );
    return times.length > 0
      ? times.reduce((sum, time) => sum + time, 0) / times.length
      : 0;
  }
}
