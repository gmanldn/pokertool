# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/services/tree-sitter/index.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { ClineIgnoreController } from "@core/ignore/ClineIgnoreController"
import { listFiles } from "@services/glob/list-files"
import { fileExistsAtPath } from "@utils/fs"
import * as fs from "fs/promises"
import * as path from "path"
import { LanguageParser, loadRequiredLanguageParsers } from "./languageParser"

const CACHE_TTL_MS = 60_000

interface ParserCacheEntry {
    result: string
    timestamp: number
    fileList: string[]
    fileSignatures: Record<string, number>
}

const parserResultCache = new Map<string, ParserCacheEntry>()

function buildCacheKey(dirPath: string, clineIgnoreController?: ClineIgnoreController): string {
    const ignoreSignature = clineIgnoreController?.clineIgnoreContent ?? "__NO_IGNORE__"
    return `${path.resolve(dirPath)}::${ignoreSignature}`
}

function normalizeFileList(filePaths: string[]): string[] {
    return filePaths.map((file) => path.resolve(file)).sort()
}

function areArraysEqual(a: string[], b: string[]): boolean {
    if (a.length !== b.length) {
        return false
    }
    return a.every((value, index) => value === b[index])
}

async function tryGetCachedResult(cacheKey: string, normalizedFileList: string[]): Promise<string | null> {
    const entry = parserResultCache.get(cacheKey)
    if (!entry) {
        return null
    }

    if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
        parserResultCache.delete(cacheKey)
        return null
    }

    if (!areArraysEqual(entry.fileList, normalizedFileList)) {
        return null
    }

    for (const filePath of normalizedFileList) {
        try {
            const stat = await fs.stat(filePath)
            if (entry.fileSignatures[filePath] !== stat.mtimeMs) {
                return null
            }
        } catch {
            return null
        }
    }

    return entry.result
}

function updateCacheEntry(
    cacheKey: string,
    normalizedFileList: string[],
    fileSignatures: Record<string, number>,
    result: string,
): void {
    parserResultCache.set(cacheKey, {
        result,
        timestamp: Date.now(),
        fileList: normalizedFileList,
        fileSignatures,
    })
}

// Caches recent parse results to avoid repeatedly reanalyzing unchanged projects.
export async function parseSourceCodeForDefinitionsTopLevel(
    dirPath: string,
    clineIgnoreController?: ClineIgnoreController,
): Promise<string> {
    // check if the path exists
    const dirExists = await fileExistsAtPath(path.resolve(dirPath))
    if (!dirExists) {
        return "This directory does not exist or you do not have permission to access it."
    }

    // Get all files at top level (not gitignored)
    const [allFiles, _] = await listFiles(dirPath, false, 200)

    // Separate files to parse and remaining files
    const { filesToParse, remainingFiles } = separateFiles(allFiles)

    const allowedFilesToParse = clineIgnoreController ? clineIgnoreController.filterPaths(filesToParse) : filesToParse
    const normalizedFileList = normalizeFileList(allowedFilesToParse)
    const cacheKey = buildCacheKey(dirPath, clineIgnoreController)

    const cachedResult = await tryGetCachedResult(cacheKey, normalizedFileList)
    if (cachedResult !== null) {
        return cachedResult
    }

    const languageParsers = await loadRequiredLanguageParsers(filesToParse)

    // Parse specific files we have language parsers for
    // const filesWithoutDefinitions: string[] = []

    // Filter filepaths for access if controller is provided
    let result = ""
    const fileSignatures: Record<string, number> = {}
    let canCache = true

    for (const filePath of allowedFilesToParse) {
        try {
            const stat = await fs.stat(filePath)
            fileSignatures[path.resolve(filePath)] = stat.mtimeMs
        } catch {
            // If we cannot stat the file, skip caching for this entry so we refresh next time
            canCache = false
            continue
        }

        const definitions = await parseFile(filePath, languageParsers, clineIgnoreController)
        if (definitions) {
            result += `${path.relative(dirPath, filePath).toPosix()}\n${definitions}\n`
        }
        // else {
        //     filesWithoutDefinitions.push(file)
        // }
    }

    // List remaining files' paths
    // let didFindUnparsedFiles = false
    // filesWithoutDefinitions
    //     .concat(remainingFiles)
    //     .sort()
    //     .forEach((file) => {
    //         if (!didFindUnparsedFiles) {
    //             result += "# Unparsed Files\n\n"
    //             didFindUnparsedFiles = true
    //         }
    //         result += `${path.relative(dirPath, file)}\n`
    //     })

    const finalResult = result ? result : "No source code definitions found."
    if (canCache) {
        updateCacheEntry(cacheKey, normalizedFileList, fileSignatures, finalResult)
    }

    return finalResult
}

