# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/state/updateTelemetrySetting.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty } from "@shared/proto/cline/common"
import { TelemetrySettingRequest } from "@shared/proto/cline/state"
import { convertProtoTelemetrySettingToDomain } from "../../../shared/proto-conversions/state/telemetry-setting-conversion"
import { Controller } from ".."

/**
 * Updates the telemetry setting
 * @param controller The controller instance
 * @param request The telemetry setting request
 * @returns Empty response
 */
export async function updateTelemetrySetting(controller: Controller, request: TelemetrySettingRequest): Promise<Empty> {
    const telemetrySetting = convertProtoTelemetrySettingToDomain(request.setting)
    await controller.updateTelemetrySetting(telemetrySetting)
    return Empty.create()
}
