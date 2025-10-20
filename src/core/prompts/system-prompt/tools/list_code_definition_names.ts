# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/prompts/system-prompt/tools/list_code_definition_names.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { ModelFamily } from "@/shared/prompts"
import { ClineDefaultTool } from "@/shared/tools"
import type { ClineToolSpec } from "../spec"
import { TASK_PROGRESS_PARAMETER } from "../types"

const id = ClineDefaultTool.LIST_CODE_DEF

const generic: ClineToolSpec = {
    variant: ModelFamily.GENERIC,
    id,
    name: "list_code_definition_names",
    description:
        "Request to list definition names (classes, functions, methods, etc.) used in source code files at the top level of the specified directory. This tool provides insights into the codebase structure and important constructs, encapsulating high-level concepts and relationships that are crucial for understanding the overall architecture.",
    parameters: [
        {
            name: "path",
            required: true,
            instruction: `The path of the directory (relative to the current working directory {{CWD}}){{MULTI_ROOT_HINT}} to list top level source code definitions for.`,
            usage: "Directory path here",
        },
        TASK_PROGRESS_PARAMETER,
    ],
}

export const list_code_definition_names_variants = [generic]
