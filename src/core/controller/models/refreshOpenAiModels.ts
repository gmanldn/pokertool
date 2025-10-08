# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/models/refreshOpenAiModels.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { StringArray } from "@shared/proto/cline/common"
import { OpenAiModelsRequest } from "@shared/proto/cline/models"
import type { AxiosRequestConfig } from "axios"
import axios from "axios"
import { Controller } from ".."

/**
 * Fetches available models from the OpenAI API
 * @param controller The controller instance
 * @param request Request containing the base URL and API key
 * @returns Array of model names
 */
export async function refreshOpenAiModels(_controller: Controller, request: OpenAiModelsRequest): Promise<StringArray> {
    try {
        if (!request.baseUrl) {
            return StringArray.create({ values: [] })
        }

        if (!URL.canParse(request.baseUrl)) {
            return StringArray.create({ values: [] })
        }

        const config: AxiosRequestConfig = {}
        if (request.apiKey) {
            config["headers"] = { Authorization: `Bearer ${request.apiKey}` }
        }

        const response = await axios.get(`${request.baseUrl}/models`, config)
        const modelsArray = response.data?.data?.map((model: any) => model.id) || []
        const models = [...new Set<string>(modelsArray)]

        return StringArray.create({ values: models })
    } catch (error) {
        console.error("Error fetching OpenAI models:", error)
        return StringArray.create({ values: [] })
    }
}
