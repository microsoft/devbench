SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert C++ benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C++ Syntax Completion
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can correctly
complete complex syntactical structures and nested scope patterns
in modern C++, including RAII lifetime control, template syntax,
fold expressions, constexpr branching, and smart-pointer
ownership transfer.

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
  - language: "cpp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Syntax Completion task

Requirements:

1. Realistic syntax scenarios.
   Use advanced C++ syntax structures that exercise scope-
   sensitive lifetime and type-level reasoning. Representative
   domains include:
   - Fold expressions: unary/binary left and right folds with
     parameter packs, comma-fold side effects, fold-based
     string joining with index counters
   - constexpr if: multi-branch type dispatch with is_integral_v,
     is_floating_point_v, is_same_v, recursive container branches
   - RAII lifetime control: unique_ptr reset/release/swap inside
     nested blocks, destructor ordering from declaration order,
     scope-guard dismiss patterns, optional emplace/reset
     destruction timing
   - Structured bindings: if-init with map::insert pair
     destructuring, range-for over map with const auto& [k, v],
     tuple unpacking across function boundaries
   - Variadic templates: recursive parameter-pack expansion,
     sizeof...(Ts), base-case specialization, std::apply with
     tuple expansion
   - Lambda syntax: init-capture with std::move, mutable keyword,
     trailing return types, generic lambdas with auto parameters
   - Smart-pointer ownership: unique_ptr move into inner scope,
     shared_ptr copy/reset reference counting, custom-deleter
     reset construction-before-deletion ordering
   - std::visit with overloaded pattern: aggregate brace nesting
     with multiple typed lambdas, variant dispatch
   - Concepts and SFINAE: requires clauses with compound
     requirements, enable_if return-type placement, mutually
     exclusive overloads via type traits
   - Move semantics: move constructor/assignment with source
     invalidation, self-assignment guards, std::exchange idiom
   - Lock-guard nesting: scoped_lock declaration order
     controlling unlock sequence, nested mutex scopes
   - Monadic optional chaining: and_then / transform composition,
     nested optional-returning function pipelines
   The syntax pattern should be embedded in a plausible function
   or class, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two syntactic
   constraints: correct brace/scope nesting, template angle-
   bracket balancing, RAII destruction ordering, parameter-pack
   expansion placement, or lifetime-sensitive statement sequencing.
   The task should not be solvable by copying a nearby line.
   Hidden assertions should verify observable side effects of the
   syntax (e.g., destructor log order, return values) rather than
   just compilation success.

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
   by boilerplate rather than syntax reasoning, invalid C++, or
   overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

