// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/api/providers/doubao.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import type { ModelInfo } from "../baseTypes"

// Doubao
// https://www.volcengine.com/docs/82379/1298459
// https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement
export type DoubaoModelId = keyof typeof doubaoModels
export const doubaoDefaultModelId: DoubaoModelId = "doubao-1-5-pro-256k-250115"
export const doubaoModels = {
    "doubao-1-5-pro-256k-250115": {
        maxTokens: 12_288,
        contextWindow: 256_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.7,
        outputPrice: 1.3,
        cacheWritesPrice: 0,
        cacheReadsPrice: 0,
    },
    "doubao-1-5-pro-32k-250115": {
        maxTokens: 12_288,
        contextWindow: 32_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.11,
        outputPrice: 0.3,
        cacheWritesPrice: 0,
        cacheReadsPrice: 0,
    },
    "deepseek-v3-250324": {
        maxTokens: 12_288,
        contextWindow: 128_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.55,
        outputPrice: 2.19,
        cacheWritesPrice: 0,
        cacheReadsPrice: 0,
    },
    "deepseek-r1-250120": {
        maxTokens: 32_768,
        contextWindow: 64_000,
        supportsImages: false,
        supportsPromptCache: false,
        inputPrice: 0.27,
        outputPrice: 1.09,
        cacheWritesPrice: 0,
        cacheReadsPrice: 0,
    },
} as const satisfies Record<string, ModelInfo>
