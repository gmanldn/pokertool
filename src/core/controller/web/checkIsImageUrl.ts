# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/web/checkIsImageUrl.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { detectImageUrl } from "@integrations/misc/link-preview"
import { StringRequest } from "@shared/proto/cline/common"
import { IsImageUrl } from "@shared/proto/cline/web"
import { Controller } from "../index"

/**
 * Checks if a URL is an image URL
 * @param controller The controller instance
 * @param request The request containing the URL to check
 * @returns A result indicating if the URL is an image and the URL that was checked
 */
export async function checkIsImageUrl(_: Controller, request: StringRequest): Promise<IsImageUrl> {
	try {
		const url = request.value || ""
		// Check if the URL is an image
		const isImage = await detectImageUrl(url)

		return IsImageUrl.create({
			isImage,
			url,
		})
	} catch (error) {
		console.error(`Error checking if URL is an image: ${request.value}`, error)
		return IsImageUrl.create({
			isImage: false,
			url: request.value || "",
		})
	}
}
