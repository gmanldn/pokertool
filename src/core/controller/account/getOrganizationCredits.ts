# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/account/getOrganizationCredits.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { GetOrganizationCreditsRequest, OrganizationCreditsData, OrganizationUsageTransaction } from "@shared/proto/cline/account"
import type { Controller } from "../index"

/**
 * Handles fetching all organization credits data (balance, usage, payments)
 * @param controller The controller instance
 * @param request Organization credits request
 * @returns Organization credits data response
 */
export async function getOrganizationCredits(
	controller: Controller,
	request: GetOrganizationCreditsRequest,
): Promise<OrganizationCreditsData> {
	try {
		if (!controller.accountService) {
			throw new Error("Account service not available")
		}

		// Call the individual RPC variants in parallel
		const [balanceData, usageTransactions] = await Promise.all([
			controller.accountService.fetchOrganizationCreditsRPC(request.organizationId),
			controller.accountService.fetchOrganizationUsageTransactionsRPC(request.organizationId),
		])

		// If balance call fails (returns undefined), throw an error
		if (!balanceData) {
			throw new Error("Failed to fetch organization credits data")
		}

		return OrganizationCreditsData.create({
			balance: balanceData ? { currentBalance: balanceData.balance / 100 } : { currentBalance: 0 },
			organizationId: balanceData?.organizationId || "",
			usageTransactions:
				usageTransactions?.map((tx) =>
					OrganizationUsageTransaction.create({
						aiInferenceProviderName: tx.aiInferenceProviderName,
						aiModelName: tx.aiModelName,
						aiModelTypeName: tx.aiModelTypeName,
						completionTokens: tx.completionTokens,
						costUsd: tx.costUsd,
						createdAt: tx.createdAt,
						creditsUsed: tx.creditsUsed,
						generationId: tx.generationId,
						organizationId: tx.organizationId,
						promptTokens: tx.promptTokens,
						totalTokens: tx.totalTokens,
						userId: tx.userId,
					}),
				) || [],
		})
	} catch (error) {
		console.error(`Failed to fetch organization credits data: ${error}`)
		throw error
	}
}
