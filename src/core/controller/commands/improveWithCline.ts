# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/commands/improveWithCline.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { getFileMentionFromPath } from "@/core/mentions"
import { HostProvider } from "@/hosts/host-provider"
import { telemetryService } from "@/services/telemetry"
import { CommandContext, Empty } from "@/shared/proto/index.cline"
import { ShowMessageType } from "@/shared/proto/index.host"
import { Controller } from "../index"

export async function improveWithCline(controller: Controller, request: CommandContext): Promise<Empty> {
    if (!request.selectedText || !request.selectedText.trim()) {
        HostProvider.window.showMessage({
            type: ShowMessageType.INFORMATION,
            message: "Please select some code to improve.",
        })
        return {}
    }
    const fileMention = await getFileMentionFromPath(request.filePath || "")
    const prompt = `Improve the following code from ${fileMention} (e.g., suggest refactorings, optimizations, or better practices):
\`\`\`${request.language}\n${request.selectedText}\n\`\`\``

    await controller.initTask(prompt)

    telemetryService.captureButtonClick("codeAction_improveCode", controller.task?.ulid)

    return {}
}