SYNTAX_COMPLETION_USER_PROMPT = """
Generate one C++ Syntax Completion evaluation instance. Choose a
domain from the representative list in the system prompt (fold
expressions, constexpr if, RAII lifetime control, structured
bindings, variadic templates, lambda syntax, smart-pointer
ownership, std::visit with overloaded, concepts/SFINAE, move
semantics, lock-guard nesting, or monadic optional chaining).

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
- language: "cpp"
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
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within proper C++ scope boundaries
2. Do not place executable statements or assertions at global
   scope; includes, type aliases, constants, class/struct
   definitions, and helper function definitions are allowed
3. All code blocks must have matching braces
4. Include only headers that are actually used
5. The code must be fully executable C++

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-syntax-completion", "language":
"cpp", "prefix": "...", "suffix": "...",
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
You are an expert C++ benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C++ Code2NL/NL2Code
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can produce
precise Doxygen-style documentation for C++ standard-library
code, or implement code from detailed documentation, requiring
exact technical keywords about API semantics, complexity,
mutation, iterator validity, and edge-case behavior.

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
  - language: "cpp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code2NL/NL2Code task

Requirements:

1. Realistic documentation and implementation scenarios.
   Use C++ standard library APIs and idioms where precise
   documentation wording separates correct from generic
   descriptions. Representative domains include:
   - Algorithm documentation: copy_if with back_inserter and
     predicate call count, next_permutation false/reset behavior,
     equal_range sorted precondition and half-open interval,
     sample without-replacement and URBG seed determinism,
     stable_sort vs sort stability guarantees, rotate_copy
     non-mutating output order, transform_exclusive_scan
     transform-before-scan and exclusive semantics
   - Container semantics: map try_emplace no-overwrite pair
     return, unordered_map reserve/rehash and load factor,
     set::merge node-transfer without copying, list::splice
     O(1) node-relink without allocation, deque segmented
     non-contiguous storage, priority_queue top-then-pop void
     return and max-heap default
   - Smart-pointer precision: unique_ptr release non-deleting
     raw-pointer handoff, shared_ptr aliasing constructor
     stored-vs-managed distinction, weak_ptr::lock nullptr on
     expiry, shared_ptr custom deleter type-erasure and
     reference-counting destruction, unique_ptr deleter-as-type
   - C++17 vocabulary types: optional value_or eager evaluation,
     any_cast pointer-vs-value overloads with null-on-mismatch,
     variant std::visit active-alternative dispatch, string_view
     non-owning dangling lifetime and no null-terminator
   - Threading documentation: scoped_lock multi-mutex deadlock
     avoidance, unique_lock deferred state machine, promise/
     future shared-state and get invalidation, condition_variable
     spurious-wakeup predicate requirement
   - Numeric and text: accumulate left-fold order and init-type,
     partition not-stable and partition-point return, rotate
     left-rotation and iterator-to-original-first return,
     std::exchange old-value return and single-expression idiom,
     std::forward conditional value-category preservation,
     std::clamp UB when lo > hi
   - NL2Code implementations: trie insert with node creation and
     is_end marking, quickselect partition-based kth-element,
     balanced parentheses with stack, LRU cache with list::splice,
     RPN evaluator with operand ordering, run-length encoding
   The documentation or code should be embedded in a plausible
   function or class, not presented as isolated trivia.

2. Difficulty.
   For Code2NL tasks: the documentation must require at least two
   precise technical keywords that generic summaries omit (e.g.,
   "node transfer" + "source mutation" for set::merge; "type-
   erased" + "reference counting" for shared_ptr custom deleters).
   For NL2Code tasks: the implementation must handle at least one
   edge case not obvious from the function signature (e.g., empty
   string, all-equal elements, self-referential input).

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. For Code2NL
   tasks, assertions should check substring presence of required
   technical keywords (e.g., assert(doc.find("node") !=
   std::string::npos)). For NL2Code tasks, assertions should
   verify functional behavior and edge cases. Assertions must not
   hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than documentation precision or
   implementation reasoning, invalid C++, or overly simplified
   textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

NL2CODE_CODE2NL_USER_PROMPT = """
Generate one C++ Code2NL/NL2Code evaluation instance. Choose a
domain from the representative list in the system prompt
(algorithm documentation, container semantics, smart-pointer
precision, C++17 vocabulary types, threading documentation,
numeric and text APIs, or NL2Code implementations).

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
- language: "cpp"
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
6. For Code2NL tasks, use substring checks for required keywords:
   assert(doc.find("keyword") != std::string::npos)
7. For NL2Code tasks, verify functional behavior and edge cases
8. Include at least one edge case assertion

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
1. All code must be within proper C++ scope boundaries
2. Do not place executable statements or assertions at global
   scope; includes, type aliases, constants, class/struct
   definitions, and helper function definitions are allowed
3. All code blocks must have matching braces
4. Include only headers that are actually used
5. The code must be fully executable C++

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language":
"cpp", "prefix": "...", "suffix": "...",
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
You are an expert C++ benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C++ Code Purpose
Understanding instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model
can correctly implement multi-invariant business logic by reading
surrounding struct definitions, helper constants, and suffix
assertions to infer the precise ordering and interaction of
coupled side effects.

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
  - language: "cpp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code Purpose Understanding task

Requirements:

