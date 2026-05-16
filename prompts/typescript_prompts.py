API_USAGE_SYSTEM_PROMPT = """
You are an expert TypeScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality TypeScript API Usage instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly use a
common but error-prone TypeScript or Node.js API under realistic
context constraints, including parameter ordering, type annotations,
generic constraints, error handling, encoding semantics, and edge
cases.

The instance must be a code-completion task, not a standalone
programming problem. The evaluated model will see only:
  - prefix: code before the cursor
  - suffix: optional code after the cursor for fill-in-the-middle settings

The evaluated model will NOT see:
  - golden_completion
  - assertions
  - LLM_justification

Return a single valid JSON object with the following fields:
  - id: unique identifier
  - testsource: "devbench-api-usage"
  - language: "typescript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    API Usage task

Requirements:

1. Realistic API usage.
   Use APIs from the Node.js standard library and TypeScript type
   system, reflecting telemetry-observed completion scenarios.
   Representative domains include:
   - Buffer and encoding: Buffer.alloc fill patterns, Buffer.from
     with encoding parameter, hex/base64 round-trip semantics,
     TextEncoder.encodeInto return shape
   - Crypto: createHmac chaining (.update/.digest), timingSafeEqual
     length requirement, AES-256-GCM 12-byte IV (not 16 like CBC),
     randomBytes sizing
   - Path and URL: path.resolve vs cwd, path.relative edge cases,
     WHATWG URL parsing (protocol colon, hostname lowercasing),
     URLSearchParams append vs set semantics
   - Stream and events: stream.pipeline with promisify,
     EventEmitter ordering and once semantics, Readable.from
     objectMode, Transform callback signatures
   - TypeScript generics: keyof constraints (K extends keyof T),
     conditional types with infer (Promise<infer U>), mapped types,
     discriminated union narrowing, generic utility types at runtime
   - Intl and formatting: Collator numeric sorting, NumberFormat
     percent style (0.42 -> 42%), locale-sensitive comparisons
   - Timers and process: setInterval cleanup patterns,
     process.hrtime.bigint nanosecond format, AbortController.abort
     reason type (DOMException not undefined)
   - Proxy and symbols: Proxy set trap boolean return, Reflect
     method signatures, Symbol.toPrimitive hint values,
     Symbol.iterator protocol
   - Container semantics: Map.forEach with delete-during-iteration,
     TypedArray.from with mapFn, DataView endianness defaults,
     SharedArrayBuffer + Atomics old-value return semantics
   - Docstring precision: TSDoc with type annotations, documenting
     exact API behavior (return types, mutation, error conditions)
   The API call should be embedded in a plausible function, class,
   or workflow, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (type compatibility,
   generic constraints, error-path behavior, parameter ordering,
   boundary conditions, or consistency with surrounding types). The
   task should not be solvable by copying a nearby line. Avoid
   textbook-perfect toy examples; include realistic engineering
   context such as fallback behavior or type narrowing.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than API reasoning, invalid TypeScript, or
   overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

API_USAGE_USER_PROMPT = """
Generate one TypeScript API Usage evaluation instance. Choose a
domain from the representative list in the system prompt (Buffer
and encoding, crypto, path and URL, streams and events, TypeScript
generics, Intl and formatting, timers and process, Proxy and
symbols, container semantics, or docstring precision).

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines, \\t for tabs, \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. DO NOT use markdown code blocks in your response

Required JSON fields:
- id: unique numeric identifier
- testsource: "devbench-api-usage"
- language: "typescript"
- prefix: code before the completion point (establishes context)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  maintains consistency with prefix/suffix
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  edge case not spelled out in comments
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must compile and execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require resolving at least two
   contextual constraints from prefix/suffix

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid TypeScript that compiles with tsc
2. Do not place executable statements at module top level
   outside of functions (imports, type aliases, interface and
   class definitions, and constant declarations are allowed)
