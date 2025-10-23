// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/account/getRedirectUrl.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { EmptyRequest, String } from "@shared/proto/cline/common"
import { HostProvider } from "@/hosts/host-provider"
import { Controller } from "../index"

/**
 * Constructs and returns a URL that will redirect to the user's IDE.
 */
export async function getRedirectUrl(_controller: Controller, _: EmptyRequest): Promise<String> {
	const url = (await HostProvider.env.getIdeRedirectUri({})).value
	return { value: url }
}
