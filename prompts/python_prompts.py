API_USAGE_SYSTEM_PROMPT = """
You are an expert Python benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Python API Usage instance
that reflects telemetry-observed developer completion scenarios.
The instance should test whether a model can correctly use a
standard-library API under realistic context constraints, including
parameter ordering, return-value semantics, edge-case handling,
protocol compliance, and API-specific conventions.

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
  - language: "python"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    API Usage task

Requirements:

1. Realistic API usage.
   Use APIs from the Python standard library, reflecting
   telemetry-observed completion scenarios. Representative
   domains include:
   - inspect module: signature binding, annotation introspection,
     getmembers with predicates, parameter metadata
   - weakref: finalize callbacks, one-shot semantics, preventing
     premature garbage collection of ref targets
   - csv: DictWriter extrasaction modes, dialect registration,
     QUOTE_NONE with escape chars, lineterminator stripping
   - struct: pack/unpack with network byte order and mixed format
     codes, signed vs unsigned types, buffer size calculations
   - collections: ChainMap mutation semantics, OrderedDict move_to_end,
     namedtuple _replace, defaultdict with depth-limited nesting
   - functools: lru_cache typed parameter, total_ordering from
     __eq__ plus one comparison, reduce with initializer
   - itertools: chain.from_iterable lazy consumption, groupby
     requiring pre-sorted data, islice on generators
   - contextlib: suppress continuation semantics, ExitStack LIFO
     callback ordering, redirect_stdout
   - dataclasses: field default_factory for mutable defaults,
     metadata access, asdict with dict_factory, replace on frozen
   - enum: Flag with auto() and bitwise ops, custom
     _generate_next_value_ overrides
   - typing: get_type_hints with localns for forward references,
     runtime_checkable Protocol
   - copy: deepcopy with custom __deepcopy__ and memo dict,
     __copy__ for uncopyable attributes
   - abc: ABCMeta with __subclasshook__ for structural typing
   - statistics: quantiles exclusive vs inclusive methods
   - fractions: limit_denominator continued-fraction approximation,
     string constructor for exact decimal representation
   - logging: custom Filter subclass, LogRecord mutation
   - unittest.mock: patch with side_effect as iterable
   - operator: attrgetter with dotted nested paths
   - textwrap: indent with predicate callable
   - heapq: nlargest with key function and tie-breaking
   - bisect: bisect_left with key parameter semantics
   - hmac: compare_digest timing-safe comparison
   - secrets: token_bytes/token_hex/token_urlsafe/randbelow
   - sqlite3: create_aggregate class protocol (step/finalize)
   - xml.etree: namespace map for findall/find resolution
   - pathlib: Pure path classes for cross-platform drive parsing
   - tempfile: NamedTemporaryFile delete=False with manual cleanup
   The API call should be embedded in a plausible function or
   workflow, not presented as isolated trivia.

2. Difficulty.
   The completion should require resolving at least two contextual
   constraints from the prefix/suffix (type compatibility, protocol
   compliance, parameter ordering, return-value semantics, boundary
   conditions, or consistency with a helper function). The task
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
   unavailable external services or third-party packages,
   near-duplicated from public benchmarks, solvable by a single
   obvious keyword, dominated by boilerplate rather than API
   reasoning, invalid Python, or overly simplified textbook
   implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

API_USAGE_USER_PROMPT = """
Generate one Python API Usage evaluation instance. Choose a domain
from the representative list in the system prompt (inspect, weakref,
csv, struct, collections, functools, itertools, contextlib,
dataclasses, enum, typing, copy, abc, statistics, fractions,
logging, unittest.mock, operator, textwrap, heapq, bisect, hmac,
secrets, sqlite3, xml.etree, pathlib, or tempfile).

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
- language: "python"
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
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must use proper Python indentation
2. Do not place executable statements at module level except
   imports and constants
3. All assertions and test code belong in the "assertions" field
4. Include only imports that are actually used
5. The code must be fully executable Python
6. Standard library only -- no third-party packages

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-api-usage", "language":
"python", "prefix": "...", "suffix": "...",
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
You are an expert Python benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Python Code Purpose
Understanding instance that reflects telemetry-observed developer
completion scenarios. The instance should test whether a model can
infer business logic and domain intent from surrounding code and
produce a completion that correctly coordinates coupled side
effects, validation ordering, state transitions, and accumulator
updates.

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
  - language: "python"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code Purpose Understanding task

Requirements:

