// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/exports/cline.d.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
export interface ClineAPI {
    /**
     * Starts a new task with an optional initial message and images.
     * @param task Optional initial task message.
     * @param images Optional array of image data URIs (e.g., "data:image/webp;base64,...").
     */
    startNewTask(task?: string, images?: string[]): Promise<void>

    /**
     * Sends a message to the current task.
     * @param message Optional message to send.
     * @param images Optional array of image data URIs (e.g., "data:image/webp;base64,...").
     */
    sendMessage(message?: string, images?: string[]): Promise<void>

    /**
     * Simulates pressing the primary button in the chat interface.
     */
    pressPrimaryButton(): Promise<void>

    /**
     * Simulates pressing the secondary button in the chat interface.
     */
    pressSecondaryButton(): Promise<void>
}
