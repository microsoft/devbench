API_USAGE_SYSTEM_PROMPT = """
You are an expert JavaScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality JavaScript API Usage instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly use a
common but error-prone Node.js or JavaScript API under realistic
context constraints, including parameter ordering, encoding
semantics, resource lifecycle, error handling, type coercion,
API-specific conventions, and edge cases.

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
  - language: "javascript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    API Usage task

Requirements:

1. Realistic API usage.
   Use APIs from Node.js built-in modules and core JavaScript,
   reflecting telemetry-observed completion scenarios.
   Representative domains include:
   - crypto: scryptSync options, createCipheriv/Decipher with
     GCM auth tags, timingSafeEqual length constraints, Hash.copy
     for incremental digests, randomInt bounds
   - Buffer: from() encoding leniency (base64 padding, hex),
     alloc zero-fill, compare sort semantics, concat totalLength
     truncation, subarray vs slice copy semantics
   - stream: Transform lifecycle (_transform/_flush), pipeline
     error propagation, Readable.from async iterables,
     string_decoder for split multi-byte sequences
   - util: promisify.custom symbol override, format specifier
     coercion (%d, %j, %o), types predicate functions, inspect
     custom symbol hooks
   - path: resolve vs join semantics, posix.relative lexical
     computation, normalize edge cases
   - url/querystring: WHATWG URL vs legacy url, URLSearchParams
     sort/getAll, querystring.stringify sep/eq/encodeURIComponent
   - events: EventEmitter error event default throw, newListener
     internal event, setMaxListeners, events.once with
     AbortSignal
   - fs: openSync flags (wx exclusive), mkdtempSync path
     requirements, readFileSync encoding
   - zlib: deflateRawSync vs deflateSync header differences,
     brotliCompressSync parameter constants
   - Atomics: add returns old value, wait/notify semantics,
     SharedArrayBuffer requirements
   - Intl: NumberFormat percent multiplication, Collator numeric
     sorting, DateTimeFormat options
   - Reflect: construct newTarget argument, ownKeys ordering
   - structuredClone: transfer option for ArrayBuffer,
     non-transferable type errors
   - WeakRef/FinalizationRegistry: deref() undefined semantics,
     GC non-determinism
   - AbortController: abort(reason) custom reasons, signal
     composition
   - perf_hooks: performance.mark/measure API
   The API call should be embedded in a plausible function, class,
   or workflow, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (encoding semantics, error
   path behavior, parameter ordering, type coercion, lifecycle
   management, or consistency with a helper method). The task
   should not be solvable by copying a nearby line. Avoid
   textbook-perfect toy examples; include realistic engineering
   context such as fallback behavior or resource cleanup.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services or npm packages, near-duplicated
   from public benchmarks, solvable by a single obvious keyword,
   dominated by boilerplate rather than API reasoning, invalid
   JavaScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

API_USAGE_USER_PROMPT = """
Generate one JavaScript API Usage evaluation instance. Choose a
domain from the representative list in the system prompt (crypto,
Buffer, stream, util, path, url/querystring, events, fs, zlib,
Atomics, Intl, Reflect, structuredClone, WeakRef, AbortController,
or perf_hooks).

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
- language: "javascript"
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
   must execute successfully
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
3. Include helper functions, require() calls, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid Node.js JavaScript
2. Use const/let (not var) and require() or import for modules
3. Do not place executable statements outside of function bodies
   or immediately-invoked expressions; top-level require() calls,
   const/let declarations, and function/class definitions are fine
4. All code blocks must have matching braces
5. Include only modules that are actually used
6. Use // Run assertions comment style before assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-api-usage", "language":
"javascript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the golden_completion resolve multiple context constraints?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

