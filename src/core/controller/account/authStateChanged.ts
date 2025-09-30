# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/account/authStateChanged.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { AuthState, AuthStateChangedRequest } from "@shared/proto/cline/account"
import type { Controller } from "../index"

/**
 * Handles authentication state changes from the Firebase context.
 * Updates the user info in global state and returns the updated value.
 * @param controller The controller instance
 * @param request The auth state change request
 * @returns The updated user info
 */
export async function authStateChanged(controller: Controller, request: AuthStateChangedRequest): Promise<AuthState> {
	try {
		// Store the user info directly in global state
		controller.stateManager.setGlobalState("userInfo", request.user)

		// Return the same user info
		return AuthState.create({ user: request.user })
	} catch (error) {
		console.error(`Failed to update auth state: ${error}`)
		throw error
	}
}