1. Realistic multi-invariant business workflows.
   Use struct-based workflows where a single function must
   coordinate multiple coupled side effects in strict order.
   Representative domains include:
   - Healthcare claim adjudication: idempotency, auth denial,
     primary-payer offsets, preventive bypass, copay/deductible/
     coinsurance waterfall with OOP cap and accumulator updates
   - Inventory allocation: FEFO expiry sorting, quarantine
     filtering, shelf-life validation, atomic failure on
     insufficient stock, audit logging
   - Loan/mortgage payment processing: charged-off recovery
     routing, late fee injection with pending+applied flags,
     fees-interest-escrow-principal waterfall, paid-off
     transition, ledger logging
   - Payroll computation: retirement contribution cap by YTD
     accumulator, marginal tax brackets, garnishment with
     minimum-net floor, health deduction ordering
   - Insurance premium/adjudication: age validation, risk
     surcharges, multiplicative discount tiers, minimum premium
     floor, deductible/coinsurance/OOP-max clamping
   - Order fulfillment and e-commerce: cancellation checks,
     backorder queuing, partial ship, coupon exclusion by
     category, tax on pre-discount prices, auth-failure rollback
   - Subscription/SaaS billing: trial countdown, proration on
     activation, auto-renewal cycling, grace-to-dunning
     transition, plan conversion with quota reset
   - Financial operations: wire transfer with cross-currency
     fees, daily limits, margin checks with rollback, royalty
     distribution with accrual thresholds
   - Service industry: restaurant ordering with modifier pricing,
     hotel reservation with seasonal/early-bird/cancellation
     tiers, clinic scheduling with provider blocks and waitlist
   - Miscellaneous: tax return with progressive brackets and
     credits, construction estimates with waste/efficiency
     factors, rental car return with tiered late surcharges,
     donation processing with employer match caps
   The workflow should be embedded in a plausible struct with
   state fields, not presented as isolated arithmetic.

2. Difficulty.
   The completion should require coordinating at least five
   coupled invariants (idempotency, validation ordering,
   accumulator updates, conditional branching, audit/logging)
   where getting one wrong causes cascading assertion failures.
   The task should not be solvable by copying a nearby line or
   implementing a single formula. Include at least one ordering
   trap where checking conditions in the wrong sequence produces
   a subtly different result.

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
   one edge case not explicitly described in comments (e.g.,
   idempotent re-call, boundary accumulator value, zero-amount
   input). Assertions must not hard-code or leak the golden
   completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than business-logic reasoning, invalid
   C++, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
Generate one C++ Code Purpose Understanding evaluation instance.
Choose a domain from the representative list in the system prompt
(healthcare claims, inventory allocation, loan processing,
payroll, insurance, order fulfillment, subscription billing,
financial operations, service industry, or miscellaneous business
workflows).

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
- language: "cpp"
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
6. Include at least one edge case assertion (e.g., idempotent
   re-call, zero-amount input, boundary accumulator)

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require coordinating at least five
   coupled invariants from the surrounding struct definitions

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context: struct definitions, helper
   constants, state fields, and the function signature
3. Include comments describing the business rules
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within proper C++ scope boundaries
2. Do not place executable statements or assertions at global
   scope; includes, type aliases, constants, class/struct
   definitions, and helper function definitions are allowed
3. All code blocks must have matching braces
4. Include only headers that are actually used
5. The code must be fully executable C++

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code-purpose-understanding",
"language": "cpp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion coordinate multiple coupled
   invariants from the struct definitions?
6. Is the task non-trivial and not solvable by copying a line?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert C++ benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C++ Low Context
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can correctly
complete C++ code from minimal surrounding context (10-20 lines
total for prefix + suffix), requiring recognition of C++ idioms,
RAII patterns, move semantics, and standard-library conventions
from very few cues.

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
  - language: "cpp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Low Context task

Requirements:

1. Realistic low-context scenarios.
   Use compact C++ idioms and patterns where the model must infer
   correct behavior from minimal visible code. Representative
   domains include:
   - Custom encoding with reversed alphabets: base64, base58,
     hex, base32, base85, octal, base36, base62, ascii85,
     base45, base52, base26, base57, base16, decimal encoders
     with familiar function names but non-standard (reversed)
     default alphabets
   - RAII patterns: scope-guard with deleted copy constructor,
     unique_ptr custom deleters, resource-acquisition idioms
   - Move semantics: move-capture lambdas transferring unique_ptr
     ownership, std::exchange in move constructors
   - Documentation precision keywords: single-sentence API
     descriptions requiring exact technical terms (e.g.,
     "allocates without constructing" for vector::reserve,
     "type-erased" for shared_ptr custom deleters, "spurious
     wakeup" for condition_variable, "non-owning" and "dangling"
     for string_view)
   - Structured bindings: map::insert pair destructuring with
     insertion-count tracking
   - Fold expressions: variadic product with empty-pack identity
     handling via if-constexpr guard
   - Optional transform: value doubling with fallback, monadic
     chaining patterns
   - Container merge documentation: node-transfer semantics,
     source mutation, duplicate-key retention
   - Smart-pointer semantics: unique_ptr deleter-as-type vs
     shared_ptr type-erasure, promise/future exception
     propagation, std::bind placeholder reordering
   The pattern should be recognizable from 10-20 lines of total
   visible context.

