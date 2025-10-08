# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/api/providers/anthropic.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { ModelInfo } from "../baseTypes"

export const CLAUDE_SONNET_4_1M_SUFFIX = ":1m"
export const CLAUDE_SONNET_4_1M_TIERS = [
    {
        contextWindow: 200000,
        inputPrice: 3.0,
        outputPrice: 15,
        cacheWritesPrice: 3.75,
        cacheReadsPrice: 0.3,
    },
    {
        contextWindow: Number.MAX_SAFE_INTEGER, // storing infinity in vs storage is not possible, it converts to 'null', which causes crash in webview ModelInfoView
        inputPrice: 6,
        outputPrice: 22.5,
        cacheWritesPrice: 7.5,
        cacheReadsPrice: 0.6,
    },
]

// Anthropic
// https://docs.anthropic.com/en/docs/about-claude/models // prices updated 2025-01-02
export type AnthropicModelId = keyof typeof anthropicModels
export const anthropicDefaultModelId: AnthropicModelId = "claude-sonnet-4-20250514"
export const anthropicModels = {
    "claude-sonnet-4-20250514:1m": {
        maxTokens: 8192,
        contextWindow: 1_000_000,
        supportsImages: true,
        supportsPromptCache: true,
        inputPrice: 3.0,
        outputPrice: 15.0,
        cacheWritesPrice: 3.75,
        cacheReadsPrice: 0.3,
        tiers: CLAUDE_SONNET_4_1M_TIERS,
    },
    "claude-sonnet-4-20250514": {
        maxTokens: 8192,
        contextWindow: 200_000,
        supportsImages: true,

        supportsPromptCache: true,
        inputPrice: 3.0,
        outputPrice: 15.0,
        cacheWritesPrice: 3.75,
        cacheReadsPrice: 0.3,
    },
    "claude-opus-4-1-20250805": {
        maxTokens: 8192,
        contextWindow: 200_000,
        supportsImages: true,
        supportsPromptCache: true,
        inputPrice: 15.0,
        outputPrice: 75.0,
        cacheWritesPrice: 18.75,
        cacheReadsPrice: 1.5,
    },
    "claude-opus-4-20250514": {
        maxTokens: 8192,
        contextWindow: 200_000,
        supportsImages: true,
        supportsPromptCache: true,
        inputPrice: 15.0,
        outputPrice: 75.0,
        cacheWritesPrice: 18.75,
        cacheReadsPrice: 1.5,
    },
    "claude-3-7-sonnet-20250219": {
        maxTokens: 8192,
        contextWindow: 200_000,
        supportsImages: true,

        supportsPromptCache: true,
        inputPrice: 3.0,
        outputPrice: 15.0,
        cacheWritesPrice: 3.75,
        cacheReadsPrice: 0.3,
    },
    "claude-3-5-sonnet-20241022": {
        maxTokens: 8192,
        contextWindow: 200_000,
        supportsImages: true,

        supportsPromptCache: true,
        inputPrice: 3.0, // $3 per million input tokens
        outputPrice: 15.0, // $15 per million output tokens
        cacheWritesPrice: 3.75, // $3.75 per million tokens
        cacheReadsPrice: 0.3, // $0.30 per million tokens
    },
    "claude-3-5-haiku-20241022": {
        maxTokens: 8192,
        contextWindow: 200_000,
        supportsImages: false,
        supportsPromptCache: true,
        inputPrice: 0.8,
        outputPrice: 4.0,
        cacheWritesPrice: 1.0,
        cacheReadsPrice: 0.08,
    },
    "claude-3-opus-20240229": {
        maxTokens: 4096,
        contextWindow: 200_000,
        supportsImages: true,
        supportsPromptCache: true,
        inputPrice: 15.0,
        outputPrice: 75.0,
        cacheWritesPrice: 18.75,
        cacheReadsPrice: 1.5,
    },
    "claude-3-haiku-20240307": {
        maxTokens: 4096,
        contextWindow: 200_000,
        supportsImages: true,
        supportsPromptCache: true,
        inputPrice: 0.25,
        outputPrice: 1.25,
        cacheWritesPrice: 0.3,
        cacheReadsPrice: 0.03,
    },
} as const satisfies Record<string, ModelInfo>
