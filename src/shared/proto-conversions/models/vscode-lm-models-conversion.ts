// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/proto-conversions/models/vscode-lm-models-conversion.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { LanguageModelChatSelector } from "@shared/proto/cline/models"

/**
 * Represents a VS Code language model in the native VS Code format
 */
export interface VsCodeNativeModel {
    vendor?: string
    family?: string
    version?: string
    id?: string
}

/**
 * Converts VS Code native model format to protobuf format
 */
export function convertVsCodeNativeModelsToProtoModels(models: VsCodeNativeModel[]): LanguageModelChatSelector[] {
    return (models || []).map((model) => ({
        vendor: model.vendor || "",
        family: model.family || "",
        version: model.version || "",
        id: model.id || "",
    }))
}