1. Realistic business-logic scenarios.
   Use iterators, generators, context managers, and stateful class
   workflows reflecting real-world domain logic. Representative
   domains include:
   - Multi-invariant business workflows: healthcare claims with
     copay/deductible ordering, payroll with pre-tax caps and
     garnishments, inventory with FIFO/FEFO depletion and batch
     tracking, warranty with deductible-before-coverage ordering
   - Financial state machines: payment waterfalls (late-fees vs
     interest vs principal ordering), billing period close with
     FIFO credit consumption, commission/reserve formulas
   - Resource lifecycle: idempotent operations, partial-capture
     state transitions, atomic over-allocation failure, validation-
     before-mutation ordering
   - Rate limiters: fixed-window, token-bucket, tiered per-endpoint,
     dual-quota with calendar resets, sliding time windows
   - Validation pipelines: fail-fast vs collect-all, dependent
     validation with skip semantics, normalize-then-validate,
     sanitization with change tracking
   - Approval workflows: quorum with impossibility detection,
     escalation chains, transactional rollback in reverse order
   - Cache implementations: LRU eviction, multi-level inclusive
     caches with L1/L2 promotion, CRDT last-writer-wins with
     tombstones
   - Statistical accumulators: EMA with variance using previous
     mean, exponential decay counters, nearest-rank percentile,
     fixed-width histograms
   The scenario must require the model to READ existing code to
   understand its PURPOSE, not just match syntax.

2. Difficulty.
   The completion should require coordinating at least two coupled
   side effects (e.g., idempotency guard + validation ordering +
   accumulator update + audit log + state transition). The task
   should not be solvable by implementing a standard algorithm;
   the specific ordering and interaction of effects must be
   inferred from the surrounding code context. Include at least
   one invariant that contradicts a common default assumption.

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
   Python, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
Generate one Python Code Purpose Understanding evaluation instance.
Choose a domain from the representative list in the system prompt
(multi-invariant business workflows, financial state machines,
resource lifecycle, rate limiters, validation pipelines, approval
workflows, cache implementations, or statistical accumulators).

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
- language: "python"
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
4. The completion should require coordinating at least two coupled
   side effects from prefix/suffix

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, class definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must use proper Python indentation
2. Do not place executable statements at module level except
   imports and constants
3. All assertions and test code belong in the "assertions" field
4. Include only imports that are actually used
5. The code must be fully executable Python
6. Standard library only -- no third-party packages

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code-purpose-understanding",
"language": "python", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the golden_completion coordinate multiple coupled effects?
6. Is the task non-trivial and not solvable by standard algorithm?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert Python benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Python Code2NL/NL2Code
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can produce
precise documentation for existing code (Code2NL) or implement
code from detailed natural-language specifications (NL2Code),
requiring exact technical vocabulary and coverage of edge cases.

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
  - language: "python"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Code2NL/NL2Code task

Requirements:

1. Realistic documentation and implementation scenarios.
   Use Python docstrings and standard-library APIs, reflecting
   telemetry-observed completion scenarios. Alternate between:

   Code-to-Natural-Language (Code2NL) tasks:
   - describe_* function pattern: generate precise docstrings for
     stdlib API usage (csv.DictWriter, urllib.parse, bisect, heapq,
     datetime.strptime, hashlib streaming, json object_pairs_hook,
     Decimal quantize, dataclasses.replace, pathlib PurePosixPath)
   - Docstrings must document: exact parameter semantics, return
     types, mutation vs immutability, exception conditions, side
     effects, performance characteristics, and edge-case behavior
   - Hidden assertions check for specific required keywords, not
     exact string matches

   Natural-Language-to-Code (NL2Code) tasks:
   - Implement algorithms from precise specifications: run-length
     encoding, interval merging with index tracking, recursive dict
     merge, proximity grouping, decorator factories with cache
     expiry, CSV parsing with quote handling
   - Specifications include subtle constraints: deduplication
     before finding second-largest, touching intervals as
     overlapping, empty-dict preservation in flattening, adjacent-
     element comparison in grouping

   Mixed (bidirectional) tasks:
   - Complete both docstring (Returns section) and implementation
   - Docstring must be consistent with the implementation
   - Examples: MinStack with O(1) constraint, DFS with adjacency
     list, Caesar cipher preserving case, Kahn's topological sort

2. Difficulty.
   For Code2NL: the docstring must include at least two specific
   technical details that a generic description would omit (e.g.,
   exact exception type, mutation behavior, time complexity, side
   effects on shared state). For NL2Code: the specification must
   include at least one subtle constraint that contradicts a
   standard implementation (e.g., deduplication requirement,
   touching-interval semantics, empty-container preservation).

