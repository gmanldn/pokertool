// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/test/e2e/utils/global.setup.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { rmSync } from "node:fs"
import { test as setup } from "@playwright/test"
import { E2ETestHelper } from "./helpers"

setup("setup test environment", async () => {
    try {
        const path = E2ETestHelper.getResultsDir()
        const options = { recursive: true, force: true }

        const maxAttempts = 2

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                rmSync(path, options)
                return
            } catch (error) {
                if (attempt === maxAttempts) {
                    throw new Error(`Failed to rmSync ${path} after ${maxAttempts} attempts: ${error}`)
                }
                console.error(`Failed to rmSync ${path} after ${attempt} attempts: ${error}`)
                await new Promise((resolve) => setTimeout(resolve, 50 * attempt)) // Progressive delay
            }
        }
    } catch (error) {
        console.error(`Error during setup: ${error}`)
    }
})
