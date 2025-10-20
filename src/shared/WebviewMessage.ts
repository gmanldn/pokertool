# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/WebviewMessage.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
export interface WebviewMessage {
    type: "grpc_request" | "grpc_request_cancel"
    grpc_request?: GrpcRequest
    grpc_request_cancel?: GrpcCancel
}

export type GrpcRequest = {
    service: string
    method: string
    message: any // JSON serialized protobuf message
    request_id: string // For correlating requests and responses
    is_streaming: boolean // Whether this is a streaming request
}

export type GrpcCancel = {
    request_id: string // ID of the request to cancel
}

export type ClineAskResponse = "yesButtonClicked" | "noButtonClicked" | "messageResponse"

export type ClineCheckpointRestore = "task" | "workspace" | "taskAndWorkspace"

export type TaskFeedbackType = "thumbs_up" | "thumbs_down"