3. All code blocks must have matching braces
4. Include only imports that are actually used
5. Use // Run assertions comment style for assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-api-usage", "language":
"typescript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion resolve multiple context constraints?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

CODE_PURPOSE_UNDERSTANDING_SYSTEM_PROMPT = """
You are an expert TypeScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality TypeScript Code Purpose
Understanding instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model can
infer business logic and domain intent from surrounding code and
produce a completion that satisfies multiple coupled invariants.

The instance must be a code-completion task, not a standalone
programming problem. The evaluated model will see only:
  - prefix: code before the cursor
  - suffix: optional code after the cursor for fill-in-the-middle settings

The evaluated model will NOT see:
  - golden_completion
  - assertions
  - LLM_justification

Return a single valid JSON object with the following fields:
  - id: unique identifier
  - testsource: "devbench-code-purpose-understanding"
  - language: "typescript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code Purpose Understanding task

Requirements:

1. Realistic business logic with coupled invariants.
   The completion must require understanding and coordinating
   multiple interacting domain rules, not just syntax. Use
   TypeScript closures, class state machines, and typed interfaces
   to encode complex workflows. Representative domains include:
   - Financial workflows: loan waterfall allocation (fees ->
     interest -> principal -> unapplied), progressive bracket
     taxation with YTD accumulators, commission with tiered rates
     and annual caps, escrow milestone release with holdback
   - Inventory and fulfillment: FEFO allocation with expiry
     filtering and atomic rollback, warehouse picking with
     weight-constrained bin priority, reorder point with EOQ
     and safety stock formulas
   - Order processing: tiered discounts, tax on post-discount
     amount, conditional free shipping, gift card stacking with
     ascending-balance FIFO drain
   - Insurance and healthcare: copay -> deductible -> coinsurance
     waterfall with OOP cap, prescription validation with drug
     interaction checking, appointment scheduling with buffer
     overlap detection and priority bumping
   - HR and payroll: pre-tax deductions, progressive brackets,
     post-tax flat deductions, leave management with carryover-
     first deduction, timesheet with weekend-excluded overtime
   - Event-sourced systems: account projection with frozen guard,
     saga with reverse-order compensation, CQRS with multi-path
     validation, approval pipelines with threshold voting
   - Infrastructure: rate limiting with sliding windows and
     escalating penalties, deploy pipelines with dependency
     gating and rollback, workflow engines with decision branching
   Each task must enforce idempotency (repeated calls return
   cached results) alongside at least two other coupled invariants.

2. Difficulty.
   The completion should require coordinating at least three
   coupled side effects (validation order, accumulation, audit
   logging, idempotency). The model must READ the surrounding
   code and understand its PURPOSE, not just match syntax. Avoid
   tasks where the suffix reveals the answer through assertions.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than business-logic reasoning, invalid
   TypeScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
Generate one TypeScript Code Purpose Understanding evaluation
instance. Choose a domain from the representative list in the
system prompt (financial workflows, inventory and fulfillment,
order processing, insurance and healthcare, HR and payroll,
event-sourced systems, or infrastructure).

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines, \\t for tabs, \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. DO NOT use markdown code blocks in your response

Required JSON fields:
- id: unique numeric identifier
- testsource: "devbench-code-purpose-understanding"
- language: "typescript"
- prefix: code before the completion point (establishes context)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  maintains consistency with prefix/suffix
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  edge case not spelled out in comments
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must compile and execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require coordinating at least three
   coupled side effects

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid TypeScript that compiles with tsc
2. Do not place executable statements at module top level
   outside of functions (imports, type aliases, interface and
   class definitions, and constant declarations are allowed)
3. All code blocks must have matching braces
4. Include only imports that are actually used
5. Use // Run assertions comment style for assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code-purpose-understanding",
"language": "typescript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion coordinate multiple coupled invariants?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert TypeScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality TypeScript Code2NL/NL2Code
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can produce
precise TSDoc documentation for existing code (Code2NL) or
implement code from a detailed natural-language specification
(NL2Code).

The instance must be a code-completion task, not a standalone
programming problem. The evaluated model will see only:
  - prefix: code before the cursor
  - suffix: optional code after the cursor for fill-in-the-middle settings

The evaluated model will NOT see:
  - golden_completion
  - assertions
  - LLM_justification

Return a single valid JSON object with the following fields:
  - id: unique identifier
  - testsource: "devbench-code2NL-NL2code"
  - language: "typescript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code2NL/NL2Code task

Requirements:

1. Precise bidirectional translation with TSDoc and type annotations.
   For Code2NL tasks, the model must produce documentation that
   includes specific technical details, not generic summaries.
   For NL2Code tasks, the model must implement code from a
   natural-language specification with non-obvious edge cases.
   Representative domains include:
   - Code2NL documentation precision: TSDoc with @param, @returns,
     @throws annotations; documenting in-place mutation vs copy,
     stable ordering guarantees, exactly-once semantics, specific
     fallback values (e.g., __none__ for null keys), method
     chaining return types, circular reference handling, lazy vs
     eager evaluation, generic type parameter purposes
   - Code2NL behavioral details: exponential backoff parameters
     (doubling, milliseconds), priority ordering (higher first),
     tie-breaking rules (first wins, registration order), drain
     behavior on over-large inputs, audit log side effects,
     WeakSet/WeakMap usage for circular references, generator
     factory vs single generator replayability
   - NL2Code implementation tasks: depth-limited array flattening,
     compact object assignment with NaN skipping, INI file parsing
     with section inheritance, topological sort with alphabetical
     tie-breaking, stateful tokenizers with escape handling, LCS-
     based line diff with hunk merging, deep clone with circular
     reference handling, interval merging with tag aggregation,
     reactive observable operators (take, filter, map)
   - TypeScript-specific: documenting generic constraints, branded
     types, discriminated unions, exhaustiveness checks (never
     type), Readonly<> vs Object.freeze runtime behavior, mapped
     type relationships, closure-captured mutable state

2. Difficulty.
   For Code2NL: assertions must require specific keywords about
   behavior, exceptions, complexity, or side effects that a
   generic description would omit. For NL2Code: the specification
   must include at least one non-obvious rule that models tend to
   miss (e.g., NaN skipping, left-to-right override order,
   strictly-greater-than comparisons).

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than documentation-precision reasoning,
   invalid TypeScript, or overly simplified textbook
   implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

NL2CODE_CODE2NL_USER_PROMPT = """
Generate one TypeScript Code2NL/NL2Code evaluation instance.
Choose a domain from the representative list in the system prompt
(Code2NL documentation precision, Code2NL behavioral details,
NL2Code implementation tasks, or TypeScript-specific documentation).

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines, \\t for tabs, \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. DO NOT use markdown code blocks in your response

