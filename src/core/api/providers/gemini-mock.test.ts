# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/api/providers/gemini-mock.test.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
// Mock for @google/genai module to avoid ESM compatibility issues in tests

export class GoogleGenAI {
	constructor(_options: any) {
		// Mock constructor
	}

	models = {
		generateContentStream: async (_params: any) => {
			// Mock implementation that returns an async iterator
			return {
				async *[Symbol.asyncIterator]() {
					yield {
						text: "Mock response",
						candidates: [],
						usageMetadata: {
							promptTokenCount: 100,
							candidatesTokenCount: 50,
							thoughtsTokenCount: 0,
							cachedContentTokenCount: 0,
						},
					}
				},
			}
		},
		countTokens: async (_params: any) => {
			// Mock token counting
			return {
				totalTokens: 100,
			}
		},
	}
}

// Export mock types
export interface GenerateContentConfig {
	httpOptions?: any
	systemInstruction?: string
	temperature?: number
	thinkingConfig?: any
}

export interface GenerateContentResponseUsageMetadata {
	promptTokenCount?: number
	candidatesTokenCount?: number
	thoughtsTokenCount?: number
	cachedContentTokenCount?: number
}

export interface Part {
	thought?: boolean
	text?: string
}
