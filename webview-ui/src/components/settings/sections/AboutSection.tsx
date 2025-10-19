import { VSCodeLink } from "@vscode/webview-ui-toolkit/react"
import Section from "../Section"

interface AboutSectionProps {
	version: string
	renderSectionHeader: (tabId: string) => JSX.Element | null
}

const AboutSection = ({ version, renderSectionHeader }: AboutSectionProps) => {
	return (
		<div>
			{renderSectionHeader("about")}
			<Section>
				<div className="flex flex-col items-center text-center text-[var(--vscode-descriptionForeground)] text-xs leading-[1.3] px-0 py-0 pr-2 pb-[18px] mt-auto gap-4">
					<div
						className="inline-flex items-center gap-3 rounded-full border px-4 py-2 text-sm font-semibold shadow-sm"
						style={{
							borderColor: "var(--vscode-focusBorder)",
							background: "var(--vscode-editorWidget.background)",
							color: "var(--vscode-foreground)",
						}}
					>
						<span className="uppercase tracking-[0.3em] text-[10px] text-[var(--vscode-descriptionForeground)]">
							Version
						</span>
						<span className="text-xl font-bold">v{version}</span>
					</div>
					<p className="break-words m-0 p-0">
						If you have any questions or feedback, feel free to open an issue at{" "}
						<VSCodeLink className="inline" href="https://github.com/gmanldn/pokertool/issues">
							https://github.com/gmanldn/pokertool/issues
						</VSCodeLink>
					</p>
				</div>
			</Section>
		</div>
	)
}

export default AboutSection