2. Difficulty.
   The completion should require resolving at least one
   preconception trap (familiar name with non-standard behavior)
   or one precise technical keyword that generic descriptions
   omit. The task should not be solvable by copying a nearby
   line. For encoding tasks, the default alphabet must differ
   from standard and the suffix must assert non-standard output.

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must compile and execute successfully.
   PREFIX + SUFFIX COMBINED MUST BE 10-20 LINES TOTAL.

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
   by boilerplate rather than idiom recognition, invalid C++, or
   overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

LOW_CONTEXT_USER_PROMPT = """
Generate one C++ Low Context evaluation instance. Choose a domain
from the representative list in the system prompt (custom encoding
with reversed alphabets, RAII patterns, move semantics,
documentation precision keywords, structured bindings, fold
expressions, optional transform, container merge documentation,
or smart-pointer semantics).

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
- language: "cpp"
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

CRITICAL: LOW CONTEXT SIZE REQUIREMENT:
1. The prefix and suffix COMBINED must be only 10-20 lines total
2. Keep the context deliberately minimal
3. The pattern must be identifiable from these few lines alone

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require resolving at least one
   preconception trap or precise technical constraint

CODE STRUCTURE REQUIREMENTS:
1. All code must be within proper C++ scope boundaries
2. Do not place executable statements or assertions at global
   scope; includes, type aliases, constants, class/struct
   definitions, and helper function definitions are allowed
3. All code blocks must have matching braces
4. Include only headers that are actually used
5. The code must be fully executable C++

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-low-context", "language":
"cpp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Is the combined prefix + suffix only 10-20 lines total?
6. Does the completion exploit a preconception trap or require
   a precise technical keyword?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert C++ benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C++ Pattern Matching
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can correctly
implement a custom transformation or parser by following the
pattern established in the prefix, rather than retrieving a
memorized standard implementation triggered by a familiar
function name.

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
  - language: "cpp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Pattern Matching task

Requirements:

1. Realistic pattern-following scenarios.
   Use tasks where the prefix establishes a non-standard pattern
   that the model must follow, not retrieve from training data.
   Representative domains include:
   - Custom encoding with reversed alphabets: base64, base58,
     hex, base32, base85, base36 encoders where the default
     alphabet is reversed from standard, causing standard
     implementations to produce wrong output
   - Stateful config/INI/.env parsers: line-continuation with
     backslash, quote-aware comment stripping, section context
     tracking, duplicate-key append semantics, profile/host
     block scoping (manifest, .env, INI, route-table, systemd,
     SSH-config, Makefile, YAML-like, Dockerfile ENV, C
     preprocessor #define)
   - Bracket matching with string awareness: tracking in_string
     state with backslash escape handling, ignoring brackets
     inside quoted strings
   - Edit distance with custom costs: transposition cost != 1,
     fractional costs that standard Levenshtein ignores
   - Algorithm variants with non-standard behavior: RLE with
     count-before-character format, sort with reverse-alpha
     tie-breaking, binary search returning LAST occurrence,
     merge sort with abs-value and positive-first ties, FNV-1a
     with non-standard parameters and folding, deep flatten
     with depth limit, consecutive grouping (not global),
     zip-extend by repeating last element, circular sliding
     window max, topological sort with reverse-alpha tie-
     breaking, deep merge with first-wins (not last-wins)
   - Template expansion: recursive ${var} substitution with
     brace-depth tracking and $$ escaping
   - Expression tokenizer: multi-char operator ordering, string
     literal parsing with backslash escapes
   - Custom number formatting: European style (dot for thousands,
     comma for decimal) vs US style
   - Weighted random with custom LCG: deterministic selection
     using provided pseudo-random generator parameters
   The pattern should be embedded in a plausible function or
   parser, not presented as isolated trivia.

2. Difficulty.
   The completion should require following at least two non-
   standard conventions established in the prefix (reversed
   alphabet + padding character, continuation + comment rules,
   custom cost + transposition support). The task should not be
   solvable by retrieving a memorized standard implementation.
   Include an anti-standard assertion that explicitly checks the
   output differs from what the standard algorithm would produce.

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
   one edge case not explicitly described in comments (e.g., empty
   input, single-element input, escaped delimiter). Assertions
   must not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than pattern-following reasoning, invalid
   C++, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

PATTERN_MATCHING_USER_PROMPT = """
Generate one C++ Pattern Matching evaluation instance. Choose a
domain from the representative list in the system prompt (custom
encoding with reversed alphabets, stateful config parsers,
bracket matching, edit distance with custom costs, algorithm
variants with non-standard behavior, template expansion,
expression tokenizer, custom number formatting, or weighted
random with custom LCG).

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
- language: "cpp"
- prefix: code before the completion point (MUST establish the
  non-standard pattern the model must follow)
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
6. Include at least one anti-standard assertion that verifies
   the output differs from the standard algorithm