3. Completion structure.
   The golden_completion must contain only the code at the cursor.
   The suffix must not duplicate the golden_completion. The prefix
   and suffix together must make the completion inferable but not
   reveal the answer. The combined prefix + golden_completion +
   suffix + assertions must execute successfully.

4. Hidden assertions.
   Assertions must be stored only in the "assertions" field; do
   not place hidden tests in the prefix or suffix. For Code2NL
   tasks, use substring checks for required keywords (e.g.,
   assert "keyword" in docstring.lower()). For NL2Code tasks,
   validate functional behavior and edge cases. Assertions must
   not hard-code or leak the golden completion.

5. Rejection criteria. Do not generate instances that are:
   ambiguous (multiple equally valid completions), dependent on
   unavailable external services, near-duplicated from public
   benchmarks, solvable by a single obvious keyword, dominated
   by boilerplate rather than documentation/implementation
   precision, invalid Python, or overly simplified textbook
   implementations (factorial, fibonacci, palindrome).

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

NL2CODE_CODE2NL_USER_PROMPT = """
Generate one Python Code2NL/NL2Code evaluation instance. Choose
a task type: Code2NL (docstring generation with keyword assertions),
NL2Code (implementation from specification), or mixed (both
docstring and implementation).

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
- language: "python"
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
7. For Code2NL tasks: use keyword substring checks, not exact
   string matches

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require precise technical vocabulary
   (Code2NL) or subtle constraint handling (NL2Code)

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, type definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must use proper Python indentation
2. Do not place executable statements at module level except
   imports and constants
3. All assertions and test code belong in the "assertions" field
4. Include only imports that are actually used
5. The code must be fully executable Python
6. Standard library only -- no third-party packages

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language":
"python", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the completion require precise technical detail?
6. Is the task non-trivial and not a textbook example?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert Python benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Python Low Context
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can complete
code correctly from minimal surrounding context, requiring
recognition of Python-specific idioms, protocols, and patterns
with very few contextual cues.

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
  - language: "python"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Low Context task

Requirements:

1. Realistic low-context scenarios.
   Use Python decorators, context managers, descriptors, and
   compact idioms, reflecting telemetry-observed completion
   scenarios. Representative domains include:
   - Custom base-N encoders: base32/36/45/52/58/62/64/85/91/94
     with non-standard (reversed) default alphabets, standard-
     alphabet overrides, and custom padding characters
   - Context managers: __enter__/__exit__ with selective exception
     suppression, generator-based @contextmanager cleanup
   - Descriptors: __get__/__set__/__set_name__ with per-instance
     storage, validation, and access counting
   - Metaclass protocols: __init_subclass__ for attribute
     enforcement, custom __contains__ for Enum value membership
   - Dataclass features: __post_init__ cross-field validation,
     computed properties from frozen fields
   - Generator protocols: try/finally cleanup on .close(), yield
     from delegation, __length_hint__ for remaining count
   - Compact idioms: inclusive range (unlike built-in range),
     depth-limited auto-vivification, positional-only/keyword-only
     parameter syntax, lambda closure capture with default args
   - Bitwise operations: flag grant/revoke/toggle/has with combined
     permission checking
   - Custom comparison: modular arithmetic ordering, shallow dict
     equality (keys only), anti-stable sort
   - String/sequence operations: interleave with remainder,
     jagged transpose with fill, string method chaining order
   The prefix and suffix combined should be only 10-20 lines for
   true low-context scenarios.

2. Difficulty.
   The completion should require resolving at least one non-obvious
   constraint that contradicts a common default assumption (e.g.,
   reversed alphabet vs standard, inclusive vs exclusive range,
   depth limit vs infinite nesting, custom rounding vs banker's
   rounding). The task should not be solvable by pattern matching
   alone; the model must read the visible context carefully.

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
   by boilerplate rather than idiom recognition, invalid Python,
   or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

LOW_CONTEXT_USER_PROMPT = """
Generate one Python Low Context evaluation instance. Choose a
domain from the representative list in the system prompt (custom
base-N encoders, context managers, descriptors, metaclass
protocols, dataclass features, generator protocols, compact
idioms, bitwise operations, custom comparison, or string/sequence
operations).

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
- language: "python"
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
1. The prefix and suffix combined should be ONLY 10-20 lines
   total for true low-context scenarios
2. Keep the context deliberately minimal while ensuring the
   pattern is still identifiable
3. The pattern should be non-trivial but recognizable to Python
   developers

COMPLETION STRUCTURE REQUIREMENTS:
1. The golden_completion must contain ONLY the code at the cursor
2. The suffix must NOT duplicate the golden_completion
3. The prefix and suffix must make the completion inferable but
   not reveal the answer
