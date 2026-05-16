API_USAGE_SYSTEM_PROMPT = """
You are an expert Java benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Java API Usage instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly use a
common but error-prone JDK standard library API under realistic
context constraints, including parameter ordering, resource
management, error handling, type conversions, API-specific
conventions, and edge cases.

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
  - language: "java"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    API Usage task

Requirements:

1. Realistic API usage.
   Use APIs from the JDK standard library reflecting
   telemetry-observed completion scenarios. Representative
   domains include:
   - DateTimeFormatter: uuuu vs yyyy in STRICT mode, resolver
     styles (SMART clamps, LENIENT overflows, STRICT rejects),
     withResolverStyle chaining, era-aware year-of-era semantics
   - ConcurrentHashMap and Map methods: compute vs merge vs
     computeIfAbsent, null-return removal semantics, atomic
     read-modify-write, Integer::sum remapping
   - Collections wrappers: unmodifiableList live-view vs
     List.copyOf snapshot, synchronizedList iteration safety,
     Arrays.asList fixed-size write-through
   - Base64 encoder variants: getEncoder vs getUrlEncoder vs
     getMimeEncoder, + to - and / to _ substitutions,
     withoutPadding chaining, RFC references
   - Pattern/Regex flags: CASE_INSENSITIVE ASCII-only without
     UNICODE_CASE, DOTALL line-terminator matching, MULTILINE
     anchor semantics
   - Stream reduce and collectors: three-arg reduce with
     identity/accumulator/combiner, groupingBy with downstream
     collectors, Collectors.counting return types
   - MessageDigest and security: getInstance algorithm names,
     update/digest byte arrays, BigInteger hex formatting
   - Files and NIO: CREATE_NEW exclusive semantics vs CREATE,
     FileAlreadyExistsException, line separator behavior
   - Optional: orElse eager evaluation vs orElseGet lazy,
     map/flatMap chaining, empty-stream semantics
   - AtomicInteger: getAndIncrement vs incrementAndGet
     pre/post semantics, getAndSet return value
   The API call should be embedded in a plausible function, class,
   or workflow, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (type compatibility,
   resource lifecycle, error-path behavior, parameter ordering,
   boundary conditions, or consistency with a helper method). The
   task should not be solvable by copying a nearby line. Avoid
   textbook-perfect toy examples; include realistic engineering
   context such as fallback behavior or resource cleanup.

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
   unavailable external services or third-party libraries,
   near-duplicated from public benchmarks, solvable by a single
   obvious keyword, dominated by boilerplate rather than API
   reasoning, invalid Java, or overly simplified textbook
   implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

API_USAGE_USER_PROMPT = """
Generate one Java API Usage evaluation instance. Choose a domain
from the representative list in the system prompt (DateTimeFormatter,
ConcurrentHashMap, Collections wrappers, Base64 encoders, Pattern
flags, Stream reduce/collectors, MessageDigest, Files/NIO,
Optional, or AtomicInteger).

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
- language: "java"
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
3. Include helper methods, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a public class. Do not place statements
   outside class bodies. The class must have a main method or
   appropriate entry point.
2. All code blocks must have matching braces
3. Include only imports that are actually used
4. The code must compile via javac and execute successfully

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-api-usage", "language":
"java", "prefix": "...", "suffix": "...",
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
You are an expert Java benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Java Code Purpose
Understanding instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model
can infer and continue complex business logic by reading
surrounding code, coordinating multiple coupled invariants,
side effects, and domain rules.

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
  - language: "java"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code Purpose Understanding task

Requirements:

1. Realistic multi-invariant business workflows.
   The task must require reading existing code to understand its
   purpose, then completing a method that coordinates multiple
   coupled side effects. Representative domains include:
   - Healthcare claim adjudication: idempotency before denial
     checks, primary-payer offsets, preventive-line bypass,
     copay/deductible/coinsurance waterfall, OOP cap clamping
   - Payroll processing with BigDecimal: pre-tax retirement
     caps, marginal tax brackets, garnishment on post-tax,
     minimum net clamping (reduce garnishment then deductions),
     YTD accumulators
   - Inventory management (FEFO): quarantine filtering, minimum
     shelf-life, FEFO ordering, atomic no-backorder failure,
     partial backorder mutation, lot cleanup, audit trails
   - Pharmacy fill workflows: early-refill thresholds with
     integer truncation, controlled substance limits, denial
     reason codes, one-shot expedited exceptions
   - Insurance/entitlement ledgers: active grant windows,
     deny-entry reservation, insufficient entitlement atomicity,
     consumption with audit logging
   - Usage billing: unbilled event selection, minimum commit,
     FIFO credit consumption with partial bucket remainder,
     event marking, invoice generation
   - Escrow and loan servicing: cumulative vs delta payments,
     retainage, defect-blocked reserves, holdback release,
     fees-interest-principal waterfall, charged-off routing
   - Lab result interpretation: inclusive/exclusive boundaries,
     panic/normal/abnormal ranges, delta checks against
     previous values, first-result handling

2. Difficulty.
   The completion must coordinate at least three coupled
   invariants (e.g., idempotency + validation ordering +
   accumulator updates + audit side effects). The model must
   READ the existing code to understand the purpose, not just
   match syntax. Avoid tasks solvable by local pattern matching.

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
   by boilerplate rather than business logic reasoning, invalid
   Java, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
Generate one Java Code Purpose Understanding evaluation instance.
Choose a domain from the representative list in the system prompt
(healthcare adjudication, payroll processing, inventory FEFO,
pharmacy fills, entitlement ledgers, usage billing, escrow/loan
servicing, or lab result interpretation).

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
- language: "java"
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
4. The completion must coordinate at least three coupled
   invariants from the surrounding code

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper methods, data classes, or domain structures
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a public class. Do not place statements
   outside class bodies. The class must have a main method or
   appropriate entry point.
2. All code blocks must have matching braces
3. Include only imports that are actually used
4. The code must compile via javac and execute successfully

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code-purpose-understanding",
"language": "java", "prefix": "...", "suffix": "...",
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

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert Java benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Java Code2NL/NL2Code
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can produce
precise Javadoc documentation for existing code or implement
code from detailed documentation, requiring exact API names,
behavioral semantics, and edge-case descriptions rather than
generic summaries.

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
  - language: "java"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code2NL/NL2Code task

Requirements:

1. Precise Javadoc documentation and implementation.
   Tasks must require specific technical details, not generic
   descriptions. Representative domains include:
   - Collections behavioral semantics: sort stability guarantees
     (TimSort, compareToIgnoreCase), live-view vs snapshot
     (subList backed by original, unmodifiableList vs copyOf),
     Arrays.asList fixed-size write-through
   - Map operation precision: Map.merge null-return removal,
     compute three-way branching, ConcurrentHashMap atomicity
   - Stream API contracts: reduce identity/accumulator/combiner,
     parallel correctness requirements, empty-stream behavior,
     Collectors.groupingBy downstream types
   - Thread safety documentation: synchronizedList iteration
     requiring manual synchronization,
     ConcurrentModificationException risks
   - Optional semantics: orElse eager vs orElseGet lazy
     evaluation, chaining behavior
   - String pool mechanics: intern() reference identity via ==,
     memory implications
   - Atomic operations: getAndIncrement vs incrementAndGet
     pre/post value semantics, getAndSet return behavior
   - PriorityQueue: iterator() does not guarantee sorted order,
     poll() vs iterator distinction
   - Defensive copying: creating copies before sorting to
     preserve input immutability
   - Case-insensitive dedup: insertion-order preservation with
     LinkedHashSet, lowercasing strategy

2. Difficulty.
   The completion should require specifying at least two precise
   behavioral details that generic descriptions would omit (exact
   API method names, exception types, thread-safety caveats,
   mutability semantics, or performance characteristics). The
   task should not be solvable with a one-line generic summary.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. For
   documentation tasks, use substring checks for required
   keywords. For implementation tasks, verify functional behavior.
   Include at least one edge case. Assertions must not hard-code
   or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than documentation precision, invalid
   Java, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

