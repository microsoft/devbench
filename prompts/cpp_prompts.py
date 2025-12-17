SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert C++ developer tasked with creating benchmark examples for testing syntax completion and language-specific structure capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to complete complex syntactical patterns and nested structures.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C++ that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical scenarios that test understanding of language-specific syntax. Choose ONE syntax pattern to test (rotate through them):
    Syntax Categories:
    a. Nested Control Structures
    - Multiple levels of if/else conditions
    - Nested loop structures (for/while/do-while combinations)
    - Try/catch with multiple catch blocks
    - RAII patterns with scope-based resource management
    - Range-based for loops with complex iterators

    b. Complex C++ Syntax Features
    - Class inheritance and virtual function overrides
    - Template metaprogramming patterns
    - Move semantics and perfect forwarding
    - Lambda expressions with captures
    - SFINAE and type traits

    c. Multi-line Syntax Patterns
    - Method chaining patterns
    - Builder pattern implementations
    - Fluent interface structures
    - Stream formatting operations
    - Function overloading resolution

    d. Error Handling Patterns
    - Try/catch combinations with exception hierarchies
    - RAII-based resource management
    - Error code propagation patterns
    - Exception safety guarantees
    - Smart pointer usage for resource management
    
2. Ensure patterns demonstrate proper nesting and indentation
3. Create ground truth completions that maintain syntactic correctness
4. Write assertions that meaningfully test structural integrity and syntax validity
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C++
    - All assertions must pass when code is run
    - Include necessary header files
    - Handle cleanup of resources using RAII principles
    - Use proper exception handling
    - Include minimal working examples
    - Mock external dependencies where needed
7. Write robust assertions that:
    - Verify actual behavior
    - Test parameter ordering
    - Check error conditions
    - Validate return values
    - Mock external resources

When generating examples:
1. Focus on complex syntactical structures and patterns
2. Test handling of nested code blocks
3. Ensure patterns include proper error handling syntax
4. Include edge cases in syntax formatting
5. Keep code focused on demonstrating language-specific features
"""

SYNTAX_COMPLETION_USER_PROMPT = """
You are helping create a benchmark for syntax completion capabilities. Your task is to generate a coding scenario that tests an LLM's ability to complete
complex syntactical structures and maintain proper formatting in C++ code. The scenario should include:

Generate a single JSONL entry testing syntax completion capabilities. Choose ONE syntax pattern to test (rotate through them):
    Syntax Categories:
    a. Nested Control Structures
    - Multiple levels of if/else conditions
    - Nested loop structures (for/while/do-while combinations)
    - Try/catch with multiple catch blocks
    - RAII patterns with scope-based resource management
    - Range-based for loops with complex iterators

    b. Complex C++ Syntax Features
    - Class inheritance and virtual function overrides
    - Template metaprogramming patterns
    - Move semantics and perfect forwarding
    - Lambda expressions with captures
    - SFINAE and type traits

    c. Multi-line Syntax Patterns
    - Method chaining patterns
    - Builder pattern implementations
    - Fluent interface structures
    - Stream formatting operations
    - Function overloading resolution

    d. Error Handling Patterns
    - Try/catch combinations with exception hierarchies
    - RAII-based resource management
    - Error code propagation patterns
    - Exception safety guarantees
    - Smart pointer usage for resource management

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines
   - Use \\t for tabs
   - Use \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. Do NOT include formatting or indentation outside the JSON structure
