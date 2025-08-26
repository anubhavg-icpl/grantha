/**
 * Models Store
 * Manages AI model configurations and provider settings
 */

import { writable, derived, get } from "svelte/store";
import { browser } from "$app/environment";
import { apiClient } from "$api/client";
import type { ModelConfig, Provider, Model } from "$types/api";

interface ModelsState {
  config: ModelConfig | null;
  selectedProvider: string | null;
  selectedModel: string | null;
  customModel: string;
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
}

// Initialize models state
const initialState: ModelsState = {
  config: null,
  selectedProvider: null,
  selectedModel: null,
  customModel: "",
  isLoading: false,
  error: null,
  lastUpdated: null,
};

// Create writable store
export const modelsState = writable<ModelsState>(initialState);

// Derived stores for computed values
export const availableProviders = derived(
  modelsState,
  ($modelsState) => $modelsState.config?.providers || [],
);

export const currentProvider = derived(
  [modelsState, availableProviders],
  ([$modelsState, $availableProviders]) => {
    if (!$modelsState.selectedProvider) return null;
    return (
      $availableProviders.find(
        (p: Provider) => p.id === $modelsState.selectedProvider,
      ) || null
    );
  },
);

export const availableModels = derived(
  currentProvider,
  ($currentProvider) => $currentProvider?.models || [],
);

export const currentModel = derived(
  [modelsState, availableModels],
  ([$modelsState, $availableModels]) => {
    if (!$modelsState.selectedModel) return null;
    return (
      $availableModels.find(
        (m: Model) => m.id === $modelsState.selectedModel,
      ) || null
    );
  },
);

export const isCustomModelSupported = derived(
  currentProvider,
  ($currentProvider) => $currentProvider?.supportsCustomModel || false,
);

export const effectiveModel = derived(
  [modelsState, currentModel, isCustomModelSupported],
  ([$modelsState, $currentModel, $isCustomModelSupported]) => {
    if ($isCustomModelSupported && $modelsState.customModel.trim()) {
      return {
        id: $modelsState.customModel.trim(),
        name: `Custom: ${$modelsState.customModel.trim()}`,
      };
    }
    return $currentModel;
  },
);

/**
 * Models actions
 */
export const modelsActions = {
  // Load model configuration from API
  async loadConfig(): Promise<void> {
    if (!browser) return;

    modelsState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const config = await apiClient.getModelConfig();

      modelsState.update((state) => {
        // Auto-select default provider and first model if none selected
        const selectedProvider =
          state.selectedProvider || config.defaultProvider;
        const provider = config.providers.find(
          (p: Provider) => p.id === selectedProvider,
        );
        const selectedModel =
          state.selectedModel || provider?.models[0]?.id || null;

        return {
          ...state,
          config,
          selectedProvider,
          selectedModel,
          isLoading: false,
          error: null,
          lastUpdated: Date.now(),
        };
      });

      // Save to localStorage
      modelsActions.saveToStorage();
    } catch (error) {
      console.error("Failed to load model config:", error);
      modelsState.update((state) => ({
        ...state,
        isLoading: false,
        error: error instanceof Error ? error.message : "Failed to load models",
      }));
    }
  },

  // Select provider
  setProvider(providerId: string): void {
    modelsState.update((state) => {
      const provider = state.config?.providers.find(
        (p: Provider) => p.id === providerId,
      );
      const firstModel = provider?.models[0]?.id || null;

      return {
        ...state,
        selectedProvider: providerId,
        selectedModel: firstModel,
        customModel: "", // Clear custom model when changing provider
      };
    });
    modelsActions.saveToStorage();
  },

  // Select model
  setModel(modelId: string): void {
    modelsState.update((state) => ({
      ...state,
      selectedModel: modelId,
      customModel: "", // Clear custom model when selecting a predefined model
    }));
    modelsActions.saveToStorage();
  },

  // Set custom model
  setCustomModel(customModel: string): void {
    modelsState.update((state) => ({
      ...state,
      customModel,
      selectedModel: null, // Clear selected model when using custom
    }));
    modelsActions.saveToStorage();
  },

  // Get current selection for API calls
  getCurrentSelection(): { provider: string | null; model: string | null } {
    const state = get(modelsState);
    const effective = get(effectiveModel);

    return {
      provider: state.selectedProvider,
      model: effective?.id || null,
    };
  },

  // Save state to localStorage
  saveToStorage(): void {
    if (!browser) return;

    const state = get(modelsState);
    const toSave = {
      selectedProvider: state.selectedProvider,
      selectedModel: state.selectedModel,
      customModel: state.customModel,
    };

    localStorage.setItem("grantha-models-state", JSON.stringify(toSave));
  },

  // Load state from localStorage
  loadFromStorage(): void {
    if (!browser) return;

    try {
      const saved = localStorage.getItem("grantha-models-state");
      if (saved) {
        const { selectedProvider, selectedModel, customModel } =
          JSON.parse(saved);
        modelsState.update((state) => ({
          ...state,
          selectedProvider: selectedProvider || state.selectedProvider,
          selectedModel: selectedModel || state.selectedModel,
          customModel: customModel || state.customModel,
        }));
      }
    } catch (error) {
      console.error("Failed to load models state from storage:", error);
    }
  },

  // Refresh configuration
  async refresh(): Promise<void> {
    await modelsActions.loadConfig();
  },

  // Clear error
  clearError(): void {
    modelsState.update((state) => ({ ...state, error: null }));
  },
};

// Load saved state and then refresh config on initialization
if (browser) {
  modelsActions.loadFromStorage();
  modelsActions.loadConfig();
}