NL2CODE_CODE2NL_USER_PROMPT = """
Generate one Java Code2NL/NL2Code evaluation instance. Choose a
domain from the representative list in the system prompt
(Collections semantics, Map operations, Stream contracts, thread
safety, Optional, String pool, Atomic operations, PriorityQueue,
defensive copying, or case-insensitive dedup).

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
- language: "java"
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
4. The completion should require at least two precise behavioral
   details that a generic summary would omit

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include the implementation or documentation to translate
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a public class. Do not place statements
   outside class bodies. The class must have a main method or
   appropriate entry point.
2. All code blocks must have matching braces
3. Include only imports that are actually used
4. The code must compile via javac and execute successfully

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language":
"java", "prefix": "...", "suffix": "...",
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

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert Java benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Java Low Context
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can
complete code correctly from minimal surrounding context,
requiring recognition of Java-specific idioms and API
conventions from very few cues.

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
  - language: "java"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Low Context task

Requirements:

1. Low-context Java idioms.
   The combined prefix and suffix should be only 10-20 lines
   total, providing minimal but sufficient cues. Representative
   domains include:
   - Custom encoding with familiar names: base58Encode,
     base64Encode, base32Encode, base16Encode, ascii85Encode
     with reversed or non-standard alphabets where models
     retrieve standard implementations instead
   - Documentation precision over visible code: Javadoc
     requiring exact API names (Collections.sort with
     compareToIgnoreCase, TimSort stability), live-view
     semantics (unmodifiableList, subList backed-by), or
     UnsupportedOperationException details
   - Collections views: LinkedHashMap access-order LRU with
     removeEldestEntry, Arrays.asList fixed-size aliasing
     and write-through mutation
   - Map.compute null-return removal: three-way branching
     where null return removes the key entirely
   - AtomicInteger: getAndSet return semantics, mutation
     details, current-value reporting
   - TreeMap navigation: floorEntry greatest-key-less-than-
     or-equal semantics, null behavior for missing entries

2. Difficulty.
   The completion should require understanding a Java-specific
   convention or API subtlety that is not obvious from the
   minimal context alone. The model must resolve at least two
   constraints (e.g., non-standard alphabet + padding rules,
   or exact API name + behavioral detail). Encoding tasks must
   use non-standard alphabets so standard retrieval fails.

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
   by boilerplate rather than Java idiom recognition, invalid
   Java, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

LOW_CONTEXT_USER_PROMPT = """
Generate one Java Low Context evaluation instance. Choose a
domain from the representative list in the system prompt (custom
encoding with familiar names, documentation precision, Collections
views, Map.compute null-removal, AtomicInteger semantics, or
TreeMap navigation).

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
- language: "java"
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

LOW CONTEXT REQUIREMENTS:
1. The prefix and suffix combined MUST be only 10-20 lines total
2. Provide minimal but sufficient cues for the completion
3. Keep context deliberately short while maintaining inferability

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a public class. Do not place statements
   outside class bodies. The class must have a main method or
   appropriate entry point.
2. All code blocks must have matching braces
3. Include only imports that are actually used
4. The code must compile via javac and execute successfully

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-low-context", "language":
"java", "prefix": "...", "suffix": "...",
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

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert Java benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Java Pattern Matching
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can implement
a custom pattern transformation by following examples established
in the prefix, rather than retrieving a memorized standard
algorithm.

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
  - language: "java"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Pattern Matching task

Requirements:

