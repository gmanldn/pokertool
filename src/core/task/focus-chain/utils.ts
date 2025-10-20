# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/task/focus-chain/utils.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { isCompletedFocusChainItem, isFocusChainItem } from "@shared/focus-chain-utils"

export interface TodoListCounts {
    totalItems: number
    completedItems: number
}

/**
 * Parses a focus chain list string and returns counts of total and completed items
 * @param todoList The focus chain list string to parse
 * @returns Object with totalItems and completedItems counts
 */
export function parseFocusChainListCounts(todoList: string): TodoListCounts {
    const lines = todoList.split("\n")
    let totalItems = 0
    let completedItems = 0

    for (const line of lines) {
        const trimmed = line.trim()
        if (isFocusChainItem(trimmed)) {
            totalItems++
            if (isCompletedFocusChainItem(trimmed)) {
                completedItems++
            }
        }
    }

    return { totalItems, completedItems }
}
