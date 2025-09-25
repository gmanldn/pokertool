# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/prompts/system-prompt/components/index.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { SystemPromptSection } from "../templates/placeholders"
import { getActVsPlanModeSection } from "./act_vs_plan_mode"
import { getAgentRoleSection } from "./agent_role"
import { getTodoListSection } from "./auto_todo"
import { getCapabilitiesSection } from "./capabilities"
import { getEditingFilesSection } from "./editing_files"
import { getFeedbackSection } from "./feedback"
import { getMcp } from "./mcp"
import { getObjectiveSection } from "./objective"
import { getRulesSection } from "./rules"
import { getSystemInfo } from "./system_info"
import { getUpdatingTaskProgress } from "./task_progress"
import { getToolUseSection } from "./tool_use"
import { getUserInstructions } from "./user_instructions"

/**
 * Registers all tool variants with the ClineToolSet provider.
 * This function should be called once during application initialization
 * to make all tools available for use.
 */
export function getSystemPromptComponents() {
	return [
		{ id: SystemPromptSection.AGENT_ROLE, fn: getAgentRoleSection },
		{ id: SystemPromptSection.SYSTEM_INFO, fn: getSystemInfo },
		{ id: SystemPromptSection.MCP, fn: getMcp },
		{ id: SystemPromptSection.TODO, fn: getTodoListSection },
		{
			id: SystemPromptSection.USER_INSTRUCTIONS,
			fn: getUserInstructions,
		},
		{ id: SystemPromptSection.TOOL_USE, fn: getToolUseSection },
		{
			id: SystemPromptSection.EDITING_FILES,
			fn: getEditingFilesSection,
		},
		{
			id: SystemPromptSection.CAPABILITIES,
			fn: getCapabilitiesSection,
		},
		{ id: SystemPromptSection.RULES, fn: getRulesSection },
		{ id: SystemPromptSection.OBJECTIVE, fn: getObjectiveSection },
		{
			id: SystemPromptSection.ACT_VS_PLAN,
			fn: getActVsPlanModeSection,
		},
		{
			id: SystemPromptSection.FEEDBACK,
			fn: getFeedbackSection,
		},
		{ id: SystemPromptSection.TASK_PROGRESS, fn: getUpdatingTaskProgress },
	]
}
