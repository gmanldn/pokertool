# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/services/feature-flags/feature-flags.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
export enum FeatureFlag {
    CUSTOM_INSTRUCTIONS = "custom-instructions",
    DEV_ENV_POSTHOG = "dev-env-posthog",
    FOCUS_CHAIN_CHECKLIST = "focus_chain_checklist",
    MULTI_ROOT_WORKSPACE = "multi_root_workspace",
}

export const FEATURE_FLAGS = Object.values(FeatureFlag)