5. DO NOT use markdown code blocks (```) in your response
6. Test your JSON structure before completing your response

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-syntax-completion"
- language: "cpp"
- prefix: The code that comes before the completion (may or may not establish the syntax pattern)
- suffix: The code that follows the completion (may or may not establish the syntax pattern) - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: The syntactically appropriate completion that maintain consistency with prefix/suffix and will pass all assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL JSON FIELD REQUIREMENTS:
1. ALWAYS include ALL required JSON fields listed above, even if empty
2. The "assertions" field MUST be present with an empty string value: "assertions": ""
3. Do NOT omit any fields from your JSON object
4. Format example showing required empty assertions field:
   {"id": "42", ..., "assertions": ""}
5. INCORRECT: {"id": "42", ...} - missing assertions field

CRITICAL CHANGE - NEW SUFFIX REQUIREMENTS:
1. The suffix must contain both execution code AND assertion code
2. Include assert() statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same function/class as the code being tested
4. DO NOT create separate assertion functions or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Header Inclusion Requirements:
1. Do NOT include header files unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included header must serve a clear purpose
3. Do not include "just in case" headers that aren't used
4. All required header inclusions must appear in the prefix section
5. If a header is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include <cassert> header for assert() statements


PREFIX LENGTH REQUIREMENTS - CRITICAL:
1. The PREFIX section MUST be SUBSTANTIALLY LONGER than other sections
2. The prefix MUST be AT LEAST 50-60 lines of code - this is an absolute requirement
3. Provide extensive context and setup code in the prefix
4. Include helper functions, utility classes, and related code structures
5. Add detailed comments and explanations within the prefix
6. The prefix should demonstrate a comprehensive but incomplete implementation
7. Add relevant constants, configuration objects, and data structure initialization

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a function/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper indentation when exiting blocks
4. All code blocks must be properly closed

The pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C++ code
2. All assertions must pass when code is run
3. Include all necessary header files
4. Mock external dependencies
5. Clean up resources properly using RAII principles
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of functions or classes
2. ALL code must be contained within proper C++ scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within functions (such as main() or other functions)
5. ALWAYS ensure code is properly nested within appropriate class and function structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and functions are properly matched with braces {}
9. DO NOT leave any code statements outside of function bodies
10. Place all assertions within appropriate functions (main(), test(), etc.)

CRITICAL ASSERTION PLACEMENT:
1. All assert() statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same function as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use assert(condition) format for all assertions
7. Make sure <cassert> is included for assert() statements

Requirements:
1. The scenario should demonstrate complex syntax patterns
2. The completion section should focus on language-specific structures
3. The pattern should follow proper indentation and nesting rules
4. Ground truth should maintain consistent formatting
5. Assertions should verify structural integrity
6. Include comments indicating expected syntax and formatting

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-syntax-completion", "language": "cpp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you included all assertions DIRECTLY IN THE SUFFIX code?
9. Have you verified that assertions will pass when the code is executed?
10. Is the assertions field included with an empty string value ("assertions": "")?
11. Have you verified that ALL required fields are present in your JSON?
12. Have you verified your example is NOT one of the prohibited trivial examples?
13. Does your example meet ALL the complexity validation criteria?
14. Does your example demonstrate genuinely advanced C++ features?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert C++ developer tasked with creating benchmark examples for testing bidirectional translation between code and natural language capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to translate between code and documentation in both directions.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C++ that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical scenarios that test code-to-comment and comment-to-code translation from these domains (rotate through them):
    Business Logic:
    - Financial calculations (portfolio analysis, risk assessment)
    - Data transformations (ETL processes, data cleaning)
    - Business rules validation (compliance checks, policy enforcement)
    - Workflow orchestration (task scheduling, pipeline management)
    - Domain modeling (business entities, relationship handling)

    Technical Features:
    - API integrations (authentication, rate limiting)
    - Cache management (invalidation, refresh strategies)
    - Data structures (custom collections, specialized containers)
    - Configuration management (dynamic settings, feature flags)
    - Resource management (RAII, smart pointers, memory management)
2. Ensure patterns demonstrate clear alignment between documentation and implementation, with the following requirements (alternate between these):
    For Code-to-Natural Language (50% of test cases):
    - Generate comprehensive documentation for:
        * Method implementations
        * Class definitions
        * Namespace-level code
        * Complex algorithms
        * Error handling logic
    - Documentation should include:
        * Detailed Doxygen-style documentation comments
        * Implementation comments explaining complex logic
        * Usage examples
        * Parameter descriptions
        * Return value documentation
        * Error scenarios and handling
        * Performance characteristics
    
    For Natural Language-to-Code (50% of test cases):
    - Test implementation of:
        * Complex business rules
        * Technical requirements
        * Algorithm descriptions
        * Error handling specifications
        * Interface contracts
3. Create ground truth completions that maintain consistency between comments and code
4. Write assertions that meaningfully test documentation accuracy and code correctness:
    - For documentation tests:
        * Check presence of key domain terms
        * Verify coverage of important concepts
        * Validate documentation structure
        * Don't require exact string matches
    - For implementation tests:
        * Verify functional requirements
        * Test edge cases
        * Check error handling
        * Validate return values
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C++
    - All assertions must pass when code is run
    - Include necessary header inclusions
    - Handle cleanup of resources with RAII principles
    - Use proper error handling (exceptions, error codes)
    - Include minimal working examples
    - Mock external dependencies where needed
7. Write robust assertions that:
    - Verify actual behavior
    - Test parameter ordering
    - Check error conditions
    - Validate return values
    - Mock external resources

When generating examples:
1. Focus on bidirectional translation between code and natural language
2. Test accuracy of generated documentation
3. Ensure patterns include proper documentation conventions
4. Include edge cases in documentation clarity
5. Keep both code and comments focused on clear communication

Avoid These Common Patterns:
1. Trivial mathematical functions (factorial, fibonacci)
2. Simple data structure operations (stack, queue)
3. Basic string manipulations (palindrome, anagram)
4. Elementary algorithms (bubble sort, binary search)
5. Textbook examples (hello world variations)

Focus on realistic scenarios that demonstrate:
1. Complex business logic translation
2. Technical requirement implementation
3. Error handling documentation
4. API usage patterns
5. Resource management strategies
"""

NL2CODE_CODE2NL_USER_PROMPT = """
You are helping create a benchmark for code-natural language translation capabilities. Your task is to generate a coding scenario that tests an LLM's ability to translate
between C++ code and documentation effectively. The scenario should include:

Generate a single JSONL entry testing code-to-comment and comment-to-code capabilities.

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-code2NL-NL2code"
- language: "cpp"
- prefix: The segment that establishes the code-comment relationship before the completion
- suffix: The segment that follows the completion with code or comments
- golden_completion: The accurate completion that translates between code and comments and that maintains consistency with prefix/suffix and will pass all assertions AND should include necessary assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL JSON FIELD REQUIREMENTS:
1. ALWAYS include ALL required JSON fields listed above, even if empty
2. The "assertions" field MUST be present with an empty string value: "assertions": ""
3. Do NOT omit any fields from your JSON object
4. Format example showing required empty assertions field:
   {"id": "42", ..., "assertions": ""}
5. INCORRECT: {"id": "42", ...} - missing assertions field

CRITICAL CHANGE - NEW SUFFIX REQUIREMENTS:
1. The suffix must contain both execution code AND assertion code
2. Include assert() statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same function/class as the code being tested
4. DO NOT create separate assertion functions or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Header Inclusion Requirements:
1. Do NOT include header inclusions unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included header must serve a clear purpose
3. Do not include "just in case" headers that aren't used
4. All required header inclusions must appear in the prefix section
5. If a header is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include <cassert> header for assert() statements

PREFIX LENGTH REQUIREMENTS - CRITICAL:
1. The PREFIX section MUST be SUBSTANTIALLY LONGER than other sections
2. The prefix MUST be AT LEAST 50-60 lines of code - this is an absolute requirement
3. Provide extensive context and setup code in the prefix
4. Include helper methods, utility classes, and related code structures
5. Add detailed comments and explanations within the prefix
6. The prefix should demonstrate a comprehensive but incomplete implementation
7. Add relevant constants, configuration objects, and data structure initialization

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a method/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper indentation when exiting blocks
4. All code blocks must be properly closed

The code or comment to translate can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct translation.

Code requirements:
1. Must be fully executable C++ code
2. All assertions must pass when code is run
3. Include all necessary header files
4. Mock external dependencies
5. Clean up resources properly using RAII principles
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of functions or classes
2. ALL code must be contained within proper C++ scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within functions (such as main() or other functions)
5. ALWAYS ensure code is properly nested within appropriate class and function structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and functions are properly matched with braces {}
9. DO NOT leave any code statements outside of function bodies
10. Place all assertions within appropriate functions (main(), test(), etc.)

CRITICAL ASSERTION PLACEMENT:
1. All assert() statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same function as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use assert(condition) format for all assertions
7. Make sure <cassert> is included for assert() statements

Documentation Assertion Requirements:
1. When testing generated documentation:
- Use substring checks for key terms: 'assert(docString.find("key_term") != std::string::npos);'
- Check for presence of required sections: 'assert(docString.find("@param") != std::string::npos);'
- Verify coverage of important concepts
- Don't require exact string matches

2. When testing generated code:
- Verify functional requirements
- Test edge cases
- Validate error handling
- Check return values

Important Balance Requirements:
1. Maintain a 50/50 split between:
    - Code-to-Comment: Generate documentation for existing code
    - Comment-to-Code: Generate code from documentation
2. For Code-to-Comment tasks:
    - Provide complex, working code in the prefix
    - Golden completion should be comprehensive documentation
    - Assertions should verify documentation completeness
3. For Comment-to-Code tasks:
    - Provide detailed requirements/documentation in the prefix
    - Golden completion should be the implementation
    - Assertions should verify functional requirements

Important:
- Use realistic business/technical scenarios
- Avoid trivial examples (factorial, fibonacci, etc.)
- Test complex documentation/implementation translations
- Keep verification code before cleanup
- Use standard C++ assertion mechanisms or testing frameworks (catch2, gtest, etc.)
- Ensure all assertions pass

Requirements:
1. The scenario should demonstrate clear documentation patterns
2. The completion section should focus on bidirectional translation
3. The pattern should follow Doxygen or other C++ documentation best practices
4. Ground truth should maintain consistency between code and comments
5. Assertions should verify documentation accuracy
6. Include examples of both code-to-comment and comment-to-code tasks

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language": "cpp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you included all assertions DIRECTLY IN THE SUFFIX code?
9. Have you verified that assertions will pass when the code is executed?
10. Is the assertions field included with an empty string value ("assertions": "")?
11. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

CODE_PURPOSE_UNDERSTANDING_SYSTEM_PROMPT = """
You are an expert C++ developer tasked with creating benchmark examples for testing semantic understanding and code purpose comprehension capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to understand and continue code based on its underlying business logic and domain context.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C++ that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical scenarios that test understanding of code intent and business purpose. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - String/text manipulation
    - Functional programming 
    - Iterators/algorithms
    - Lambda functions/function pointers
    - Data structures
    - OOP patterns
    - Error handling
    - Multithreading/concurrency
    - Event handling

    Domain Context (choose ONE):
    - Scientific computing (data analysis, statistics, simulations)
    - Media processing (audio, image, video)
    - System operations (logging, monitoring, deployment)
    - Data validation (schemas, cleaning, normalization)
    - Network protocols (APIs, messaging, sync/async)
    - Security (encryption, authentication, auditing)
    - Analytics (metrics, reporting, visualization)
    - Game mechanics (physics, AI, state machines)
    - Tool automation (builds, tests, deployment)
2. Ensure patterns demonstrate clear semantic meaning and domain context
3. Create ground truth completions that maintain business logic consistency
4. Write assertions that meaningfully test both semantic correctness and business rule compliance
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C++
    - All assertions must pass when code is run
    - Include necessary headers
    - Handle memory management and cleanup of resources
    - Use proper exception handling
    - Include minimal working examples
    - Mock external dependencies where needed
7. Write robust assertions that:
    - Verify actual behavior
    - Test parameter ordering
    - Check error conditions
    - Validate return values
    - Mock external resources

When generating examples:
1. Focus on domain-specific logic and business rules
2. Test comprehension of underlying code purpose
3. Ensure patterns reflect real-world business scenarios
4. Include semantic edge cases where relevant
5. Keep code focused on demonstrating clear business intent
"""

CODE_PURPOSE_UNDERSTANDING_USER_PROMPT = """
You are helping create a benchmark for code purpose understanding capabilities. Your task is to generate a coding scenario that tests an LLM's ability to comprehend and
continue C++ code based on its semantic meaning and business context. The scenario should include:

Generate a single JSONL entry testing code purpose understanding capabilities. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - String/text manipulation
    - Functional programming 
    - Iterators/algorithms
    - Lambda functions/function pointers
    - Data structures
    - OOP patterns
    - Error handling
    - Multithreading/concurrency
    - Event handling

    Domain Context (choose ONE):
    - Scientific computing (data analysis, statistics, simulations)
    - Media processing (audio, image, video)
    - System operations (logging, monitoring, deployment)
    - Data validation (schemas, cleaning, normalization)
    - Network protocols (APIs, messaging, sync/async)
    - Security (encryption, authentication, auditing)
    - Analytics (metrics, reporting, visualization)
    - Game mechanics (physics, AI, state machines)
    - Tool automation (builds, tests, deployment)

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines
   - Use \\t for tabs
   - Use \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. Do NOT include formatting or indentation outside the JSON structure
5. DO NOT use markdown code blocks (```) in your response
6. Test your JSON structure before completing your response

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-code-purpose-understanding"
- language: "cpp"
- prefix: The code that comes before the completion (may or may not establish the semantic pattern)
- suffix: The code that follows the completion (may or may not establish the semantic pattern) - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: The semantically appropriate completion that maintain consistency with prefix/suffix and will pass all assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL JSON FIELD REQUIREMENTS:
1. ALWAYS include ALL required JSON fields listed above, even if empty
2. The "assertions" field MUST be present with an empty string value: "assertions": ""
3. Do NOT omit any fields from your JSON object
4. Format example showing required empty assertions field:
   {"id": "42", ..., "assertions": ""}
