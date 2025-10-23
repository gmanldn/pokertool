// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/prompts/system-prompt/spec.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import type { ModelFamily } from "@/shared/prompts"
import type { ClineDefaultTool } from "@/shared/tools"
import type { SystemPromptContext } from "./types"

export interface ClineToolSpec {
    variant: ModelFamily
    id: ClineDefaultTool
    name: string
    description: string
    instruction?: string
    contextRequirements?: (context: SystemPromptContext) => boolean
    parameters?: Array<ClineToolSpecParameter>
}

interface ClineToolSpecParameter {
    name: string
    required: boolean
    instruction: string
    usage?: string
    dependencies?: ClineDefaultTool[]
    description?: string
    contextRequirements?: (context: SystemPromptContext) => boolean
}