function separateFiles(allFiles: string[]): {
    filesToParse: string[]
    remainingFiles: string[]
} {
    const extensions = [
        "js",
        "jsx",
        "ts",
        "tsx",
        "py",
        // Rust
        "rs",
        "go",
        // C
        "c",
        "h",
        // C++
        "cpp",
        "hpp",
        // C#
        "cs",
        // Ruby
        "rb",
        "java",
        "php",
        "swift",
        // Kotlin
        "kt",
    ].map((e) => `.${e}`)
    const filesToParse = allFiles.filter((file) => extensions.includes(path.extname(file))).slice(0, 50) // 50 files max
    const remainingFiles = allFiles.filter((file) => !filesToParse.includes(file))
    return { filesToParse, remainingFiles }
}

/*
Parsing files using tree-sitter

1. Parse the file content into an AST (Abstract Syntax Tree) using the appropriate language grammar (set of rules that define how the components of a language like keywords, expressions, and statements can be combined to create valid programs).
2. Create a query using a language-specific query string, and run it against the AST's root node to capture specific syntax elements.
    - We use tag queries to identify named entities in a program, and then use a syntax capture to label the entity and its name. A notable example of this is GitHub's search-based code navigation.
    - Our custom tag queries are based on tree-sitter's default tag queries, but modified to only capture definitions.
3. Sort the captures by their position in the file, output the name of the definition, and format by i.e. adding "|----\n" for gaps between captured sections.

This approach allows us to focus on the most relevant parts of the code (defined by our language-specific queries) and provides a concise yet informative view of the file's structure and key elements.

- https://github.com/tree-sitter/node-tree-sitter/blob/master/test/query_test.js
- https://github.com/tree-sitter/tree-sitter/blob/master/lib/binding_web/test/query-test.js
- https://github.com/tree-sitter/tree-sitter/blob/master/lib/binding_web/test/helper.js
- https://tree-sitter.github.io/tree-sitter/code-navigation-systems
*/
async function parseFile(
    filePath: string,
    languageParsers: LanguageParser,
    clineIgnoreController?: ClineIgnoreController,
): Promise<string | null> {
    if (clineIgnoreController && !clineIgnoreController.validateAccess(filePath)) {
        return null
    }
    const fileContent = await fs.readFile(filePath, "utf8")
    const ext = path.extname(filePath).toLowerCase().slice(1)

    const { parser, query } = languageParsers[ext] || {}
    if (!parser || !query) {
        return `Unsupported file type: ${filePath}`
    }

    let formattedOutput = ""

    try {
        // Parse the file content into an Abstract Syntax Tree (AST), a tree-like representation of the code
        const tree = parser.parse(fileContent)
        if (!tree || !tree.rootNode) {
            return null
        }

        // Apply the query to the AST and get the captures
        // Captures are specific parts of the AST that match our query patterns, each capture represents a node in the AST that we're interested in.
        const captures = query.captures(tree.rootNode)

        // Sort captures by their start position
        captures.sort((a, b) => a.node.startPosition.row - b.node.startPosition.row)

        // Split the file content into individual lines
        const lines = fileContent.split("\n")

        // Keep track of the last line we've processed
        let lastLine = -1

        captures.forEach((capture) => {
            const { node, name } = capture
            // Get the start and end lines of the current AST node
            const startLine = node.startPosition.row
            const endLine = node.endPosition.row
            // Once we've retrieved the nodes we care about through the language query, we filter for lines with definition names only.
            // name.startsWith("name.reference.") > refs can be used for ranking purposes, but we don't need them for the output
            // previously we did `name.startsWith("name.definition.")` but this was too strict and excluded some relevant definitions

            // Add separator if there's a gap between captures
            if (lastLine !== -1 && startLine > lastLine + 1) {
                formattedOutput += "|----\n"
            }
            // Only add the first line of the definition
            // query captures includes the definition name and the definition implementation, but we only want the name (I found discrepancies in the naming structure for various languages, i.e. javascript names would be 'name' and typescript names would be 'name.definition)
            if (name.includes("name") && lines[startLine]) {
                formattedOutput += `│${lines[startLine]}\n`
            }
            // Adds all the captured lines
            // for (let i = startLine; i <= endLine; i++) {
            //     formattedOutput += `│${lines[i]}\n`
            // }
            //}

            lastLine = endLine
        })
    } catch (error) {
        console.log(`Error parsing file: ${error}\n`)
    }

    if (formattedOutput.length > 0) {
        return `|----\n${formattedOutput}|----\n`
    }
    return null
}
