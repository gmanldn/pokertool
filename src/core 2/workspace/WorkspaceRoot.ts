# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/workspace/WorkspaceRoot.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
/**
 * Workspace root types and interfaces for multi-workspace support
 */

export enum VcsType {
	None = "none",
	Git = "git",
	Mercurial = "mercurial",
}

export interface WorkspaceRoot {
	path: string // Absolute path to the workspace root
	name?: string // Optional display name for the workspace (auto-derived from path if not provided)
	vcs: VcsType // Version control system type for this root
	commitHash?: string // Optional latest commit hash/changeset ID for VCS tracking
}

// Example usage:
// const workspaceRoots: WorkspaceRoot[] = [
//   {
//     path: "/Users/dev/frontend",
//     name: "frontend",
//     vcs: VcsType.Git,
//     commitHash: "a1b2c3d4e5f6789"
//   },
//   {
//     path: "/Users/dev/backend",
//     name: "backend",
//     vcs: VcsType.Git,
//     commitHash: "f6e5d4c3b2a1987"
//   }
// ]