5. INCORRECT: {"id": "42", ...} - missing assertions field

CRITICAL CHANGE - NEW SUFFIX REQUIREMENTS:
1. The suffix must contain both execution code AND assertion code
2. Include assert() statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same function/class as the code being tested
4. DO NOT create separate assertion functions or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Header Include Requirements:
1. Do NOT include headers unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included header must serve a clear purpose
3. Do not include "just in case" headers that aren't used
4. All required headers must appear in the prefix section
5. If a header is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include <cassert> header for assert() statements

PREFIX LENGTH REQUIREMENTS - CRITICAL:
1. The PREFIX section MUST be SUBSTANTIALLY LONGER than other sections
2. The prefix MUST be AT LEAST 50-60 lines of code - this is an absolute requirement
3. Provide extensive context and setup code in the prefix
4. Include helper functions, utility methods, and related code structures
5. Add detailed comments and explanations within the prefix
6. The prefix should demonstrate a comprehensive but incomplete implementation
7. Add relevant constants, configuration objects, type definitions, and data structure initialization

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a function/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper indentation when exiting blocks
4. All code blocks must be properly closed

The semantic pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the semantic pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C++ code
2. All assertions must pass when run
3. Include all necessary headers
4. Mock external dependencies
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of functions or classes
2. ALL code must be contained within proper C++ scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within functions (such as main() or other functions)
5. ALWAYS ensure code is properly nested within appropriate class and function structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and functions are properly matched with braces {}
9. DO NOT leave any code statements outside of function bodies
10. Place all assertions within appropriate functions (main(), test(), etc.)