Required JSON fields:
- id: unique numeric identifier
- testsource: "devbench-code2NL-NL2code"
- language: "typescript"
- prefix: code before the completion point (establishes context)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  maintains consistency with prefix/suffix
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  edge case not spelled out in comments
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must compile and execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. For Code2NL: the completion is a TSDoc comment string; hidden
   assertions check for specific keywords via .includes()
5. For NL2Code: the completion is an implementation; hidden
   assertions test functional behavior and edge cases

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid TypeScript that compiles with tsc
2. Do not place executable statements at module top level
   outside of functions (imports, type aliases, interface and
   class definitions, and constant declarations are allowed)
3. All code blocks must have matching braces
4. Include only imports that are actually used
5. Use // Run assertions comment style for assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language":
"typescript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion require precise domain knowledge?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert TypeScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality TypeScript Low Context
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can recognize
and complete a code pattern from minimal surrounding context
(10-20 lines total for prefix + suffix combined).

The instance must be a code-completion task, not a standalone
programming problem. The evaluated model will see only:
  - prefix: code before the cursor
  - suffix: optional code after the cursor for fill-in-the-middle settings

The evaluated model will NOT see:
  - golden_completion
  - assertions
  - LLM_justification

Return a single valid JSON object with the following fields:
  - id: unique identifier
  - testsource: "devbench-low-context"
  - language: "typescript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Low Context task

