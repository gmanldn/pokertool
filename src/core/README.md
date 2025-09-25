        <!-- POKERTOOL-HEADER-START
        ---
        schema: pokerheader.v1
project: pokertool
file: src/core/README.md
version: v20.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
        ---
        POKERTOOL-HEADER-END -->
# Core Architecture

Extension entry point (extension.ts) -> webview -> controller -> task

```tree
core/
├── webview/      # Manages webview lifecycle
├── controller/   # Handles webview messages and task management
├── task/         # Executes API requests and tool operations
└── ...           # Additional components to help with context, parsing user/assistant messages, etc.
```
