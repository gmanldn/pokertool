# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/integrations/misc/open-file.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { writeFile } from "@utils/fs"
import * as os from "os"
import * as path from "path"
import { HostProvider } from "@/hosts/host-provider"
import { ShowMessageType } from "@/shared/proto/host/window"

export async function openImage(dataUri: string) {
    const matches = dataUri.match(/^data:image\/([a-zA-Z]+);base64,(.+)$/)
    if (!matches) {
        HostProvider.window.showMessage({
            type: ShowMessageType.ERROR,
            message: "Invalid data URI format",
        })
        return
    }
    const [, format, base64Data] = matches
    const imageBuffer = Buffer.from(base64Data, "base64")
    const tempFilePath = path.join(os.tmpdir(), `temp_image_${Date.now()}.${format}`)
    try {
        await writeFile(tempFilePath, new Uint8Array(imageBuffer))
        await HostProvider.window.openFile({
            filePath: tempFilePath,
        })
    } catch (error) {
        HostProvider.window.showMessage({
            type: ShowMessageType.ERROR,
            message: `Error opening image: ${error}`,
        })
    }
}

export async function openFile(absolutePath: string, preserveFocus: boolean = false, preview: boolean = false) {
    try {
        await HostProvider.window.showTextDocument({
            path: absolutePath,
            options: { preserveFocus, preview },
        })
    } catch (_error) {
        HostProvider.window.showMessage({
            type: ShowMessageType.ERROR,
            message: `Could not open file!`,
        })
    }
}
