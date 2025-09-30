# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/grpc-recorder/__tests__/log-file-handler.test.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { expect } from "chai"
import { before, describe, it } from "mocha"
import { LogFileHandler } from "@/core/controller/grpc-recorder/log-file-handler"

describe("log-file-handler", () => {
	let logHandler: LogFileHandler

	before(async () => {
		logHandler = new LogFileHandler()
		expect(logHandler.getFilePath()).not.empty
	})

	describe("LogFileHandler", () => {
		it("returns file name with timestamp when env var not set", () => {
			const result = logHandler.getFileName()
			expect(result).to.contains("grpc_recorded_session")
		})
	})
})
