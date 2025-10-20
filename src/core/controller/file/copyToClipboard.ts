# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/file/copyToClipboard.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { writeTextToClipboard } from "@/utils/env"
import { Controller } from ".."

/**
 * Copies text to the system clipboard
 * @param controller The controller instance
 * @param request The request containing the text to copy
 * @returns Empty response
 */
export async function copyToClipboard(_controller: Controller, request: StringRequest): Promise<Empty> {
    try {
        if (request.value) {
            await writeTextToClipboard(request.value)
        }
    } catch (error) {
        console.error("Error copying to clipboard:", error)
    }
    return Empty.create()
}