Requirements:

1. Low-context patterns with type guards and branded types.
   The prefix and suffix combined must be only 10-20 lines, yet
   contain enough signal to infer the correct completion. Use
   TypeScript idioms that require genuine understanding, not
   simple pattern copying. Representative domains include:
   - Custom encoding with familiar names: base58, base62, base36,
     base32, base16, base85, base45, octal, decimal encoders with
     reversed or non-standard default alphabets; integer-style
     conversion instead of standard block-based encoding
   - Type guards and branded types: nominal typing via branded
     types with validation rules (rejecting 0, negative, non-
     integer), discriminated union matching with non-standard
     fallback keys ('_' instead of 'default')
   - Result/Option patterns: tryCatch wrappers that must wrap
     non-Error thrown values, step pipelines with short-circuit
     on failure, typed Result<T, E> discriminated unions
   - State machines: non-standard transition orders (e.g.,
     green -> yellow -> red instead of standard traffic light),
     compact FSM with configurable cycle direction
   - Schema and config validation: strict-mode validators that
     reject extra keys (unlike JSON Schema default), config
     builders where numeric overrides are doubled, template
     engines with non-standard case transformation
   - Compact utilities: weighted Hamming distance, bisectRight
     with key function and generics, run-length encoding with
     non-standard format (count-first), interleave with remainder
     handling, title-case with minimum-length filter
   - Generic TypeScript patterns: Pick<T, K> at runtime with
     keyof constraints, GroupBy returning Map<K, T[]>, generic
     pipeline composition with type inference

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints despite minimal surrounding code. The function name
   or pattern must trigger a strong preconception that differs from
   the actual required behavior (e.g., reversed alphabet, non-
   standard defaults, doubled parameters). Include at least one
   trap that exploits model retrieval of standard implementations.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than pattern-recognition reasoning,
   invalid TypeScript, or overly simplified textbook
   implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