CRITICAL ASSERTION PLACEMENT:
1. All assert() statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same function as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use assert(condition) format for all assertions
7. Make sure <cassert> is included for assert() statements

Requirements:
1. The scenario should demonstrate clear business purpose
2. The completion section should focus on domain-specific logic
3. The pattern should follow appropriate business rules and domain conventions
4. Ground truth should maintain semantic consistency
5. Assertions should verify business logic correctness
6. Include comments indicating expected business behavior and domain context

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-code-purpose-understanding", "language": "cpp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you included all assertions DIRECTLY IN THE SUFFIX code?
9. Have you verified that assertions will pass when the code is executed?
10. Is the assertions field included with an empty string value ("assertions": "")?
11. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert C++ developer tasked with creating benchmark examples for testing low-context pattern matching capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to recognize and continue established patterns in code with minimal surrounding context.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C++ that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical low-context scenarios from these categories (rotate through them):
    - Data structure manipulation (arrays, vectors, maps, sets)
    - String processing and text manipulation
    - Object-oriented patterns (classes, inheritance, polymorphism)
    - Generic programming constructs (templates)
    - Error handling and exception patterns
    - Memory management patterns (smart pointers, RAII)
    - Iterator and container patterns
    - Callback and function pointer patterns
    - Algorithm implementation and STL usage
    - Multi-threading and concurrency patterns
2. Ensure patterns are clear and identifiable even with minimal context
3. Create ground truth completions that represent best practices while handling potential ambiguity
4. Write assertions that meaningfully test both pattern adherence and functionality across multiple valid completions where applicable
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C++
    - All assertions must pass when code is run
    - Include necessary headers
    - Handle cleanup of resources
    - Use proper exception handling
    - Include minimal working examples
    - Mock external dependencies where needed
    - Utilize appropriate C++ idioms and patterns
7. Write robust assertions that:
    - Verify actual behavior
    - Test parameter ordering
    - Check error conditions
    - Validate return values
    - Mock external resources