4. The completion should require resolving at least one constraint
   that contradicts a common default assumption

PREFIX LENGTH REQUIREMENTS:
1. Keep combined prefix + suffix to 10-20 lines total
2. Provide just enough context for the pattern to be identifiable
3. Every line should carry signal -- no filler

CODE STRUCTURE REQUIREMENTS:
1. All code must use proper Python indentation
2. Do not place executable statements at module level except
   imports and constants
3. All assertions and test code belong in the "assertions" field
4. Include only imports that are actually used
5. The code must be fully executable Python
6. Standard library only -- no third-party packages

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-low-context", "language":
"python", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Is prefix + suffix combined 10-20 lines total?
6. Does the completion contradict a common default assumption?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert Python benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Python Pattern Matching
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can implement
a custom transformation or parser that follows a pattern
established in the prefix, rather than retrieving a standard
algorithm from training data.

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
  - language: "python"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Pattern Matching task

Requirements:

1. Realistic pattern-following scenarios.
   Use config parsers, template dispatch, custom encoders, and
   stateful parsers, reflecting telemetry-observed completion
   scenarios. Representative domains include:
   - Custom encoding with familiar names: base32/36/45/52/58/62/
     64/85/94 encoders with reversed default alphabets, standard-
     alphabet overrides, and leading-zero byte conventions; the
     function name triggers standard retrieval but the visible
     suffix contradicts it
   - Config parsers: INI-style with section inheritance
     ([section:parent] syntax), flat key-value with custom
     delimiters, sectioned parsers with override semantics
   - Template and string dispatch: custom variable interpolation
     (${var} with \\$ escape), single-quote JSON serialization,
     custom number formatting using prefix helpers, conditional
     template blocks (${if var}...${end})
   - Stateful parsers: bracket matching with string-literal
     awareness, expression evaluation with operator precedence
     (two-pass), recursive bracket-tree serialization, hex-length
     chunk parsing
   - Graph and sequence algorithms: deterministic topological sort
     with tie-breaking, spiral matrix fill, LSB-first base
     conversion, KMP multi-pattern search
   - Data structure extensions: ring buffer with wrap-around,
     weighted-score cache eviction, ordered set with re-add-to-end,
     immutable stack-based RPN evaluation
   - Type-safe composition: inspect-based annotation checking for
     function pipeline composition
   - Deep equality extensions: float epsilon comparison with type
     strictness, set comparison without order
   The prefix must establish a clear pattern (at least 2-3
   examples) that the completion must follow.

2. Difficulty.
   The completion should require following the specific pattern
   established in the prefix, not retrieving a standard algorithm.
   Include at least one visible assertion or suffix check that
   explicitly contradicts the standard implementation (e.g.,
   assert encode(x) != STANDARD_RESULT). The task should not be
   solvable by importing a stdlib function.

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
   by boilerplate rather than pattern-following reasoning, invalid
   Python, or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

