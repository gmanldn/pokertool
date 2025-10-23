// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/FocusChainSettings.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
export interface FocusChainSettings {
    // Enable/disable the focus chain feature
    enabled: boolean
    // Interval (in messages) to remind Cline about focus chain
    remindClineInterval: number
}

export const DEFAULT_FOCUS_CHAIN_SETTINGS: FocusChainSettings = {
    enabled: true,
    remindClineInterval: 6,
}
