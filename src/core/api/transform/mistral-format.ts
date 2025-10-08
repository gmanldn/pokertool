# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/api/transform/mistral-format.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Anthropic } from "@anthropic-ai/sdk"
import { AssistantMessage } from "@mistralai/mistralai/models/components/assistantmessage"
import { SystemMessage } from "@mistralai/mistralai/models/components/systemmessage"
import { ToolMessage } from "@mistralai/mistralai/models/components/toolmessage"
import { UserMessage } from "@mistralai/mistralai/models/components/usermessage"

export type MistralMessage =
    | (SystemMessage & { role: "system" })
    | (UserMessage & { role: "user" })
    | (AssistantMessage & { role: "assistant" })
    | (ToolMessage & { role: "tool" })

export function convertToMistralMessages(anthropicMessages: Anthropic.Messages.MessageParam[]): MistralMessage[] {
    const mistralMessages: MistralMessage[] = []
    for (const anthropicMessage of anthropicMessages) {
        if (typeof anthropicMessage.content === "string") {
            mistralMessages.push({
                role: anthropicMessage.role,
                content: anthropicMessage.content,
            })
        } else {
            if (anthropicMessage.role === "user") {
                // Filter to only include text and image blocks
                const textAndImageBlocks = anthropicMessage.content.filter(
                    (part) => part.type === "text" || part.type === "image",
                )

                if (textAndImageBlocks.length > 0) {
                    mistralMessages.push({
                        role: "user",
                        content: textAndImageBlocks.map((part) => {
                            if (part.type === "image") {
                                return {
                                    type: "image_url",
                                    imageUrl: {
                                        url: `data:${part.source.media_type};base64,${part.source.data}`,
                                    },
                                }
                            }
                            return { type: "text", text: part.text }
                        }),
                    })
                }
            } else if (anthropicMessage.role === "assistant") {
                // Only process text blocks - assistant cannot send images or other content types in Mistral's API format
                const textBlocks = anthropicMessage.content.filter((part) => part.type === "text")

                if (textBlocks.length > 0) {
                    const content = textBlocks.map((part) => part.text).join("\n")

                    mistralMessages.push({
                        role: "assistant",
                        content,
                    })
                }
            }
        }
    }

    return mistralMessages
}
