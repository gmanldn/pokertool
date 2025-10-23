// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/api/providers/mistral.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import type { ModelInfo } from "../baseTypes"

// Mistral
// https://docs.mistral.ai/getting-started/models/models_overview/
export type MistralModelId = keyof typeof mistralModels
export const mistralDefaultModelId: MistralModelId = "devstral-small-2505"
export const mistralModels = {
    "mistral-large-2411": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 2.0,
        outputPrice: 6.0,
    },
    "pixtral-large-2411": {
        maxTokens: 131_000,
        contextWindow: 131_000,
        supportsImages: true,
        supportsPromptCache: false,
        inputPrice: 2.0,
        outputPrice: 6.0,
    },
    "ministral-3b-2410": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.04,
        outputPrice: 0.04,
    },
    "ministral-8b-2410": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.1,
        outputPrice: 0.1,
    },
    "mistral-small-latest": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: true,
        supportsPromptCache: false,
        inputPrice: 0.1,
        outputPrice: 0.3,
    },
    "mistral-medium-latest": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: true,
        supportsPromptCache: false,
        inputPrice: 0.4,
        outputPrice: 2.0,
    },
    "mistral-small-2501": {
        maxTokens: 32_000,
        contextWindow: 32_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.1,
        outputPrice: 0.3,
    },
    "pixtral-12b-2409": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: true,
        supportsPromptCache: false,
        inputPrice: 0.15,
        outputPrice: 0.15,
    },
    "open-mistral-nemo-2407": {
        maxTokens: 128_000,
        contextWindow: 128_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.15,
        outputPrice: 0.15,
    },
    "open-codestral-mamba": {
        maxTokens: 256_000,
        contextWindow: 256_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.15,
        outputPrice: 0.15,
    },
    "codestral-2501": {
        maxTokens: 256_000,
        contextWindow: 256_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.3,
        outputPrice: 0.9,
    },
    "devstral-small-2505": {
        maxTokens: 128_000,
        contextWindow: 131_072,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.1,
        outputPrice: 0.3,
    },
    "devstral-medium-latest": {
        maxTokens: 128_000,
        contextWindow: 131_072,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.4,
        outputPrice: 2.0,
    },
} as const satisfies Record<string, ModelInfo>