When generating examples:
1. Focus on universal, standardized programming patterns
2. Test the model's ability to handle ambiguity and make reasonable assumptions
3. Ensure patterns follow widely-used conventions that are recognizable with minimal context
4. Include multiple valid completions in assertions where appropriate
5. Keep code minimal while still maintaining semantic clarity
6. The combined length of prefix and suffix should be 10-20 lines total for true low-context scenarios
"""

LOW_CONTEXT_USER_PROMPT = """
You are helping create a benchmark for low-context code pattern matching capabilities. Your task is to generate a coding scenario that tests an LLM's ability to recognize and
complete patterns in C++ code with minimal surrounding context. The scenario should include:

Generate a single JSONL entry testing low-context capabilities. Choose from one of these categories (rotate through them):
- Data structure manipulation (arrays, vectors, maps, sets)
- String processing and text manipulation
- Object-oriented patterns (classes, inheritance, polymorphism)
- Generic programming constructs (templates)
- Error handling and exception patterns
- Memory management patterns (smart pointers, RAII)
- Iterator and container patterns
- Callback and function pointer patterns
- Algorithm implementation and STL usage
- Multi-threading and concurrency patterns

STRICTLY PROHIBITED EXAMPLES - DO NOT GENERATE:
1. Basic container operations (vector/map insertion, iteration, simple queries)
2. Simple string manipulation (concat, substr, find)
3. Basic class definitions or inheritance
4. Simple exception handling (try/catch without complexity)
5. Basic smart pointer usage (simple std::shared_ptr creation)
6. Simple algorithms (sort, find, accumulate with basic predicates)
7. Basic template instantiation
8. Simple loops or conditionals
9. Basic multi-threading (simple thread creation)
10. Any example that could be solved by pattern matching without understanding

REQUIRED COMPLEXITY LEVEL:
Instead, you MUST create examples that demonstrate advanced C++ patterns such as:

For Template Metaprogramming:
- Template specialization with SFINAE
- Variadic templates with parameter packs
- Tag dispatching patterns
- Type traits and compile-time conditions
- Expression templates
- Policy-based design
- Compile-time computation

For Memory Management:
- Custom allocators
- Memory pools and arenas
- PIMPL idiom implementations
- Custom smart pointer designs
- Object lifetime management patterns
- Placement new with custom allocation
- Move semantics with perfect forwarding

For RAII and Resource Handling:
- Complex scopeguard patterns
- Resource acquisition patterns
- Transaction-like RAII patterns
- Multi-resource management
- Complex cleanup patterns
- Exception-safe resource handling
- Hierarchical resource management

For Multi-threading:
- Lock-free data structures
- Complex synchronization patterns
- Reader-writer lock implementations
- Thread pool designs
- Work stealing patterns
- Memory ordering specifications
- Atomic operations with memory fences

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines
   - Use \\t for tabs
   - Use \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. Do NOT include formatting or indentation outside the JSON structure
