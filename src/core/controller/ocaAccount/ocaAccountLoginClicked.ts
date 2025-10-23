// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/ocaAccount/ocaAccountLoginClicked.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { EmptyRequest, String as ProtoString } from "@shared/proto/cline/common"
import { OcaAuthService } from "@/services/auth/oca/OcaAuthService"
import { Controller } from "../index"

/**
 * Handles the user clicking the login link in the UI.
 * Generates a secure nonce for state validation, stores it in secrets,
 * and opens the authentication URL in the external browser.
 *
 * @param controller The controller instance.
 * @returns The login URL as a string.
 */
export async function ocaAccountLoginClicked(_controller: Controller, _: EmptyRequest): Promise<ProtoString> {
	return await OcaAuthService.getInstance().createAuthRequest()
}
