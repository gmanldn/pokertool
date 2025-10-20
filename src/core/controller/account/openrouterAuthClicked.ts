# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/account/openrouterAuthClicked.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, EmptyRequest } from "@shared/proto/cline/common"
import { HostProvider } from "@/hosts/host-provider"
import { openExternal } from "@/utils/env"
import { Controller } from ".."

/**
 * Initiates OpenRouter auth
 */
export async function openrouterAuthClicked(_: Controller, __: EmptyRequest): Promise<Empty> {
    const callbackUrl = await HostProvider.get().getCallbackUrl()
    const authUrl = `https://openrouter.ai/auth?callback_url=${callbackUrl}/openrouter`

    await openExternal(authUrl)

    return {}
}