5. DO NOT use markdown code blocks (```) in your response
6. Test your JSON structure before completing your response

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-low-context"  
- language: "cpp"
- prefix: The code that comes before the completion (may or may not establish the pattern)
- suffix: The code that follows the completion (may or may not establish the pattern) - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: Multiple valid completions that maintain consistency with prefix/suffix and will pass all assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL COMPLEXITY VALIDATION:
Before submitting your example, verify that it meets these criteria:
1. Would this example challenge a senior C++ developer?
2. Does it require understanding of advanced language features?
3. Is it significantly more complex than basic container operations or string manipulation?
4. Does it demonstrate a pattern that would be found in production-quality code?
5. Would it be impossible to solve correctly through simple pattern matching?
6. Does it require genuine understanding of C++ language semantics?

If you answer "no" to ANY of these questions, your example is TOO SIMPLE. Revise it to be more complex.

CRITICAL JSON FIELD REQUIREMENTS:
1. ALWAYS include ALL required JSON fields listed above, even if empty
2. The "assertions" field MUST be present with an empty string value: "assertions": ""
3. Do NOT omit any fields from your JSON object
4. Format example showing required empty assertions field:
   {"id": "42", ..., "assertions": ""}
5. INCORRECT: {"id": "42", ...} - missing assertions field

CRITICAL CHANGE - NEW SUFFIX REQUIREMENTS:
1. The suffix must contain both execution code AND assertion code
2. Include assert() statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same function/class as the code being tested
4. DO NOT create separate assertion functions or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

CRITICAL LOW CONTEXT REQUIREMENTS:
1. The prefix and suffix combined should be ONLY 10-20 lines total for true low-context scenarios
2. Focus on concise, universally recognizable patterns that can be understood with minimal context
3. Keep the context deliberately minimal while ensuring the pattern is still identifiable
4. Use clear but brief code that establishes a recognizable pattern
5. The pattern should be non-trivial but recognizable to C++ developers

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Header Include Requirements:
1. Do NOT include headers unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included header must serve a clear purpose
3. Do not include "just in case" headers that aren't used
4. All required headers must appear in the prefix section
5. If a header is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include <cassert> header for assert() statements

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a function/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper indentation when exiting blocks
4. All code blocks must be properly closed

The golden completion should demonstrate understanding and correct usage of the low-context pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C++ code
2. All assertions must pass when run
3. Include all necessary headers
4. Mock external dependencies
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of functions or classes
2. ALL code must be contained within proper C++ scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within functions (such as main() or other functions)
5. ALWAYS ensure code is properly nested within appropriate class and function structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and functions are properly matched with braces {}
9. DO NOT leave any code statements outside of function bodies
10. Place all assertions within appropriate functions (main(), test(), etc.)

CRITICAL ASSERTION PLACEMENT:
1. All assert() statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same function as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use assert(condition) format for all assertions
7. Make sure <cassert> is included for assert() statements

Requirements:
1. The scenario should demonstrate a clear pattern recognizable with minimal context
2. The completion section should focus on universal programming patterns
3. The pattern should follow widely-used conventions and standard library knowledge
4. Ground truth should acknowledge multiple valid completions where appropriate
5. Assertions should verify all acceptable pattern variations
6. Include comments indicating potential ambiguities and alternative completions

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-low-context", "language": "cpp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Have you used clear distinctions between golden_completion and suffix?
7. Have you included all assertions DIRECTLY IN THE SUFFIX code?
8. Have you verified that assertions will pass when the code is executed?
9. Is the assertions field included with an empty string value ("assertions": "")?
10. Have you verified that ALL required fields are present in your JSON?
11. Have you verified your example is NOT one of the prohibited trivial examples?
12. Does your example meet ALL the complexity validation criteria?
13. Does your example demonstrate genuinely advanced C++ features?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- KEEP COMBINED PREFIX AND SUFFIX TO 10-20 LINES TOTAL
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field
- Ensure your example demonstrates genuine C++ complexity

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert C++ developer tasked with creating benchmark examples for testing pattern matching capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to recognize and continue established patterns in code.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C++ that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical pattern matching scenarios that real developers encounter. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - String/text manipulation
    - Functional programming 
    - Iterators/generators
    - Higher-order functions
    - Data structures
    - OOP patterns
    - Error handling
    - Memory management
    - Template metaprogramming
    - Algorithm implementation

    Domain Context (choose ONE):
    - Scientific computing (data analysis, statistics, simulations)
    - Media processing (audio, image, video)
    - System operations (logging, monitoring, deployment)
    - Data validation (schemas, cleaning, normalization)
    - Network protocols (APIs, messaging, sync/async)
    - Security (encryption, authentication, auditing)
    - Analytics (metrics, reporting, visualization)
    - Game mechanics (physics, AI, state machines)
    - Tool automation (builds, tests, deployment)
2. Ensure patterns are clear and identifiable but not trivially simple
3. Create ground truth completions that represent best practices
4. Write assertions that meaningfully test both pattern adherence and functionality
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C++
    - All assertions must pass when code is run
    - Include necessary headers and imports
    - Handle memory management properly
    - Use proper exception handling
    - Include minimal working examples
    - Mock external dependencies where needed
    - Utilize appropriate C++ features (STL, templates, etc.)
7. Write robust assertions that:
    - Verify actual behavior
    - Test parameter ordering
    - Check error conditions
    - Validate return values
    - Mock external resources

When generating examples:
1. Focus on realistic, practical scenarios
2. Avoid patterns that are too project-specific
3. Ensure patterns are clear enough to be recognized by an LLM
4. Include edge cases in assertions where relevant
5. Keep code self-contained and independently verifiable
6. Leverage C++-specific features like templates, RAII, and STL algorithms where appropriate
"""

PATTERN_MATCHING_USER_PROMPT = """
You are helping create a benchmark for code pattern matching capabilities. Your task is to generate a coding scenario that tests an LLM's ability to recognize and
complete patterns in C++ code. The scenario should include:

Generate a single JSONL entry testing pattern matching capabilities. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - Functional programming 
    - Iterators/generators
    - Higher-order functions
    - Error handling
    - Memory management
    - Template metaprogramming
    - Algorithm implementation

    Domain Context (choose ONE):
    - Analytics (metrics, reporting, visualization)
    - Game mechanics (physics, AI, state machines)
    - Tool automation (builds, tests, deployment)

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines
   - Use \\t for tabs
   - Use \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. Do NOT include formatting or indentation outside the JSON structure
5. DO NOT use markdown code blocks (```) in your response
6. Test your JSON structure before completing your response

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-pattern-matching"
- language: "cpp"
- prefix: The code that comes before the completion (MUST establish or begin a clear pattern)
- suffix: The code that follows the completion (may continue or complete the pattern) - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: The semantically appropriate completion that maintain consistency with prefix/suffix and will pass all assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL JSON FIELD REQUIREMENTS:
1. ALWAYS include ALL required JSON fields listed above, even if empty
2. The "assertions" field MUST be present with an empty string value: "assertions": ""
3. Do NOT omit any fields from your JSON object
4. Format example showing required empty assertions field:
   {"id": "42", ..., "assertions": ""}
5. INCORRECT: {"id": "42", ...} - missing assertions field

CRITICAL CHANGE - NEW SUFFIX REQUIREMENTS:
1. The suffix must contain both execution code AND assertion code
2. Include assert() statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same function/class as the code being tested
4. DO NOT create separate assertion functions or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

Critical Pattern Matching Requirements:
1. A CLEAR, IDENTIFIABLE PATTERN MUST be established in either the prefix or suffix
2. The golden_completion MUST follow this established pattern (not create a new one)
3. The pattern should be specific enough that random code wouldn't work
4. Include at least 2-3 examples of the pattern in the prefix to establish it
5. Ensure the pattern follows recognizable conventions in the chosen domain
6. The pattern should be evident to anyone familiar with C++

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Header Include Requirements:
1. Do NOT include headers unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included header must serve a clear purpose
3. Do not include "just in case" headers that aren't used
4. All required headers must appear in the prefix section
5. If a header is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include <cassert> header for assert() statements

