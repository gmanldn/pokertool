# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/api/providers/types.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
// For the following openrouter error type sources, see the docs here:
// https://openrouter.ai/docs/api-reference/errors

export interface LanguageModelChatSelector {
    vendor?: string
    family?: string
    version?: string
    id?: string
}

export type OpenRouterErrorResponse = {
    error: {
        message: string
        code: number
        metadata?: OpenRouterProviderErrorMetadata | OpenRouterModerationErrorMetadata | Record<string, unknown>
    }
}

export type OpenRouterProviderErrorMetadata = {
    provider_name: string // The name of the provider that encountered the error
    raw: unknown // The raw error from the provider
}

export type OpenRouterModerationErrorMetadata = {
    reasons: string[] // Why your input was flagged
    flagged_input: string // The text segment that was flagged, limited to 100 characters. If the flagged input is longer than 100 characters, it will be truncated in the middle and replaced with ...
    provider_name: string // The name of the provider that requested moderation
    model_slug: string
}
