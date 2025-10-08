# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/services/tree-sitter/queries/swift.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
/*
- class declarations
- method declarations (including initializers and deinitializers)
- property declarations
- function declarations
*/
export default `
(class_declaration
  name: (type_identifier) @name) @definition.class

(protocol_declaration
  name: (type_identifier) @name) @definition.interface

(class_declaration
    (class_body
        [
            (function_declaration
                name: (simple_identifier) @name
            )
            (subscript_declaration
                (parameter (simple_identifier) @name)
            )
            (init_declaration "init" @name)
            (deinit_declaration "deinit" @name)
        ]
    )
) @definition.method

(class_declaration
    (class_body
        [
            (property_declaration
                (pattern (simple_identifier) @name)
            )
        ]
    )
) @definition.property

(property_declaration
    (pattern (simple_identifier) @name)
) @definition.property

(function_declaration
    name: (simple_identifier) @name) @definition.function
`
