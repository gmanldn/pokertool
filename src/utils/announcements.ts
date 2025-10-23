// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/utils/announcements.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { ExtensionRegistryInfo } from "@/registry"

/**
 * Gets the latest announcement ID based on the extension version
 * Uses major.minor version format (e.g., "1.2" from "1.2.3")
 *
 * @param context The VSCode extension context
 * @returns The announcement ID string (major.minor version) or empty string if unavailable
 */
export function getLatestAnnouncementId(): string {
    const version = ExtensionRegistryInfo.version
    return version.split(".").slice(0, 2).join(".")
}
