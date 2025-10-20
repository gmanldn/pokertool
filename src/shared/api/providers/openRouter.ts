# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/api/providers/openRouter.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { ModelInfo } from "../baseTypes"
import { CLAUDE_SONNET_4_1M_SUFFIX } from "./anthropic"

// OpenRouter
// https://openrouter.ai/models?order=newest&supported_parameters=tools
export const openRouterDefaultModelId = "anthropic/claude-sonnet-4" // will always exist in openRouterModels
export const openRouterClaudeSonnet41mModelId = `anthropic/claude-sonnet-4${CLAUDE_SONNET_4_1M_SUFFIX}`
export const openRouterDefaultModelInfo: ModelInfo = {
    maxTokens: 8192,
    contextWindow: 200_000,
    supportsImages: true,
    supportsPromptCache: true,
    inputPrice: 3.0,
    outputPrice: 15.0,
    cacheWritesPrice: 3.75,
    cacheReadsPrice: 0.3,
    description:
        "Claude Sonnet 4 delivers superior intelligence across coding, agentic search, and AI agent capabilities. It's a powerful choice for agentic coding, and can complete tasks across the entire software development lifecycle—from initial planning to bug fixes, maintenance to large refactors. It offers strong performance in both planning and solving for complex coding tasks, making it an ideal choice to power end-to-end software development processes.\n\nRead more in the [blog post here](https://www.anthropic.com/claude/sonnet)",
}

// Cline custom model - code-supernova
export const clineCodeSupernovaModelInfo: ModelInfo = {
    contextWindow: 200000,
    supportsImages: true,
    supportsPromptCache: true,
    inputPrice: 0,
    outputPrice: 0,
    cacheReadsPrice: 0,
    cacheWritesPrice: 0,
    description: "A versatile agentic coding stealth model that supports image inputs.",
}
