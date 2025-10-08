# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/file/ifFileExistsRelativePath.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { workspaceResolver } from "@core/workspace"
import { BooleanResponse, StringRequest } from "@shared/proto/cline/common"
import { getWorkspacePath } from "@utils/path"
import * as fs from "fs"
import { Controller } from ".."

/**
 * Check if a file exists in the project using a relative path
 * @param controller The controller instance
 * @param request The request containing the relative file path to check
 * @returns BooleanResponse indicating whether the file exists
 */
export async function ifFileExistsRelativePath(_controller: Controller, request: StringRequest): Promise<BooleanResponse> {
	const workspacePath = await getWorkspacePath()

	if (!workspacePath) {
		// If no workspace is open, return false
		console.error("Error in ifFileExistsRelativePath: No workspace path available") // TODO
		return BooleanResponse.create({ value: false })
	}

	if (!request.value) {
		// If no path provided, return false
		return BooleanResponse.create({ value: false })
	}

	// Resolve the relative path to absolute path
	const resolvedPath = workspaceResolver.resolveWorkspacePath(
		workspacePath,
		request.value,
		"Controller.ifFileExistsRelativePath",
	)
	const absolutePath = typeof resolvedPath === "string" ? resolvedPath : resolvedPath.absolutePath
	// Check if the file exists
	try {
		return BooleanResponse.create({ value: fs.statSync(absolutePath).isFile() })
	} catch {
		return BooleanResponse.create({ value: false })
	}
}