CODE_PURPOSE_UNDERSTANDING_SYSTEM_PROMPT = """
You are an expert JavaScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality JavaScript Code Purpose
Understanding instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model can
read surrounding code to understand its business logic and domain
purpose, then produce a completion that coordinates coupled state
mutations, respects invariant ordering, and maintains idempotency
or audit-trail requirements established in the prefix.

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
  - language: "javascript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code Purpose Understanding task

Requirements:

1. Multi-invariant business logic.
   The completion must coordinate at least three coupled
   constraints. Use class-based state machines and closures
   that reflect real-world domains. Representative domains
   include:
   - Subscription/account lifecycle: state machine transitions
     (pending/active/suspended/cancelled), activation timestamps,
     audit logging of each transition
   - Payment/billing waterfall: fees-before-interest-before-
     principal ordering, partial allocation, idempotent ledger
     entries, balance reconciliation
   - Insurance adjudication: copay/deductible/coinsurance
     waterfall, out-of-pocket caps, member-pay capping
   - Inventory management: FEFO batch picking with expiry
     filtering, atomic rollback on insufficient stock, cross-
     batch allocation, lot number sequencing
   - Scheduling/booking: buffer-time overlap detection, waitlist
     FIFO promotion on cancellation, double-booking prevention,
     capacity enforcement
   - Tax/payroll: progressive bracket calculation, pre-tax
     deductions, YTD accumulator tracking
   - Gift card/voucher lifecycle: activation guard, partial
     redemption, expiry enforcement, reload with balance cap
   - Voting/approval workflows: weighted quorum vs threshold
     distinction, abstention semantics
   - Commission/referral tracking: tiered rates, quarterly caps,
     clawback on cancellation, chain traversal with depth limits
   - Warranty/SLA tracking: paused-time exclusion, breach
     detection, claim limits per period

2. Difficulty.
   The completion must coordinate at least three interacting
   invariants (e.g., validation ordering + accumulator updates +
   idempotency guard + audit logging). The task should not be
   solvable by reading a single line or by pattern-matching
   syntax alone. Include at least one non-obvious ordering
   dependency where doing steps out of order produces wrong
   results.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

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
   JavaScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
Generate one JavaScript Code Purpose Understanding evaluation
instance. Choose a domain from the representative list in the
system prompt (subscription lifecycle, payment waterfall,
insurance adjudication, inventory management, scheduling,
tax/payroll, gift card lifecycle, voting workflows, commission
tracking, or warranty/SLA tracking).

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
- language: "javascript"
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
   must execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require coordinating at least three
   coupled invariants from the prefix

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context: class definition, constructor,
   helper methods, state variables, and comments
3. The prefix should demonstrate an incomplete implementation
   whose business logic the model must continue

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid Node.js JavaScript
2. Use const/let (not var) and require() or import for modules
3. Do not place executable statements outside of function bodies
   or immediately-invoked expressions; top-level require() calls,
   const/let declarations, and function/class definitions are fine
4. All code blocks must have matching braces
5. Include only modules that are actually used
6. Use // Run assertions comment style before assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code-purpose-understanding",
"language": "javascript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the completion coordinate at least three invariants?
6. Is there a non-obvious ordering dependency?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert JavaScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality JavaScript Code2NL/NL2Code
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can produce
precise technical documentation (JSDoc) for existing code, or
implement code from detailed natural-language specifications,
capturing exact behavioral details that generic descriptions miss.

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
  - language: "javascript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code2NL/NL2Code task

Requirements:

1. Precise documentation or implementation.
   For Code2NL tasks: the model must produce JSDoc or inline
   documentation that captures specific behavioral details --
   not generic descriptions like "processes input and returns
   result." For NL2Code tasks: the model must implement code
   from a detailed specification with non-obvious edge cases.
   Representative domains include:
   - In-place mutation semantics: functions that modify the
     passed object/array and return it (vs creating copies)
   - Retry/backoff strategies: exponential delay doubling,
     last-error re-throw, attempt counting
   - Cache semantics: LRU promotion side-effects of get(),
     eviction callbacks, delete-and-re-set ordering
   - Collection grouping: null/undefined key fallbacks,
     alphabetical key sorting, stable within-group ordering
   - Priority event systems: higher-first ordering, registration
     order tiebreaking, method chaining returns
   - Deep freeze with cycle detection: WeakSet tracking,
     plain-object-only constraints, same-reference return
   - Debounce/throttle: leading vs trailing edge semantics,
     timer reset behavior, cancel methods
   - Promise settlement: allSettled result shapes
     ({status, value/reason}), never-reject guarantees,
     non-promise coercion, empty-array edge case
   - Stable partition: in-place mutation, predicate call count,
     split-index return value
   - Property descriptor copying: Reflect.ownKeys, symbols,
     non-enumerables, accessor preservation
   - Observable/stream patterns: lazy evaluation, backpressure
     semantics, cleanup on unsubscribe
   - Template engines: placeholder syntax, filter pipes,
     escaping conventions

2. Difficulty.
   For Code2NL: the documentation must require mentioning at
   least three specific behavioral details that a generic
   description would omit. For NL2Code: the implementation must
   require handling at least two non-obvious edge cases from
   the specification. The task should not be solvable by writing
   a single generic sentence or a trivial function body.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. For Code2NL:
   assertions should check for presence of specific keywords or
   phrases in the generated documentation using string includes
   checks. For NL2Code: assertions should verify functional
   behavior. Include at least one edge case not explicitly
   described in comments. Assertions must not hard-code or leak
   the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than documentation precision or
   implementation reasoning, invalid JavaScript, or overly
   simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

NL2CODE_CODE2NL_USER_PROMPT = """
Generate one JavaScript Code2NL/NL2Code evaluation instance.
Choose a domain from the representative list in the system prompt
(mutation semantics, retry/backoff, cache semantics, collection
grouping, priority events, deep freeze, debounce/throttle,
promise settlement, stable partition, descriptor copying,
observable patterns, or template engines).

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
- language: "javascript"
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
   must execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. For Code2NL: the completion is JSDoc or documentation text
   requiring at least three specific behavioral details
