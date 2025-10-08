# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/proto-conversions/file/search-result-conversion.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { FileInfo } from "@shared/proto/cline/file"

/**
 * Converts domain search result objects to proto FileInfo objects
 */
export function convertSearchResultsToProtoFileInfos(
	results: { path: string; type: "file" | "folder"; label?: string }[],
): FileInfo[] {
	return results.map((result) => ({
		path: result.path,
		type: result.type,
		label: result.label,
	}))
}

/**
 * Converts proto FileInfo objects to domain search result objects
 */
export function convertProtoFileInfosToSearchResults(
	protoResults: FileInfo[],
): { path: string; type: "file" | "folder"; label?: string }[] {
	return protoResults.map((protoResult) => ({
		path: protoResult.path,
		type: protoResult.type as "file" | "folder",
		label: protoResult.label,
	}))
}
