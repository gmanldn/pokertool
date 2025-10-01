# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/api/baseTypes.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { LanguageModelChatSelector } from "@core/api/providers/types"

export type ApiProvider =
	| "anthropic"
	| "claude-code"
	| "openrouter"
	| "bedrock"
	| "vertex"
	| "openai"
	| "ollama"
	| "lmstudio"
	| "gemini"
	| "openai-native"
	| "requesty"
	| "together"
	| "deepseek"
	| "qwen"
	| "qwen-code"
	| "doubao"
	| "mistral"
	| "vscode-lm"
	| "cline"
	| "litellm"
	| "moonshot"
	| "nebius"
	| "fireworks"
	| "asksage"
	| "xai"
	| "sambanova"
	| "cerebras"
	| "sapaicore"
	| "groq"
	| "huggingface"
	| "huawei-cloud-maas"
	| "dify"
	| "baseten"
	| "vercel-ai-gateway"
	| "zai"
	| "oca"

export interface ApiHandlerSecrets {
	apiKey?: string // anthropic
	liteLlmApiKey?: string
	awsAccessKey?: string
	awsSecretKey?: string
	openRouterApiKey?: string

	clineAccountId?: string
	awsSessionToken?: string
	awsBedrockApiKey?: string
	openAiApiKey?: string
	geminiApiKey?: string
	openAiNativeApiKey?: string
	ollamaApiKey?: string
	deepSeekApiKey?: string
	requestyApiKey?: string
	togetherApiKey?: string
	fireworksApiKey?: string
	qwenApiKey?: string
	doubaoApiKey?: string
	mistralApiKey?: string
	authNonce?: string
	asksageApiKey?: string
	xaiApiKey?: string
	moonshotApiKey?: string
	zaiApiKey?: string
	huggingFaceApiKey?: string
	nebiusApiKey?: string
	sambanovaApiKey?: string
	cerebrasApiKey?: string
	sapAiCoreClientId?: string
	sapAiCoreClientSecret?: string
	groqApiKey?: string
	huaweiCloudMaasApiKey?: string
	basetenApiKey?: string
	vercelAiGatewayApiKey?: string
	difyApiKey?: string
}

export interface ApiHandlerOptions {
	// Global configuration (not mode-specific)
	ulid?: string // Used to identify the task in API requests
	liteLlmBaseUrl?: string
	liteLlmUsePromptCache?: boolean
	openAiHeaders?: Record<string, string> // Custom headers for OpenAI requests
	anthropicBaseUrl?: string
	openRouterProviderSorting?: string
	awsRegion?: string
	awsUseCrossRegionInference?: boolean
	awsBedrockUsePromptCache?: boolean
	awsAuthentication?: string
	awsUseProfile?: boolean
	awsProfile?: string
	awsBedrockEndpoint?: string
	claudeCodePath?: string
	vertexProjectId?: string
	vertexRegion?: string
	openAiBaseUrl?: string
	ollamaBaseUrl?: string
	ollamaApiOptionsCtxNum?: string
	lmStudioBaseUrl?: string
	lmStudioModelId?: string
	lmStudioMaxTokens?: string
	geminiBaseUrl?: string
	requestyBaseUrl?: string
	fireworksModelMaxCompletionTokens?: number
	fireworksModelMaxTokens?: number
	qwenCodeOauthPath?: string
	azureApiVersion?: string
	qwenApiLine?: string
	moonshotApiLine?: string
	asksageApiUrl?: string
	requestTimeoutMs?: number
	sapAiResourceGroup?: string
	sapAiCoreTokenUrl?: string
	sapAiCoreBaseUrl?: string
	sapAiCoreUseOrchestrationMode?: boolean
	difyBaseUrl?: string
	zaiApiLine?: string
	onRetryAttempt?: (attempt: number, maxRetries: number, delay: number, error: any) => void
	ocaBaseUrl?: string

