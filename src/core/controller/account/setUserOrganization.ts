// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/account/setUserOrganization.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { UserOrganizationUpdateRequest } from "@shared/proto/cline/account"
import { Empty } from "@shared/proto/cline/common"
import type { Controller } from "../index"

/**
 * Handles setting the user's active organization
 * @param controller The controller instance
 * @param request UserOrganization to set as active
 * @returns Empty response
 */
export async function setUserOrganization(controller: Controller, request: UserOrganizationUpdateRequest): Promise<Empty> {
	try {
		if (!controller.accountService) {
			throw new Error("Account service not available")
		}

		// Switch to the specified organization using the account service
		await controller.accountService.switchAccount(request.organizationId)

		return Empty.create({})
	} catch (error) {
		throw error
	}
}
