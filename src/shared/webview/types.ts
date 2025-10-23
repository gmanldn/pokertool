// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/webview/types.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
export enum WebviewProviderType {
    SIDEBAR = "sidebar",
    TAB = "tab",
}

declare global {
    interface Window {
        WEBVIEW_PROVIDER_TYPE?: WebviewProviderType
    }
}