	// Plan mode configurations
	planModeApiModelId?: string
	planModeThinkingBudgetTokens?: number
	planModeReasoningEffort?: string
	planModeVsCodeLmModelSelector?: LanguageModelChatSelector
	planModeAwsBedrockCustomSelected?: boolean
	planModeAwsBedrockCustomModelBaseId?: string
	planModeOpenRouterModelId?: string
	planModeOpenRouterModelInfo?: ModelInfo
	planModeOpenAiModelId?: string
	planModeOpenAiModelInfo?: OpenAiCompatibleModelInfo
	planModeOllamaModelId?: string
	planModeLmStudioModelId?: string
	planModeLiteLlmModelId?: string
	planModeLiteLlmModelInfo?: LiteLLMModelInfo
	planModeRequestyModelId?: string
	planModeRequestyModelInfo?: ModelInfo
	planModeTogetherModelId?: string
	planModeFireworksModelId?: string
	planModeSapAiCoreModelId?: string
	planModeSapAiCoreDeploymentId?: string
	planModeGroqModelId?: string
	planModeGroqModelInfo?: ModelInfo
	planModeBasetenModelId?: string
	planModeBasetenModelInfo?: ModelInfo
	planModeHuggingFaceModelId?: string
	planModeHuggingFaceModelInfo?: ModelInfo
	planModeHuaweiCloudMaasModelId?: string
	planModeHuaweiCloudMaasModelInfo?: ModelInfo
	planModeVercelAiGatewayModelId?: string
	planModeVercelAiGatewayModelInfo?: ModelInfo
	planModeOcaModelId?: string
	planModeOcaModelInfo?: OcaModelInfo
	// Act mode configurations

	// Act mode configurations
	actModeApiModelId?: string
	actModeThinkingBudgetTokens?: number
	actModeReasoningEffort?: string
	actModeVsCodeLmModelSelector?: LanguageModelChatSelector
	actModeAwsBedrockCustomSelected?: boolean
	actModeAwsBedrockCustomModelBaseId?: string
	actModeOpenRouterModelId?: string
	actModeOpenRouterModelInfo?: ModelInfo
	actModeOpenAiModelId?: string
	actModeOpenAiModelInfo?: OpenAiCompatibleModelInfo
	actModeOllamaModelId?: string
	actModeLmStudioModelId?: string
	actModeLiteLlmModelId?: string
	actModeLiteLlmModelInfo?: LiteLLMModelInfo
	actModeRequestyModelId?: string
	actModeRequestyModelInfo?: ModelInfo
	actModeTogetherModelId?: string
	actModeFireworksModelId?: string
	actModeSapAiCoreModelId?: string
	actModeSapAiCoreDeploymentId?: string
	actModeGroqModelId?: string
	actModeGroqModelInfo?: ModelInfo
	actModeBasetenModelId?: string
	actModeBasetenModelInfo?: ModelInfo
	actModeHuggingFaceModelId?: string
	actModeHuggingFaceModelInfo?: ModelInfo
	actModeHuaweiCloudMaasModelId?: string
	actModeHuaweiCloudMaasModelInfo?: ModelInfo
	actModeVercelAiGatewayModelId?: string
	actModeVercelAiGatewayModelInfo?: ModelInfo
	actModeOcaModelId?: string
	actModeOcaModelInfo?: OcaModelInfo
}

export type ApiConfiguration = ApiHandlerOptions &
	ApiHandlerSecrets & {
		planModeApiProvider?: ApiProvider
		actModeApiProvider?: ApiProvider
	}

interface PriceTier {
	tokenLimit: number // Upper limit (inclusive) of *input* tokens for this price. Use Infinity for the highest tier.
	price: number // Price per million tokens for this tier.
}

export interface ModelInfo {
	maxTokens?: number
	contextWindow?: number
	supportsImages?: boolean
	supportsPromptCache: boolean // this value is hardcoded for now
	inputPrice?: number // Keep for non-tiered input models
	outputPrice?: number // Keep for non-tiered output models
	thinkingConfig?: {
		maxBudget?: number // Max allowed thinking budget tokens
		outputPrice?: number // Output price per million tokens when budget > 0
		outputPriceTiers?: PriceTier[] // Optional: Tiered output price when budget > 0
	}
	supportsGlobalEndpoint?: boolean // Whether the model supports a global endpoint with Vertex AI
	cacheWritesPrice?: number
	cacheReadsPrice?: number
	description?: string
	tiers?: {
		contextWindow: number
		inputPrice?: number
		outputPrice?: number
		cacheWritesPrice?: number
		cacheReadsPrice?: number
	}[]
}

export interface OpenAiCompatibleModelInfo extends ModelInfo {
	temperature?: number
	isR1FormatRequired?: boolean
}

export interface OcaModelInfo extends OpenAiCompatibleModelInfo {
	modelName: string
	surveyId?: string
	banner?: string
	surveyContent?: string
}

export interface LiteLLMModelInfo extends ModelInfo {
	temperature?: number
}
