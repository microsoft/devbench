SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert C# benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C# Syntax Completion
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can correctly
complete complex syntactical structures and nested language
constructs specific to modern C#, including proper nesting,
indentation, type annotations, and control flow.

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
  - language: "c_sharp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Syntax Completion task

Requirements:

1. Realistic syntax scenarios.
   Use modern C# syntax features that developers encounter in
   production code. Representative domains include:
   - Switch expressions with record type patterns, property
     patterns, when guards, and positional destructuring
   - Record types with inheritance hierarchies, Deconstruct,
     and with-expressions
   - LINQ query syntax: let bindings, group-into, join, orderby
     with tiebreakers, and method-syntax GroupJoin
   - Generic methods and classes with multiple constraints
     (IComparable<T>, class, new(), struct)
   - Async iterators: yield return inside async methods, await
     using, await foreach, and cancellation
   - Iterator blocks: yield return with try/finally, using
     declarations, and yield break control flow
   - Tuple patterns and deconstruction in switch expressions
     with when guards and wildcard patterns
   - C# 11 list patterns with discard (..) and exact-length
     matching in switch arms
   - Nested Func delegates with closure capture and composition
   - Collection initializers with target-typed new and nested
     member initializers
   - Null-conditional chaining (?.) with TryGetValue patterns
   - String interpolation with format specifiers inside LINQ
   The syntax feature should be embedded in a plausible class or
   method, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two syntactic
   constraints from the prefix/suffix (pattern exhaustiveness,
   correct nesting depth, type annotation consistency, control
   flow interaction with resource disposal, or arm ordering).
   The task should not be solvable by copying a nearby line.
   Avoid textbook-perfect toy examples.

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
   by boilerplate rather than syntax reasoning, invalid C#, or
   overly simplified textbook implementations.

CODE STRUCTURE: All code must be within a namespace and class.
Do not place statements outside class bodies. Use `using`
directives for namespace imports.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