PATTERN_MATCHING_USER_PROMPT = """
Generate one Python Pattern Matching evaluation instance. Choose
a domain from the representative list in the system prompt (custom
encoding, config parsers, template dispatch, stateful parsers,
graph/sequence algorithms, data structure extensions, type-safe
composition, or deep equality extensions).

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
- language: "python"
- prefix: code before the completion point (MUST establish or
  begin a clear pattern with 2-3 examples)
- suffix: code after the completion point; must be DIFFERENT from
  the golden_completion; may contain execution code but NOT
  hidden assertions
- golden_completion: the minimal correct code at the cursor that
  follows the established pattern
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
4. The completion must FOLLOW the pattern established in the
   prefix, not retrieve a standard algorithm

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context establishing the pattern
3. Include 2-3 examples of the pattern before the completion point
4. The prefix should demonstrate the convention the completion
   must follow

CODE STRUCTURE REQUIREMENTS:
1. All code must use proper Python indentation
2. Do not place executable statements at module level except
   imports and constants
3. All assertions and test code belong in the "assertions" field
4. Include only imports that are actually used
5. The code must be fully executable Python
6. Standard library only -- no third-party packages

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-pattern-matching", "language":
"python", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the prefix establish a clear pattern (2-3 examples)?
6. Does the completion follow the pattern, not a standard algo?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""

SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert Python benchmark designer creating realistic
code-completion evaluation instances for large language models.

Your task is to generate one high-quality Python Syntax Completion
instance that reflects telemetry-observed developer completion
scenarios. The instance should test whether a model can produce
syntactically correct code involving complex nested structures,
advanced language features, and precise indentation alignment.

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
  - language: "python"
  - prefix: code before the completion point
  - suffix: code after the completion point (may be empty)
  - golden_completion: the minimal correct code at the cursor
  - assertions: hidden executable test code used only for
    evaluation; must not duplicate or leak the golden completion
  - LLM_justification: why this is a realistic and challenging
    Syntax Completion task

Requirements:

1. Realistic syntax scenarios.
   Use match/case, metaclasses, async/await, and complex nesting,
   reflecting telemetry-observed completion scenarios.
   Representative domains include:
   - Structural pattern matching (match/case): class patterns with
     positional destructuring, nested mapping/sequence patterns,
     star captures (*rest), OR patterns (A | B) with shared
     capture variables, guard clauses, **extra mapping capture
   - Metaclass and class protocols: __init_subclass__ with keyword
     arguments for plugin registration, __class_getitem__ for
     subscription syntax (MyClass[X, Y]), __set_name__/__get__/
     __set__ descriptor protocol, @runtime_checkable Protocol
   - Async/await patterns: async context managers (async with),
     async for with async generators, asyncio.gather with
     return_exceptions, asyncio.wait_for with timeout handling,
     semaphore-based concurrency pools
   - Generator protocols: yield from for recursive delegation
     with return-value capture, send() for coroutine-style
     bidirectional communication, throw() for exception injection,
     generator expressions with nested helper functions
   - Complex nesting: try/except/else/finally alignment with
     nested context managers, for/else semantics with break
     control flow, raise ... from ... exception chaining across
     nested scopes, 7+ indentation levels
   - Advanced f-strings: nested dynamic width ({val:{align}{w}}),
     datetime format specs ({dt:%Y-%m-%d}), !r and !s conversion
     flags, adjacent f-string concatenation, conditional tag
     construction
   - Lambda and functional: nested lambdas in reduce, mutable
     default argument memoization, dict comprehension with nested
     sorted() and lambda keys, map/filter/reduce nesting
   - Function signatures: positional-only (/) and keyword-only (*)
     separators, *args with trailing keyword-only params, @overload
     declarations with implementation function, complex Union type
     hints
   - Decorator patterns: @classmethod + custom decorator stacking
     order, descriptor interaction with decorators

2. Difficulty.
   The completion should require precise indentation alignment or
   correct ordering of syntactic elements (e.g., except before
   finally, case arm specificity ordering, decorator stacking
   order). The task should test SYNTAX mastery, not algorithm
   knowledge. Include at least one syntactic trap where the obvious
   completion would produce a runtime or syntax error.

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
   by boilerplate rather than syntax reasoning, invalid Python,
   or overly simplified textbook implementations.

Output a single-line JSON object with all newlines and quotes
escaped for JSONL parsing.
"""

SYNTAX_COMPLETION_USER_PROMPT = """
Generate one Python Syntax Completion evaluation instance. Choose
a domain from the representative list in the system prompt
(structural pattern matching, metaclass protocols, async/await,
generator protocols, complex nesting, advanced f-strings, lambda
and functional, function signatures, or decorator patterns).

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
- language: "python"
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
4. The completion should require precise syntactic alignment or
   correct element ordering

PREFIX LENGTH REQUIREMENTS:
1. The prefix MUST be at least 15-25 lines of code
2. Provide sufficient context and setup code
3. Include helper functions, class definitions, or related code
4. The prefix should demonstrate an incomplete implementation

CODE STRUCTURE REQUIREMENTS:
1. All code must use proper Python indentation
2. Do not place executable statements at module level except
   imports and constants
3. All assertions and test code belong in the "assertions" field
4. Include only imports that are actually used
5. The code must be fully executable Python
6. Standard library only -- no third-party packages

INDENTATION REQUIREMENTS:
1. All code sections must maintain consistent indentation
2. The golden_completion must match the prefix indentation level
3. The suffix must maintain the same indentation context

Format your response as a single-line JSON object:
{"id": "1", "testsource": "devbench-syntax-completion", "language":
"python", "prefix": "...", "suffix": "...",
"golden_completion": "...", "assertions": "...",
"LLM_justification": "..."}

VALIDATION CHECKLIST:
1. Is your response a single, valid JSON object?
2. Are all special characters properly escaped?
3. Are assertions in the "assertions" field (NOT in the suffix)?
4. Does prefix + golden_completion + suffix + assertions execute?
5. Does the completion test syntax mastery, not algorithm knowledge?
6. Is there a syntactic trap where the obvious answer would fail?
7. Are all required JSON fields present, with non-empty prefix,
   golden_completion, assertions, and LLM_justification? The
   suffix may be empty for prefix-only instances.
8. Does at least one assertion test an edge case?
"""
