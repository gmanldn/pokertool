// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/services/tree-sitter/queries/rust.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
/*
- struct definitions
- method definitions
- function definitions
*/
export default `
(struct_item
    name: (type_identifier) @name.definition.class) @definition.class

(declaration_list
    (function_item
        name: (identifier) @name.definition.method)) @definition.method

(function_item
    name: (identifier) @name.definition.function) @definition.function
`