SYNTAX_COMPLETION_USER_PROMPT = """
Generate one C# Syntax Completion evaluation instance. Choose a
domain from the representative list in the system prompt (switch
expressions, records, LINQ, generics, async iterators, iterator
blocks, tuple patterns, list patterns, closures, collection
initializers, or null-conditional chaining).

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
- language: "c_sharp"
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
3. Include helper types, method signatures, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a namespace and class; do not place
   statements outside class bodies
2. Use `using` directives for namespace imports
3. All code blocks must have matching braces
4. Include only using directives that are actually used
5. The code must compile and execute as valid C#

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-syntax-completion", "language":
"c_sharp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion resolve multiple syntax constraints?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert C# benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C# Code2NL/NL2Code
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can accurately
translate between C# code and natural language documentation,
including precise API semantics, edge case behavior, complexity
characteristics, and exception conditions.

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
  - language: "c_sharp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code2NL/NL2Code task

Requirements:

1. Realistic documentation scenarios.
   Use .NET standard library APIs and idiomatic C# patterns
   that require precise documentation or implementation.
   Representative domains include:
   - XML documentation comments (/// summary, param, returns,
     exception, remarks) for methods using LINQ operators
     (Where, Aggregate, GroupBy, Zip, SelectMany)
   - Precise API documentation for collection types:
     ConcurrentDictionary.GetOrAdd (factory execution count),
     SortedSet.GetViewBetween (live view semantics),
     PriorityQueue (min-heap, instability), OrderedDictionary
     (insertion-order index access)
   - Documentation of Span<T>/ReadOnlySpan<T> behavior:
     ref struct constraints, no-allocation slicing, stack-only
   - Documentation of async patterns: ValueTask disposal,
     ConfigureAwait, SynchronizationContext capture
   - NL2Code: implementing methods from XML doc specs using
     Array.Sort with Comparison<T>, Array.FindAll with
     Predicate<T>, custom Deconstruct methods, TypeConverter
   - Documentation of stream/binary patterns: MemoryStream,
     BinaryWriter/BinaryReader, little-endian byte order
   - Documentation of modern C# features: default interface
     methods, record with-expressions, pattern matching in
     switch expressions
   The documentation task should require domain-specific
   precision, not generic "processes input and returns output."

2. Difficulty.
   For Code2NL: the documentation must require naming specific
   API behaviors (e.g., deferred execution, thread-safety
   caveats, exception types, complexity guarantees) that a
   generic description would omit. For NL2Code: the
   implementation must use specific .NET APIs with correct
   signatures, not LINQ-equivalent alternatives.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. For Code2NL
   tasks, assertions check presence of required keywords in the
   generated documentation string. For NL2Code tasks, assertions
   verify functional behavior and edge cases. Include at least
   one edge case not explicitly described in comments. Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than documentation precision, invalid
   C#, or overly simplified textbook implementations.

CODE STRUCTURE: All code must be within a namespace and class.
Do not place statements outside class bodies. Use `using`
directives for namespace imports.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

NL2CODE_CODE2NL_USER_PROMPT = """
Generate one C# Code2NL/NL2Code evaluation instance. Choose a
domain from the representative list in the system prompt (LINQ
documentation, collection API semantics, Span behavior, async
patterns, NL2Code with Array/Sort/FindAll, stream patterns, or
modern C# features).

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
- language: "c_sharp"
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
3. Include helper types, method signatures, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a namespace and class; do not place
   statements outside class bodies
2. Use `using` directives for namespace imports
3. All code blocks must have matching braces
4. Include only using directives that are actually used
5. The code must compile and execute as valid C#

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language":
"c_sharp", "prefix": "...", "suffix": "...",
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
You are an expert C# benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C# Code Purpose
Understanding instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model can
infer business logic and domain intent from surrounding code and
produce a completion that satisfies multiple coupled invariants
simultaneously.

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
  - language: "c_sharp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code Purpose Understanding task

Requirements:

1. Realistic business-logic scenarios.
   Use multi-invariant workflows where the completion must
   coordinate several coupled side effects. Representative
   domains include:
   - Healthcare claim adjudication: idempotency, auth denial
     atomicity, primary-payer offsets, preventive bypass,
     copay/deductible waterfall ordering
   - Inventory allocation: FEFO ordering, quarantine filtering,
     minimum shelf-life gates, atomic failure on insufficiency,
     lot-level tracking
   - Payroll processing: pre-tax retirement caps, marginal tax
     brackets, garnishment-before-health ordering, minimum net
     pay floors, YTD accumulation
   - Insurance underwriting: age-band surcharges, claims
     surcharges, endorsement cap clipping, loyalty discounts
     applied AFTER surcharges, coverage limit enforcement
   - Order fulfillment: cancellation checks, payment capture
     before stock, partial shipment with backorder, shipping
     cost allocation
   - Subscription state machines: trial-to-active gates,
     billing interval enforcement, pause/resume proration,
     grace period routing
   - Financial ledgers: entitlement windows, deny-rule
     reservations, expiring-soonest-first consumption,
     atomic partial failure
   - Escrow and milestone billing: draw capping, retainage
     holdback, defect holdback, final release triggers
   All tasks should use LINQ/collections and decimal arithmetic
   for precise financial calculations. The task should be
   embedded in a plausible business workflow, not isolated logic.

2. Difficulty.
   The completion must satisfy at least three coupled invariants
   (e.g., idempotency + validation ordering + accumulator
   updates). The model must READ the surrounding code to infer
   the required business rules; the task should not be solvable
   from function signatures alone. Avoid tasks where a generic
   implementation would accidentally pass.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. Assertions must
   validate functional behavior across multiple invariants.
   Include at least one edge case not explicitly described in
   comments (e.g., idempotent replay, boundary condition).
   Assertions must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than business-logic reasoning, invalid
   C#, or overly simplified textbook implementations.

CODE STRUCTURE: All code must be within a namespace and class.
Do not place statements outside class bodies. Use `using`
directives for namespace imports.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
Generate one C# Code Purpose Understanding evaluation instance.
Choose a domain from the representative list in the system prompt
(healthcare claims, inventory allocation, payroll, insurance,
order fulfillment, subscriptions, financial ledgers, or escrow
billing).

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
- language: "c_sharp"
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
4. The completion should require satisfying at least three
   coupled business-logic invariants from prefix/suffix

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper types, business entity definitions, or
   related workflow methods
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a namespace and class; do not place
   statements outside class bodies
2. Use `using` directives for namespace imports
3. All code blocks must have matching braces
4. Include only using directives that are actually used
5. The code must compile and execute as valid C#

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code-purpose-understanding",
"language": "c_sharp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion satisfy multiple coupled invariants?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert C# benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C# Low Context instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly complete
code from minimal surrounding context, requiring recognition of
C#-specific idioms, language features, and standard library
patterns from very few cues.

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
  - language: "c_sharp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Low Context task

Requirements:

1. Realistic low-context scenarios.
   Use C#-specific idioms that require recognizing language
   patterns from minimal context. Representative domains include:
   - Span<T> and ReadOnlySpan<T>: stackalloc, slicing with
     range operators ([^2..], [..3]), Reverse, no-allocation
     patterns
   - LINQ idioms: Range+Select+Where, Aggregate with custom
     accumulators, Zip with truncation, SelectMany composition
   - yield return: lazy evaluation, Take(n) early termination,
     filtering iterators, stateful iteration
   - Custom base encoding (base58, base62, base32, base36)
     with reversed or non-standard alphabets
   - Doc precision for low-level idioms: ref struct constraints,
     SynchronizationContext, acquire/release fence, stackalloc
     semantics
   - Record with-expressions and positional deconstruction
   - Nullable patterns: null-coalescing (??), null-conditional
     (?.), HasValue checks
   - Async/await: Task.Yield, ValueTask, ConfigureAwait
   - Generic constraints with nullable return types
   - Switch expressions with type patterns and when guards
   - Named tuple returns and deconstruction
   The context should be deliberately minimal (10-20 total lines
   of prefix + suffix) while testing genuine language knowledge.

2. Difficulty.
   The completion should require recognizing a C#-specific idiom
   that cannot be solved by generic pattern matching. The model
   must understand the semantic meaning of the surrounding code,
   not just its syntactic structure. Avoid tasks where any
   reasonable code would accidentally pass the assertions.

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
   by boilerplate rather than idiom recognition, invalid C#, or
   overly simplified textbook implementations.

CODE STRUCTURE: All code must be within a namespace and class.
Do not place statements outside class bodies. Use `using`
directives for namespace imports.

CRITICAL: Keep the combined prefix + suffix to 10-20 lines total
for true low-context scenarios.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

LOW_CONTEXT_USER_PROMPT = """
Generate one C# Low Context evaluation instance. Choose a domain
from the representative list in the system prompt (Span/stackalloc,
LINQ idioms, yield return, custom encoding, doc precision, records,
nullable patterns, async/await, generics, switch expressions, or
named tuples).

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
- language: "c_sharp"
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
4. The completion should require recognizing a C#-specific idiom

LOW CONTEXT REQUIREMENTS:
1. The prefix and suffix combined MUST be only 10-20 lines total
2. Keep context deliberately minimal
3. The pattern must be recognizable from few cues

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a namespace and class; do not place
   statements outside class bodies
2. Use `using` directives for namespace imports
3. All code blocks must have matching braces
4. Include only using directives that are actually used
5. The code must compile and execute as valid C#

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-low-context", "language":
"c_sharp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion require C#-specific idiom knowledge?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
9. Is the combined prefix + suffix 10-20 lines or fewer?
"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert C# benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C# Pattern Matching
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can implement
a custom pattern transformation following established examples in
the prefix, rather than retrieving a memorized standard algorithm.

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
  - language: "c_sharp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Pattern Matching task

Requirements:

1. Realistic pattern-following scenarios.
   Use custom transformations where the prefix establishes a
   non-standard pattern that the model must follow. Representative
   domains include:
   - Config file parsers with coupled state: INI parsers with
     backslash line continuation and duplicate-key accumulation,
     .env parsers with profile sections and export stripping,
     SSH config with Host block context and lowercased keys,
     TOML with dotted table names and nested dictionaries
   - Custom encoders with non-standard alphabets: base64/base58/
     base32/hex with reversed alphabets, custom padding
     characters, count-first RLE with hex counts and max-run
     splitting
   - Edit distance variants with non-standard costs:
     substitution cost != 1, transposition cost = 0.5, custom
     operations
   - Template engines with nested conditional blocks requiring
     recursive parsing (not regex)
   - Route pattern matching with typed constraints (:int) and
     wildcard capture (*rest)
   - Bracket-aware splitting with nested depth tracking,
     string context, and escape sequences
   - Shell argument splitting with quote context tracking and
     escape handling
   - Markdown table parsing with backtick-aware pipe splitting
   - Custom serializers (single quotes, yes/no bools, nil nulls,
     sorted keys)
   - Identifier splitting with acronym and digit boundaries
   - Doc precision tasks requiring specific keyword classification
   The pattern should be established in the prefix with examples
   or specification, and the completion must follow that pattern.

2. Difficulty.
   The completion should require following the established pattern
   rather than retrieving a memorized standard algorithm. Use
   familiar function names (Base64Encode, UrlEncode, HtmlEscape,
   EditDistance) with non-standard behavior to trigger retrieval
   traps. The task should have at least two coupled state
   variables (e.g., continuation + comment stripping + quoting).

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
   C#, or overly simplified textbook implementations.

CODE STRUCTURE: All code must be within a namespace and class.
Do not place statements outside class bodies. Use `using`
directives for namespace imports.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

PATTERN_MATCHING_USER_PROMPT = """
Generate one C# Pattern Matching evaluation instance. Choose a
domain from the representative list in the system prompt (config
parsers, custom encoders with non-standard alphabets, edit
distance variants, template engines, route matching, bracket-aware
splitting, shell argument splitting, markdown parsing, custom
serializers, identifier splitting, or doc precision).

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
- language: "c_sharp"
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
4. The completion should require following a pattern established
   in the prefix, not retrieving a standard algorithm

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, pattern examples, or specifications
4. The prefix should demonstrate the pattern to follow

CODE STRUCTURE REQUIREMENTS:
1. All code must be within a namespace and class; do not place
   statements outside class bodies
2. Use `using` directives for namespace imports
3. All code blocks must have matching braces
4. Include only using directives that are actually used
5. The code must compile and execute as valid C#

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-pattern-matching", "language":
"c_sharp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion follow a pattern from the prefix?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

API_USAGE_SYSTEM_PROMPT = """
You are an expert C# benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C# API Usage instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly use a
common but error-prone .NET API under realistic context
constraints, including parameter ordering, resource management,
error handling, type conversions, API-specific conventions, and
edge cases.

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
  - language: "c_sharp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    API Usage task

Requirements:

1. Realistic API usage.
   Use APIs from the .NET standard library and common development
   contexts, reflecting telemetry-observed completion scenarios.
   Representative domains include:
   - LINQ operators: Aggregate with seed/func/resultSelector,
     GroupBy with element and result selectors, Zip truncation
     behavior, SelectMany with index, ToDictionary edge cases
   - Span<T> and Memory<T>: stackalloc with range operators,
     ReadOnlySpan slicing, ref struct constraints, Span.Reverse
   - Reflection: Expression trees (Expression.Lambda, Compile),
     Activator.CreateInstance, MethodInfo.Invoke, custom
     attributes
   - Concurrent collections: ConcurrentDictionary.GetOrAdd
     (multiple factory invocations), ConcurrentQueue, Channels
     (BoundedChannelFullMode, WriteAsync blocking)
   - Collection semantics: SortedSet.GetViewBetween (live view),
     PriorityQueue (min-heap, instability), Dictionary.TryAdd,
     OrderedDictionary insertion-order indexing, StringDictionary
     auto-lowercasing
   - Text and encoding: StringBuilder.AppendJoin, Encoding.UTF8
     GetBytes vs GetPreamble (BOM), Regex auto-cache,
     NumberFormatInfo custom formatting
   - JSON processing: JsonDocument (IDisposable, ArrayPool),
     JsonNode mutable DOM (AsArray, GetValue<T>), System.Text.Json
     serializer options
   - System.IO: StringReader/StringWriter, MemoryStream with
     BinaryWriter/BinaryReader, Path decomposition
   - Modern C# APIs: Index/Range operators (^4..^1), DynamicObject
     (TryGetMember/TrySetMember), ArrayPool<T>.Shared (Rent/Return),
     Version comparison (-1 for undefined components)
   - Async patterns: Task.WhenAll (order preservation, exception
     unwrapping), async/await with ConfigureAwait
   - Data APIs: DataTable expression columns, NameValueCollection
     multi-value behavior, BitConverter endianness, Uri properties
   - Type support: Array.BinarySearch (bitwise complement on miss),
     Array.Resize (new allocation, not in-place),
     ConstrainedCopy atomicity
   The API call should be embedded in a plausible function, class,
   or workflow, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (type compatibility, API
   behavioral semantics, error-path behavior, parameter ordering,
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
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than API reasoning, invalid C#, or
   overly simplified textbook implementations.

CODE STRUCTURE: All code must be within a namespace and class.
Do not place statements outside class bodies. Use `using`
directives for namespace imports.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

API_USAGE_USER_PROMPT = """
Generate one C# API Usage evaluation instance. Choose a domain
from the representative list in the system prompt (LINQ operators,
Span/Memory, Reflection, concurrent collections, collection
semantics, text/encoding, JSON processing, System.IO, modern C#
APIs, async patterns, data APIs, or type support).

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
- language: "c_sharp"
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
1. All code must be within a namespace and class; do not place
   statements outside class bodies
2. Use `using` directives for namespace imports
3. All code blocks must have matching braces
4. Include only using directives that are actually used
5. The code must compile and execute as valid C#

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-api-usage", "language":
"c_sharp", "prefix": "...", "suffix": "...",
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