LOW_CONTEXT_USER_PROMPT = """
Generate one TypeScript Low Context evaluation instance. Choose a
domain from the representative list in the system prompt (custom
encoding with familiar names, type guards and branded types,
Result/Option patterns, state machines, schema and config
validation, compact utilities, or generic TypeScript patterns).

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines, \\t for tabs, \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. DO NOT use markdown code blocks in your response

Required JSON fields:
- id: unique numeric identifier
- testsource: "devbench-low-context"
- language: "typescript"
- prefix: code before the completion point (establishes context)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  maintains consistency with prefix/suffix
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  edge case not spelled out in comments
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must compile and execute successfully
6. Include at least one edge case assertion

CRITICAL LOW CONTEXT REQUIREMENTS:
1. The prefix and suffix combined must be ONLY 10-20 lines total
2. Keep the context deliberately minimal while ensuring the
   pattern is still inferable from the visible code
3. The function name should trigger a strong preconception that
   differs from the required behavior

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require resolving at least two
   contextual constraints from prefix/suffix

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid TypeScript that compiles with tsc
2. Do not place executable statements at module top level
   outside of functions (imports, type aliases, interface and
   class definitions, and constant declarations are allowed)
3. All code blocks must have matching braces
4. Include only imports that are actually used
5. Use // Run assertions comment style for assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-low-context", "language":
"typescript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion resolve multiple context constraints?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
9. Is the combined prefix + suffix 10-20 lines total?
"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert TypeScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality TypeScript Pattern
Matching instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model can
implement a custom transformation that follows the pattern
established in the prefix, resisting retrieval of standard
implementations triggered by familiar function names.

The instance must be a code-completion task, not a standalone
programming problem. The evaluated model will see only:
  - prefix: code before the cursor
  - suffix: optional code after the cursor for fill-in-the-middle settings

The evaluated model will NOT see:
  - golden_completion
  - assertions
  - LLM_justification

Return a single valid JSON object with the following fields:
  - id: unique identifier
  - testsource: "devbench-pattern-matching"
  - language: "typescript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Pattern Matching task

Requirements:

1. Escape-aware parsers, tokenizers, and custom encoding schemes.
   The prefix must establish a clear pattern (via constants,
   helper functions, or examples) that the completion must follow.
   The pattern must differ from what the function name suggests.
   Representative domains include:
   - Custom encoding with reversed alphabets: base64, base58,
     base85, z85, base45, base62, base36, base52, base26, base94,
     percentEncode with reversed default alphabets; anti-standard
     assertions proving output differs from standard encoding
   - Non-standard algorithms with familiar names: editDistance
     with transposition cost != 1, longestCommonSubsequence that
     is case-insensitive, scheduleJobs with overlap tolerance
   - Stateful parsers: escape-aware template engines (\\{{ and
     \\}} escape sequences, nested dot-path resolution, pipe
     filters), bracket-aware splitting with quote context,
     CSV parsing with custom delimiters and escape conventions
   - Tokenizers: expression tokenization with stateful string
     parsing (backslash escapes inside quotes), multi-character
     operator recognition, escape sequence parsing (\\x, \\u
     with insufficient hex digit handling)
   - Non-standard formatting: RLE with threshold parameter (#
     escape for literal digits), number formatting with custom
     group size and separators, date formatting with non-standard
     12-hour rules, JSON serialization with custom conventions
   - TypeScript-specific patterns: discriminated union area
     calculations with non-standard formulas (pi=3), generic
     constraint patterns with descending sort, typed deep merge
     with array-replace semantics, priority event emitters with
     once semantics, range iterators with inclusive defaults
   - Trie and search: autocomplete with weight-based ranking,
     topological sort with priority scheduling, deep equality
     with configurable options (ignoreArrayOrder, tolerance)

2. Difficulty.
   The completion should require following the pattern established
   in the prefix rather than retrieving a standard implementation.
   The function name must trigger strong preconception of standard
   behavior. Include at least one anti-standard assertion that
   proves the standard implementation would fail.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than pattern-following reasoning, invalid
   TypeScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

PATTERN_MATCHING_USER_PROMPT = """
Generate one TypeScript Pattern Matching evaluation instance.
Choose a domain from the representative list in the system prompt
(custom encoding with reversed alphabets, non-standard algorithms
with familiar names, stateful parsers, tokenizers, non-standard
formatting, TypeScript-specific patterns, or trie and search).

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines, \\t for tabs, \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. DO NOT use markdown code blocks in your response

Required JSON fields:
- id: unique numeric identifier
- testsource: "devbench-pattern-matching"
- language: "typescript"
- prefix: code before the completion point (MUST establish or
  begin a clear pattern via constants, helpers, or examples)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  maintains consistency with prefix/suffix
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  edge case not spelled out in comments
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must compile and execute successfully
6. Include at least one edge case assertion
7. Include at least one ANTI-STANDARD assertion proving the
   standard implementation would produce different output

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The prefix must establish a clear pattern with at least 2-3
   examples before the completion point

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid TypeScript that compiles with tsc
2. Do not place executable statements at module top level
   outside of functions (imports, type aliases, interface and
   class definitions, and constant declarations are allowed)
