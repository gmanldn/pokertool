# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/prompts/system-prompt/components/tool_use/formatting.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { TemplateEngine } from "../../templates/TemplateEngine"
import type { PromptVariant, SystemPromptContext } from "../../types"

export async function getToolUseFormattingSection(_variant: PromptVariant, context: SystemPromptContext): Promise<string> {
    // Return the placeholder that will be replaced with actual tools
    const template = TOOL_USE_FORMATTING_TEMPLATE_TEXT

    const focusChainEnabled = context.focusChainSettings?.enabled

    const templateEngine = new TemplateEngine()
    return templateEngine.resolve(template, context, {
        FOCUS_CHATIN_FORMATTING: focusChainEnabled ? FOCUS_CHATIN_FORMATTING_TEMPLATE : "",
    })
}

const FOCUS_CHATIN_FORMATTING_TEMPLATE = `<task_progress>
Checklist here (optional)
</task_progress>
`

const TOOL_USE_FORMATTING_TEMPLATE_TEXT = `# Tool Use Formatting

Tool use is formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. Here's the structure:

<tool_name>
<parameter1_name>value1</parameter1_name>
<parameter2_name>value2</parameter2_name>
...
</tool_name>

For example:

<read_file>
<path>src/main.js</path>
{{FOCUS_CHATIN_FORMATTING}}</read_file>

Always adhere to this format for the tool use to ensure proper parsing and execution.`
