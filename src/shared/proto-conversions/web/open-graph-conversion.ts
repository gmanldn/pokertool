# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/proto-conversions/web/open-graph-conversion.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { OpenGraphData as DomainOpenGraphData } from "@integrations/misc/link-preview"
import { OpenGraphData as ProtoOpenGraphData } from "@shared/proto/cline/web"

/**
 * Converts domain OpenGraphData objects to proto OpenGraphData objects
 * @param ogData Domain OpenGraphData object
 * @returns Proto OpenGraphData object
 */
export function convertDomainOpenGraphDataToProto(ogData: DomainOpenGraphData): ProtoOpenGraphData {
    return ProtoOpenGraphData.create({
        title: ogData.title || "",
        description: ogData.description || "",
        image: ogData.image || "",
        url: ogData.url || "",
        siteName: ogData.siteName || "",
        type: ogData.type || "",
    })
}