5. For NL2Code: the completion is implementation code requiring
   at least two non-obvious edge case handlers

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include the function signature, visible implementation or
   specification comments, and related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid Node.js JavaScript
2. Use const/let (not var) and require() or import for modules
3. Do not place executable statements outside of function bodies
   or immediately-invoked expressions; top-level require() calls,
   const/let declarations, and function/class definitions are fine
4. All code blocks must have matching braces
5. Include only modules that are actually used
6. Use // Run assertions comment style before assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language":
"javascript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the documentation/implementation capture non-obvious
   behavioral details?
6. Is the task non-trivial and not solvable by a generic sentence?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert JavaScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality JavaScript Low Context
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can complete
code correctly from minimal surrounding context (10-20 lines
total), relying on language idiom recognition and precise
reading of the visible code rather than extensive scaffolding.

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
  - language: "javascript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Low Context task

Requirements:

1. Minimal-context JavaScript patterns.
   The prefix and suffix combined should be only 10-20 lines.
   The task tests recognition of JavaScript idioms and precise
   reading of visible constants or helper code. Representative
   domains include:
   - Custom encoding with familiar names: base58/62/64/85
     encode functions with reversed or non-standard alphabets
     where the function name triggers standard retrieval but
     the visible alphabet differs
   - Proxy and Reflect patterns: has/get/set/deleteProperty
     traps, schema validation proxies, revocable proxies
   - WeakMap/WeakRef private data: per-instance metadata via
     WeakMap, lazy initialization, access counting
   - Higher-order function variants: scan (generator yielding
     intermediate accumulations), partition with reversed
     ordering, first-wins merge (opposite of Object.assign),
     flatMap with reversed sub-arrays
   - Generator and iterator protocols: Symbol.iterator with
     custom traversal, yield* delegation, bidirectional
     communication via next(value)
   - Non-standard collection semantics: LRU with eviction,
     inclusive-end range, cycling zip (pad shorter arrays
     by cycling), last-occurrence uniqueness
   - Value object patterns: valueOf/toString asymmetry
     (different units), Symbol.toPrimitive with hint dispatch
   - Modular arithmetic variants: Fibonacci with modulus,
     sequences with non-standard recurrence
   - Deep freeze with circular reference handling via WeakSet
   - JSON.stringify replacer with dual behaviors

2. Difficulty.
   The completion should require precise reading of the visible
   prefix/suffix -- especially constant definitions, alphabet
   strings, or helper function behavior -- rather than relying
   on preconceived standard implementations. The task should
   cause models to retrieve a standard implementation that
   conflicts with the visible non-standard specification.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

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
   by boilerplate rather than idiom-level reasoning, invalid
   JavaScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