7. Include at least one edge case assertion

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require following at least two non-
   standard conventions established in the prefix

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context: constants, helper functions, and
   comments establishing the non-standard pattern
3. Include at least 2-3 examples of the pattern in the prefix
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must be within proper C++ scope boundaries
2. Do not place executable statements or assertions at global
   scope; includes, type aliases, constants, class/struct
   definitions, and helper function definitions are allowed
3. All code blocks must have matching braces
4. Include only headers that are actually used
5. The code must be fully executable C++

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-pattern-matching", "language":
"cpp", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions compile?
5. Does the golden_completion follow the non-standard pattern
   established in the prefix?
6. Is the task non-trivial and not solvable by retrieving a
   standard implementation?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

API_USAGE_SYSTEM_PROMPT = """
You are an expert C++ benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality C++ API Usage instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly use a
common but error-prone C++ API under realistic context
constraints, including
parameter ordering, resource management, error handling, type
conversions, API-specific conventions, and edge cases.

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
  - language: "cpp"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    API Usage task

Requirements:

1. Realistic API usage.
   Use APIs from the C++ standard library and common development
   contexts, reflecting telemetry-observed completion scenarios.
   Representative domains include:
   - Standard algorithms: sort with custom comparators, transform
     (unary/binary), partition, nth_element, clamp, rotate, search
     with searcher objects, copy_backward, adjacent_find
   - Smart pointers and memory management: unique_ptr ownership
     transfer, shared_ptr/make_shared semantics, weak_ptr::lock()
     promotion, enable_shared_from_this, allocator patterns
   - Threading and concurrency: async/future, condition_variable
     with predicates, shared_mutex reader-writer locks, scoped_lock
     for deadlock-free multi-mutex acquisition, semaphore patterns
   - Container semantics: map insert vs operator[], reserve vs
     resize, emplace return values, set extract and node handles
   - Move semantics and forwarding: std::move, std::forward for
     perfect forwarding, std::exchange in move constructors
   - Tuple utilities: std::tie with std::ignore, std::apply for
     tuple-to-argument expansion, std::tuple_cat
   - Numeric algorithms: accumulate vs reduce, iota, inner_product
     with custom binary operations
   - String and text processing: substr boundary handling, stoi
     with index output parameter, string_view lifetime semantics,
     regex_replace
   - Filesystem: create_directories with error_code overloads,
     path decomposition and lexical normalization
   - C++17 vocabulary types: variant with std::visit, optional
     emplace vs assignment, any_cast value-vs-pointer overloads
   - Low-level type support: from_chars/to_chars, std::bitset,
     std::launder with placement new, aligned_storage
   - Chrono timing: steady_clock vs system_clock, duration_cast
   - Callable abstractions: std::invoke with member pointers
   The API call should be embedded in a plausible function, class,
   or workflow, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (type compatibility,
   ownership/lifetime, error-path behavior, parameter ordering,
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
   by boilerplate rather than API reasoning, invalid C++, or
   overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

API_USAGE_USER_PROMPT = """
Generate one C++ API Usage evaluation instance. Choose a domain
from the representative list in the system prompt (standard
algorithms, smart pointers, threading, containers, move
semantics, tuples, numerics, strings, filesystem, C++17
vocabulary types, low-level type support, chrono, or callable
abstractions).

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
- language: "cpp"
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
1. All code must be within proper C++ scope boundaries
2. Do not place executable statements or assertions at global
   scope; includes, type aliases, constants, class/struct
   definitions, and helper function definitions are allowed
3. All code blocks must have matching braces
4. Include only headers that are actually used
5. The code must be fully executable C++

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-api-usage", "language":
"cpp", "prefix": "...", "suffix": "...",
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