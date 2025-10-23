// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/hosts/vscode/hostbridge/window/showMessage.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { window } from "vscode"
import { SelectedResponse, ShowMessageRequest, ShowMessageType } from "@/shared/proto/index.host"

const DEFAULT_OPTIONS = { modal: false, items: [] } as const

export async function showMessage(request: ShowMessageRequest): Promise<SelectedResponse> {
	const { message, type, options } = request
	const { modal, detail, items } = { ...DEFAULT_OPTIONS, ...options }
	const option = { modal, detail }

	let selectedOption: string | undefined

	switch (type) {
		case ShowMessageType.ERROR:
			selectedOption = await window.showErrorMessage(message, option, ...items)
			break
		case ShowMessageType.WARNING:
			selectedOption = await window.showWarningMessage(message, option, ...items)
			break
		default:
			selectedOption = await window.showInformationMessage(message, option, ...items)
			break
	}

	return SelectedResponse.create({ selectedOption })
}