LOW_CONTEXT_USER_PROMPT = """
Generate one JavaScript Low Context evaluation instance. Choose
a domain from the representative list in the system prompt
(custom encoding, Proxy/Reflect, WeakMap/WeakRef, higher-order
function variants, generator protocols, non-standard collection
semantics, value object patterns, modular arithmetic variants,
deep freeze, or JSON.stringify replacer).

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
- language: "javascript"
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
   must execute successfully
6. Include at least one edge case assertion

CRITICAL LOW CONTEXT REQUIREMENTS:
1. The prefix and suffix combined MUST be only 10-20 lines total
2. Keep context deliberately minimal while ensuring the task is
   inferable from the visible code
3. The completion should be 3-12 lines

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require precise reading of visible
   constants or helpers, not standard algorithm retrieval

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid Node.js JavaScript
2. Use const/let (not var) and require() or import for modules
3. Do not place executable statements outside of function bodies
   or immediately-invoked expressions; top-level require() calls,
   const/let declarations, and function/class definitions are fine
4. All code blocks must have matching braces
5. Include only modules that are actually used
6. Use // Run assertions comment style before assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-low-context", "language":
"javascript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Is the prefix + suffix combined only 10-20 lines?
6. Does the task exploit a preconception trap (standard vs
   non-standard behavior)?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert JavaScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality JavaScript Pattern
Matching instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model
can follow an established code pattern in the prefix -- such as
a custom encoding scheme, parser convention, or data
transformation protocol -- rather than retrieving a memorized
standard implementation.

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
  - language: "javascript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Pattern Matching task

Requirements:

1. Pattern-following with preconception traps.
   The prefix must establish a clear pattern through 2-3 examples,
   and the completion must follow that pattern rather than a
   memorized standard. The function name should trigger retrieval
   of a well-known standard behavior that conflicts with the
   established pattern. Representative domains include:
   - Custom base encoding: base64/58/62/32/26/85/94 with reversed
     or non-standard alphabets, integer-style byte conversion,
     custom padding characters, leading-zero byte preservation
   - HTML/URL escaping variants: numeric entities (&#DD;) instead
     of named entities (&amp;), custom safe-character sets,
     lowercase hex encoding, space-to-plus conversion
   - Template engines: #{...} syntax with nesting support,
     escape sequences (## for literal #), stateful character-by-
     character parsing instead of regex
   - Deep equality variants: Object.is semantics (NaN === NaN,
     -0 !== +0), Date/RegExp/Set/Map comparison, array-as-set
     comparison (order-insensitive)
   - Priority event systems: descending priority order (not
     FIFO), once() removal before callback execution for
     re-entrant safety, handler result collection
   - Pipeline with recovery: error passed as second argument to
     next function instead of throwing, error wrapping
   - Custom memoization: placeholder-aware currying, FIFO
     eviction instead of LRU, all-args cache key
   - Collection utilities: ring buffer with newest-overwrite
     (not oldest), sliding window with step parameter,
     concurrent task pool (not batched)
   - Checksum/hash: XOR accumulation with hex grouping, custom
     rotation constants following bit-width pattern

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix pattern (alphabet selection, byte
   conversion logic, padding rules, ordering semantics, or
   metadata format). The task should cause models to retrieve a
   standard implementation that conflicts with the established
   prefix pattern.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior, not just syntax. Include at least
   one anti-standard assertion that explicitly checks the output
   differs from the standard implementation. Assertions must not
   hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than pattern-following reasoning,
   invalid JavaScript, or overly simplified textbook
   implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

PATTERN_MATCHING_USER_PROMPT = """
Generate one JavaScript Pattern Matching evaluation instance.
Choose a domain from the representative list in the system prompt
(custom base encoding, HTML/URL escaping variants, template
engines, deep equality variants, priority event systems, pipeline
with recovery, custom memoization, collection utilities, or
checksum/hash).

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
- language: "javascript"
- prefix: code before the completion point (MUST establish a
  clear pattern through 2-3 examples)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  follows the established prefix pattern
- assertions: hidden executable test code used ONLY for
  evaluation; the model under test will never see this field;
  must validate functional behavior and include at least one
  anti-standard assertion
- LLM_justification: why this is a realistic, challenging task

CRITICAL: HIDDEN ASSERTION REQUIREMENTS:
1. All functional test code must go in the "assertions" field
2. The "assertions" field must NOT be empty
3. Do NOT place hidden tests in the prefix or suffix
4. Assertions must not hard-code or leak the golden completion
5. The combined prefix + golden_completion + suffix + assertions
   must execute successfully
6. Include at least one anti-standard edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix must establish the pattern with 2-3 concrete
   examples before the completion point