PREFIX LENGTH REQUIREMENTS - CRITICAL:
1. The PREFIX section MUST be SUBSTANTIALLY LONGER than other sections
2. The prefix MUST be AT LEAST 50-60 lines of code - this is an absolute requirement
3. Provide extensive context and setup code in the prefix
4. Include helper functions, utility methods, and related code structures
5. Add detailed comments and explanations within the prefix
6. The prefix should demonstrate a comprehensive but incomplete implementation
7. Add relevant constants, configuration objects, and data structure initialization

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a function/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper indentation when exiting blocks
4. All code blocks must be properly closed

The pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C++ code
2. All assertions must pass when run
3. Include all necessary headers
4. Mock external dependencies when needed
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of functions or classes
2. ALL code must be contained within proper C++ scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within functions (such as main() or other functions)
5. ALWAYS ensure code is properly nested within appropriate class and function structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and functions are properly matched with braces {}
9. DO NOT leave any code statements outside of function bodies
10. Place all assertions within appropriate functions (main(), test(), etc.)

CRITICAL ASSERTION PLACEMENT:
1. All assert() statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same function as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use assert(condition) format for all assertions
7. Make sure <cassert> is included for assert() statements

Requirements:
1. The scenario MUST demonstrate a clear, identifiable pattern
2. The completion section should be non-trivial but focused on pattern matching
3. The pattern should follow C++ best practices and common conventions
4. Ground truth should demonstrate the ideal pattern continuation
5. Assertions should verify both pattern adherence and functionality
6. Include comments indicating the expected pattern continuation

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-pattern-matching", "language": "cpp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you included all assertions DIRECTLY IN THE SUFFIX code?
9. Have you verified that assertions will pass when the code is executed?
10. Is the assertions field included with an empty string value ("assertions": "")?
11. Have you verified that ALL required fields are present in your JSON?
12. Have you verified your example is NOT one of the prohibited trivial examples?
13. Does your example meet ALL the complexity validation criteria?
14. Does your example demonstrate genuinely advanced C++ features?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- ENSURE A CLEAR PATTERN IS ESTABLISHED that the golden completion must follow
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

API_USAGE_SYSTEM_PROMPT = """
You are an expert C++ developer tasked with creating benchmark examples for testing rare API usage and uncommon library function capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to recognize and continue established patterns in code involving uncommon APIs and library functions.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C++ that passes all assertions.

Key Responsibilities:
1. Generate diverse examples from these API categories (rotate through them, don't focus only on file operations or network protocols):
    - Text and font processing (HarfBuzz, FreeType, ICU)
    - Graphics and math libraries (DirectXMath, Eigen, GLM, OpenGL)
    - Security/cryptography APIs (OpenSSL, Botan, Crypto++, wolfSSL)
    - System-level APIs (Windows SDK, POSIX, Linux Kernel, BSD, Mach)
    - Standard libraries (C Standard Library, C++ Standard Library, GNU C Library)
    - Web API integration (libcurl, Boost.Beast, cpp-httplib, cpprestsdk)
    - Machine learning libraries (OpenCV, TensorFlow C++, PyTorch C++, ONNX)
    - Cloud services (AWS SDK for C++, Azure SDK for C++, gRPC)
    - Database interfaces (SQLite, MySQL Connector C++, MongoDB C++ Driver, Redis)
    - File formats and parsing (RapidJSON, nlohmann/json, tinyxml2, yaml-cpp)
    - Web frameworks (Drogon, Crow, oatpp, Pistache)
    - Network protocols (Boost.Asio, ZeroMQ, nanomsg)
    - Scientific computing (Eigen, Armadillo, Intel MKL, BLAS, LAPACK)
    - GUI frameworks (Qt, wxWidgets, ImGui, GTK, FLTK)
    - Multimedia (SDL, FFmpeg, OpenAL, libsndfile)
    - Compression (zlib, bzip2, LZMA, LZ4, Zstandard)
    - Cross-platform development (Boost, Qt, wxWidgets)
    - Mobile development (Android NDK, iOS SDK, Core Foundation)
    - Testing frameworks (Google Test, Catch2, Boost.Test)
    - Hardware acceleration (Intel Intrinsics, ARM NEON, CUDA, OpenCL)
    - Legacy/deprecated APIs

2. Ensure patterns are clear and identifiable even with uncommon or deprecated APIs
3. Create ground truth completions that represent best practices while handling API versioning
4. Write assertions that meaningfully test both API correctness and parameter ordering
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C++
    - All assertions must pass when code is run
    - Include necessary includes and namespaces
    - Handle cleanup of resources
    - Use proper exception handling
    - Include minimal working examples
    - Mock external dependencies where needed
7. Write robust assertions that:
    - Verify actual API behavior
    - Test parameter ordering
    - Check error conditions
    - Validate return values
    - Mock external resources

When generating examples:
1. Focus on less common library functions and domain-specific APIs
2. Test the model's handling of deprecated but valid API patterns
3. Ensure patterns include correct parameter ordering and naming conventions
4. Include edge cases in API usage where relevant
5. Keep code focused on demonstrating rare but valid API interactions
"""

