# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/file/searchCommits.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { StringRequest } from "@shared/proto/cline/common"
import { GitCommits } from "@shared/proto/cline/file"
import { searchCommits as searchCommitsUtil } from "@utils/git"
import { getWorkspacePath } from "@utils/path"
import { Controller } from ".."

/**
 * Searches for git commits in the workspace repository
 * @param controller The controller instance
 * @param request The request message containing the search query in the 'value' field
 * @returns GitCommits containing the matching commits
 */
export async function searchCommits(_controller: Controller, request: StringRequest): Promise<GitCommits> {
    const cwd = await getWorkspacePath()
    if (!cwd) {
        return GitCommits.create({ commits: [] })
    }

    try {
        const commits = await searchCommitsUtil(request.value || "", cwd)

        return GitCommits.create({ commits })
    } catch (error) {
        console.error(`Error searching commits: ${JSON.stringify(error)}`)
        return GitCommits.create({ commits: [] })
    }
}
