// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { ComponentType, SvelteComponent } from "svelte";

declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }

  // Global type augmentations for better TypeScript support
  interface Window {
    requestIdleCallback?: (callback: () => void) => void;
  }

  // Event handler types for better Svelte component typing
  type EventHandler<T = Event> = (event: T) => void;
  type MouseEventHandler = EventHandler<MouseEvent>;
  type KeyboardEventHandler = EventHandler<KeyboardEvent>;
  type InputEventHandler = EventHandler<Event & { target: HTMLInputElement }>;
  type FormEventHandler = EventHandler<SubmitEvent>;

  // Component prop types
  interface BaseComponentProps {
    class?: string;
    style?: string;
  }

  // Lazy loading types
  interface LazyComponentLoader<T = Record<string, any>> {
    (): Promise<ComponentType<SvelteComponent<T>>>;
  }
}

export {};