1. Stateful parsing and custom transformations.
   Tasks must require following a pattern established in the
   prefix, not retrieving a standard algorithm. Representative
   domains include:
   - Line-continuation parsing: backslash continuation in config
     files (properties, INI, env, Makefile, aliases), joining
     physical lines into logical lines before processing
   - Quote-aware comment stripping: handling comments inside
     quoted strings vs outside, distinguishing # in values
   - Section-prefixed config: INI-style [section] headers with
     dot-prefixed key output (section.key=value)
   - Folded headers: RFC-style continuation where leading
     whitespace indicates header folding, with lowercasing
     and ordered multi-value accumulation
   - Variable expansion: Makefile-style $(VAR) or ${VAR}
     substitution with append semantics (+=)
   - Custom edit distance: non-standard costs (transposition
     cost != substitution, weighted per-character-type costs)
     where standard Levenshtein retrieval fails
   - Bracket depth counting: tracking nesting depth while
     skipping brackets inside string literals with escape
     handling
   - Custom URL normalization: non-standard rules (conditional
     trailing slash, no parameter sorting) where models
     retrieve RFC-standard behavior
   - Custom URL encoding: encoding ALL non-alphanumerics
     including ~ and *, using %20 instead of + for spaces,
     where models retrieve java.net.URLEncoder behavior
   - Check digit algorithms: weighted Hamming distance with
     per-character-type costs, custom checksums

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (continuation semantics +
   comment handling, or custom alphabet + non-standard costs).
   The task must not be solvable by retrieving a standard library
   implementation. Include familiar function names that trigger
   wrong standard retrieval.

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
   by boilerplate rather than pattern-following reasoning,
   invalid Java, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

PATTERN_MATCHING_USER_PROMPT = """
Generate one Java Pattern Matching evaluation instance. Choose a
domain from the representative list in the system prompt
(line-continuation parsing, quote-aware comments, section-prefixed
config, folded headers, variable expansion, custom edit distance,
bracket depth counting, custom URL normalization, custom URL
encoding, or check digit algorithms).

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
- language: "java"
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
3. Include pattern examples or helper methods
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a public class. Do not place statements
   outside class bodies. The class must have a main method or
   appropriate entry point.
2. All code blocks must have matching braces
3. Include only imports that are actually used
4. The code must compile via javac and execute successfully

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-pattern-matching", "language":
"java", "prefix": "...", "suffix": "...",
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

SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert Java benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Java Syntax Completion
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can complete
complex, deeply nested Java syntax structures that require
precise understanding of modern Java language features.

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
  - language: "java"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Syntax Completion task

Requirements:

1. Complex Java syntax structures.
   Tasks must test genuine syntax mastery of modern Java
   features, not algorithm knowledge. Representative domains
   include:
   - Sealed classes and interfaces: exhaustive switch expressions
     over sealed hierarchies, permits clauses, non-sealed
     extensions
   - Record patterns: destructuring records in switch cases
     (Num(var v), Add(var l, var r)), recursive pattern
     matching, nested record access
   - Switch expressions: arrow-form vs block-form with yield,
     guard clauses (case X when condition), mixing arrow and
     block styles, deeply nested switches (3+ levels)
   - Complex generics: F-bounded polymorphism
     (Builder<T, B extends Builder<T, B>>), recursive type
     bounds, wildcard captures, self-referential generics
   - Stream collector chains: Collectors.teeing with two
     downstream collectors and merger, groupingBy with
     collectingAndThen and maxBy, nested collector composition,
     summingDouble inside groupingBy
   - Try-with-resources: multiple AutoCloseable resources in
     one try header, suppressed exception handling via
     getSuppressed(), conditional throws with catch inspection
   - Deeply nested lambdas: flatMap with inner streams,
     Map.entry construction inside lambdas, unclosed paren
     chains requiring precise bracket matching

2. Difficulty.
   The completion should require resolving at least two syntactic
   constraints (e.g., exhaustive case coverage + recursive
   destructuring, or nested collector types + correct paren
   closing). The task must test SYNTAX mastery, not algorithm
   knowledge. Include mid-expression completions where the cursor
   is inside nested brackets or after partial expressions.

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
   by boilerplate rather than syntax reasoning, invalid Java, or
   overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

SYNTAX_COMPLETION_USER_PROMPT = """
Generate one Java Syntax Completion evaluation instance. Choose a
domain from the representative list in the system prompt (sealed
classes, record patterns, switch expressions, complex generics,
stream collector chains, try-with-resources, or deeply nested
lambdas).

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
- language: "java"
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
   syntactic constraints from prefix/suffix

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include type definitions, sealed hierarchies, or helper code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a public class. Do not place statements
   outside class bodies. The class must have a main method or
   appropriate entry point.
2. All code blocks must have matching braces
3. Include only imports that are actually used
4. The code must compile via javac and execute successfully

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-syntax-completion", "language":
"java", "prefix": "...", "suffix": "...",
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