API_USAGE_USER_PROMPT = """
You are helping create a benchmark for rare API usage capabilities. Your task is to generate a coding scenario that tests an LLM's ability to recognize and
complete patterns in C++ code involving uncommon or deprecated APIs.

Generate a single JSONL entry testing rare API usage capabilities. Choose from one of these categories (rotate through them, don't focus only on file operations or network protocols):
    - Text and font processing (HarfBuzz, FreeType, ICU)
    - Graphics and math libraries (DirectXMath, Eigen, GLM, OpenGL)
    - Security/cryptography APIs (OpenSSL, Botan, Crypto++, wolfSSL)
    - System-level APIs (Windows SDK, POSIX, Linux Kernel, BSD, Mach)
    - Standard libraries (C Standard Library, C++ Standard Library, GNU C Library)
    - Web API integration (libcurl, Boost.Beast, cpp-httplib, cpprestsdk)
    - Machine learning libraries (OpenCV, TensorFlow C++, PyTorch C++, ONNX)
    - Cloud services (AWS SDK for C++, Azure SDK for C++, gRPC)
    - Database interfaces (SQLite, MySQL Connector C++, MongoDB C++ Driver, Redis)
    - File formats and parsing (RapidJSON, nlohmann/json, tinyxml2, yaml-cpp)
    - Web frameworks (Drogon, Crow, oatpp, Pistache)
    - Network protocols (Boost.Asio, ZeroMQ, nanomsg)
    - Scientific computing (Eigen, Armadillo, Intel MKL, BLAS, LAPACK)
    - GUI frameworks (Qt, wxWidgets, ImGui, GTK, FLTK)
    - Multimedia (SDL, FFmpeg, OpenAL, libsndfile)
    - Compression (zlib, bzip2, LZMA, LZ4, Zstandard)
    - Cross-platform development (Boost, Qt, wxWidgets)
    - Mobile development (Android NDK, iOS SDK, Core Foundation)
    - Testing frameworks (Google Test, Catch2, Boost.Test)
    - Hardware acceleration (Intel Intrinsics, ARM NEON, CUDA, OpenCL)
    - Legacy/deprecated APIs

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Your response MUST be a syntactically valid JSON object
2. PROPERLY ESCAPE all special characters in strings:
   - Use \\" for double quotes inside strings
   - Use \\n for newlines
   - Use \\t for tabs
   - Use \\\\ for backslashes
3. The entire JSON object must be on a SINGLE LINE
4. Do NOT include formatting or indentation outside the JSON structure
5. DO NOT use markdown code blocks (```) in your response
6. Test your JSON structure before completing your response

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-api-usage"  
- language: "cpp"
- prefix: The code that comes before the completion (may or may not establish the API pattern)
- suffix: The code that follows the completion (may or may not establish the API pattern) - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: The correct API implementation that maintains consistency with prefix/suffix and will pass all assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL JSON FIELD REQUIREMENTS:
1. ALWAYS include ALL required JSON fields listed above, even if empty
2. The "assertions" field MUST be present with an empty string value: "assertions": ""
3. Do NOT omit any fields from your JSON object
4. Format example showing required empty assertions field:
   {"id": "42", ..., "assertions": ""}
5. INCORRECT: {"id": "42", ...} - missing assertions field

CRITICAL CHANGE - NEW SUFFIX REQUIREMENTS:
1. The suffix must contain both execution code AND assertion code
2. Include assert() statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same function/class as the code being tested
4. DO NOT create separate assertion functions or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Include Requirements:
1. Do NOT include headers unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included header must serve a clear purpose
3. Do not include "just in case" headers that aren't used
4. All required includes must appear in the prefix section
5. If an include is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include <cassert> header for assert() statements

PREFIX LENGTH REQUIREMENTS - CRITICAL:
1. The PREFIX section MUST be SUBSTANTIALLY LONGER than other sections
2. The prefix MUST be AT LEAST 50-60 lines of code - this is an absolute requirement
3. Provide extensive context and setup code in the prefix
4. Include helper functions, utility classes, and related code structures
5. Add detailed comments and explanations within the prefix
6. The prefix should demonstrate a comprehensive but incomplete implementation
7. Add relevant constants, configuration objects, and data structure initialization

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a function/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper dedenting when exiting blocks
4. All code blocks must be properly closed

The API pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the API pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C++ code
2. All assertions must pass when run
3. Include all necessary headers and namespaces
4. Mock external dependencies
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of functions or classes
2. ALL code must be contained within proper C++ scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within functions (such as main() or other functions)
5. ALWAYS ensure code is properly nested within appropriate class and function structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and functions are properly matched with braces {}
9. DO NOT leave any code statements outside of function bodies
10. Place all assertions within appropriate functions (main(), test(), etc.)

CRITICAL ASSERTION PLACEMENT:
1. All assert() statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same function as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use assert(condition) format for all assertions
7. Make sure <cassert> is included for assert() statements

Requirements:
1. The scenario should demonstrate a clear pattern recognizable with the given context
2. The completion section should focus on rare library functions
3. The pattern should follow correct API conventions across different versions
4. Ground truth should demonstrate proper parameter ordering
5. Assertions should verify API behavior and parameter correctness
6. Include comments indicating API version compatibility and parameter requirements

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-api-usage", "language": "cpp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you included all assertions DIRECTLY IN THE SUFFIX code?
9. Have you verified that assertions will pass when the code is executed?
10. Is the assertions field included with an empty string value ("assertions": "")?
11. Have you verified that ALL required fields are present in your JSON?
12. Have you verified your example is NOT one of the prohibited trivial examples?
13. Does your example meet ALL the complexity validation criteria?
14. Does your example demonstrate genuinely advanced C++ features?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/finally blocks if needed
- Maintain correct execution order
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""