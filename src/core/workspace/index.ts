// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/workspace/index.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
/**
 * Workspace module exports for multi-workspace support
 */

// Export workspace path parsing utilities
export type { ParsedWorkspacePath } from "./utils/parseWorkspaceInlinePath"
export {
    addWorkspaceHint,
    hasWorkspaceHint,
    parseMultipleWorkspacePaths,
    parseWorkspaceInlinePath,
    removeWorkspaceHint,
} from "./utils/parseWorkspaceInlinePath"
export type { WorkspaceAdapterConfig } from "./WorkspacePathAdapter"
export { createWorkspacePathAdapter, WorkspacePathAdapter } from "./WorkspacePathAdapter"
export {
    getWorkspaceBasename,
    isWorkspaceTraceEnabled,
    resolveWorkspacePath,
    WorkspaceResolver,
    workspaceResolver,
} from "./WorkspaceResolver"
export type { WorkspaceRoot } from "./WorkspaceRoot"
export { VcsType } from "./WorkspaceRoot"
export type { WorkspaceContext } from "./WorkspaceRootManager"
export { createLegacyWorkspaceRoot, WorkspaceRootManager } from "./WorkspaceRootManager"

// Re-export convenience function at module level for easier imports
// Usage: import { resolveWorkspacePath } from "@core/workspace"