4. The completion should follow the prefix pattern, not a
   memorized standard implementation

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide pattern-establishing context: helper functions,
   constants, and 2-3 completed examples of the pattern
3. The prefix should demonstrate an incomplete implementation
   where the pattern is clear but the next step is non-trivial

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid Node.js JavaScript
2. Use const/let (not var) and require() or import for modules
3. Do not place executable statements outside of function bodies
   or immediately-invoked expressions; top-level require() calls,
   const/let declarations, and function/class definitions are fine
4. All code blocks must have matching braces
5. Include only modules that are actually used
6. Use // Run assertions comment style before assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-pattern-matching", "language":
"javascript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the prefix establish a clear pattern with 2-3 examples?
6. Would a standard implementation of the named function FAIL
   the assertions?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion verify anti-standard behavior?
"""

SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert JavaScript benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality JavaScript Syntax
Completion instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model
can produce syntactically correct code in deeply nested or
structurally complex JavaScript constructs, where bracket
matching, keyword placement, and scope management are
genuinely challenging.

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
  - language: "javascript"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Syntax Completion task

Requirements:

1. Complex JavaScript syntax.
   The completion should require mastery of deeply nested or
   structurally complex JavaScript-specific syntax patterns.
   Representative domains include:
   - Async generators: async function* with yield inside
     try/catch/finally, for-await-of, yield* delegation,
     consumer .throw() forwarding
   - Proxy and Reflect: handler objects with multiple traps
     (get, set, deleteProperty, has), Proxy.revocable(),
     nested trap logic with type checking
   - Symbol protocols: Symbol.iterator with custom traversal,
     Symbol.asyncIterator, Symbol.toPrimitive with hint
     dispatch, Symbol.species in subclasses
   - Deep destructuring: computed property keys ([fallbackKey]),
     property renaming (url: dbUrl), nested defaults at
     multiple levels, rest syntax in nested positions,
     array destructuring inside object destructuring
   - Promise chain nesting: Promise.allSettled with inner
     retry chains, Promise constructor with shared mutable
     state, nested .then/.catch/.finally
   - Private fields and methods: #field syntax, WeakRef and
     FinalizationRegistry interactions, method chaining with
     private state
   - Class syntax: multi-level inheritance with super() and
     computed arguments, static blocks, mixin patterns with
     prototype manipulation
   - Generator state machines: while(true) with switch/case,
     bidirectional communication via yield/next(value),
     generator delegation with yield*
   - Tagged template literals: tag function with strings/values
     arrays, recursive processing, type-based dispatch
   - Callback nesting: error-first convention with multiple
     nested levels, proper error propagation with early return
   - Logical assignment operators: ??=, ||=, &&= with nuanced
     falsy/nullish semantics
   - Optional chaining depth: ?.[], ?.(), chained across
     multiple levels with nullish coalescing (??)

2. Difficulty.
   The completion should require managing at least 4 levels of
   nesting or 3 interacting syntax features simultaneously. The
   task should test genuine syntax mastery, not algorithm
   knowledge. Bracket matching, scope tracking, and keyword
   placement must be non-trivial.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

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
   by boilerplate rather than syntax reasoning, invalid
   JavaScript, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

SYNTAX_COMPLETION_USER_PROMPT = """
Generate one JavaScript Syntax Completion evaluation instance.
Choose a domain from the representative list in the system prompt
(async generators, Proxy/Reflect, Symbol protocols, deep
destructuring, Promise chain nesting, private fields, class
syntax, generator state machines, tagged template literals,
callback nesting, logical assignment operators, or optional
chaining depth).

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
- language: "javascript"
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
   must execute successfully
6. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require managing at least 4 nesting
   levels or 3 interacting syntax features

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include function signatures, class definitions, or related
   code that establishes the nesting depth
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be valid Node.js JavaScript
2. Use const/let (not var) and require() or import for modules
3. Do not place executable statements outside of function bodies
   or immediately-invoked expressions; top-level require() calls,
   const/let declarations, and function/class definitions are fine
4. All code blocks must have matching braces
5. Include only modules that are actually used
6. Use // Run assertions comment style before assertion blocks

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-syntax-completion", "language":
"javascript", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the completion manage at least 4 nesting levels or 3
   interacting syntax features?
6. Is the task testing syntax mastery, not algorithm knowledge?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""