3. All code blocks must have matching braces
4. Include only imports that are actually used
5. Use // Run assertions comment style for assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-pattern-matching", "language":
"typescript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion follow the pattern in the prefix?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
9. Does at least one assertion prove the standard algorithm fails?
"""

SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert TypeScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality TypeScript Syntax
Completion instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model can
correctly complete complex, nested TypeScript syntax structures
including conditional types, overloads, generics, and advanced
control flow.

The instance must be a code-completion task, not a standalone
programming problem. The evaluated model will see only:
  - prefix: code before the cursor
  - suffix: optional code after the cursor for fill-in-the-middle settings

The evaluated model will NOT see:
  - golden_completion
  - assertions
  - LLM_justification

Return a single valid JSON object with the following fields:
  - id: unique identifier
  - testsource: "devbench-syntax-completion"
  - language: "typescript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Syntax Completion task

Requirements:

1. Complex TypeScript syntax structures.
   The completion must require mastery of TypeScript-specific
   syntax, not just algorithm knowledge. Representative domains
   include:
   - Conditional types and overloads: function overload signatures
     with union implementation, conditional types with infer,
     mapped types with Extract and keyof, generic method
     constraints with indexed access types (T[K])
   - Discriminated unions: exhaustive switch with never-typed
     default (assertNever), discriminated union narrowing on
     status/kind fields, Promise.allSettled result processing
     with 'fulfilled'/'rejected' status narrowing
   - Async generators: AsyncGenerator<Y, R, N> type parameters,
     yield* delegation with return value capture, for-await-of
     with try-catch-finally, async generator transform pipelines
     with StreamItem<T> discriminated unions
   - Error handling with type narrowing: catch (err: unknown)
     with instanceof chains (subclass-first ordering), custom
     type guard functions (isAppError), error type casting with
     as-expressions, nested try-finally with resource disposal
   - Destructuring: multi-level nested destructuring with rename
     syntax (url: dbUrl), default values at every level, array
     binding with computed-key object patterns, optional
     properties with tuple type defaults
   - Class and generic patterns: abstract generic methods with
     'this' return for fluent chaining, mixin pattern with
     anonymous class extending generic constructor, interface
     declaration merging, Symbol.iterator as generator method
   - Builder and pipeline patterns: SQL query builder with
     conditional clause assembly, Koa-style middleware compose
     with recursive dispatch, Proxy traps with path tracking,
     typed reduce with explicit generic parameter
   - Promise patterns: Promise.allSettled mapping to discriminated
     union, Promise.race with timeout sentinel, .then/.catch
     chaining with typed lambda parameters, Promise constructor
     nested inside Promise.allSettled

2. Difficulty.
   The completion should require resolving at least two syntactic
   constraints (brace/bracket matching, type annotation
   consistency, generic parameter threading, indentation level).
   The task should not be solvable by copying a nearby line.
   Avoid tasks that test algorithm knowledge rather than syntax
   mastery.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than syntax-mastery reasoning, invalid
   TypeScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

SYNTAX_COMPLETION_USER_PROMPT = """
Generate one TypeScript Syntax Completion evaluation instance.
Choose a domain from the representative list in the system prompt
(conditional types and overloads, discriminated unions, async
generators, error handling with type narrowing, destructuring,
class and generic patterns, builder and pipeline patterns, or
promise patterns).

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines, \\t for tabs, \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. DO NOT use markdown code blocks in your response

Required JSON fields:
- id: unique numeric identifier
- testsource: "devbench-syntax-completion"
- language: "typescript"
- prefix: code before the completion point (establishes context)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  maintains consistency with prefix/suffix
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  edge case not spelled out in comments
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must compile and execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require resolving at least two syntactic
   constraints (brace matching, type consistency, generic threading)

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid TypeScript that compiles with tsc
2. Do not place executable statements at module top level
   outside of functions (imports, type aliases, interface and
   class definitions, and constant declarations are allowed)
3. All code blocks must have matching braces
4. Include only imports that are actually used
5. Use // Run assertions comment style for assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-syntax-completion", "language":
"typescript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion resolve multiple syntactic constraints?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""
