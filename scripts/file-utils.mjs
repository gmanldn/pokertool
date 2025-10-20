# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: scripts/file-utils.mjs
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import * as fs from "fs/promises"
import * as path from "path"
/**
 * Write `contents` to `filePath`, creating any necessary directories in `filePath`.
 */
export async function writeFileWithMkdirs(filePath, content) {
	await fs.mkdir(path.dirname(filePath), { recursive: true })
	await fs.writeFile(filePath, content)
}

export async function rmrf(path) {
	await fs.rm(path, { force: true, recursive: true })
}

/**
 * Remove an empty dir, do nothing if the directory doesn't exist or is not empty.
 */
export async function rmdir(path) {
	try {
		await fs.rmdir(path)
	} catch (error) {
		if (error.code !== "ENOTEMPTY" && error.code !== "ENOENT") {
			// Only re-throw if it's not "not empty" or "doesn't exist"
			throw error
		}
	}
}
