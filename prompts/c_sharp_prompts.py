SYNTAX_COMPLETION_SYSTEM_PROMPT = """
You are an expert C# developer tasked with creating benchmark examples for testing syntax completion and language-specific structure capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to complete complex syntactical patterns and nested structures.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C# that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical scenarios that test understanding of language-specific syntax. Choose ONE syntax pattern to test (rotate through them):
    Syntax Categories:
    a. Nested Control Structures
    - Multiple levels of if/else conditions
    - Nested loop structures (for/foreach/while/do-while combinations)
    - Try/catch with multiple catch blocks
    - Using statements for resource management
    - LINQ query expressions with complex iterations

    b. Complex C# Syntax Features
    - Class inheritance and method overrides
    - Generic programming patterns
    - Lambda expressions and method references
    - LINQ operations with deferred execution
    - Attributes and reflection

    c. Multi-line Syntax Patterns
    - Method chaining patterns
    - Builder pattern implementations
    - Fluent interface structures
    - String interpolation and formatting
    - Method overloading resolution

    d. Error Handling Patterns
    - Try/catch combinations with exception hierarchies
    - Using statements for resource management
    - Nullable reference types usage
    - Exception handling best practices
    - Custom exception handling
    
2. Ensure patterns demonstrate proper nesting and indentation
3. Create ground truth completions that maintain syntactic correctness
4. Write assertions that meaningfully test structural integrity and syntax validity
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C#
    - All assertions must pass when code is run
    - Include necessary using directives
    - Handle cleanup of resources using using statements
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
complex syntactical structures and maintain proper formatting in C# code. The scenario should include:

Generate a single JSONL entry testing syntax completion capabilities. Choose ONE syntax pattern to test (rotate through them):
    Syntax Categories:
    a. Nested Control Structures
    - Multiple levels of if/else conditions
    - Nested loop structures (for/foreach/while/do-while combinations)
    - Try/catch with multiple catch blocks
    - Using statements for resource management
    - LINQ query expressions with complex iterations

    b. Complex C# Syntax Features
    - Class inheritance and method overrides
    - Generic programming patterns
    - Lambda expressions and method references
    - LINQ operations with deferred execution
    - Attributes and reflection

    c. Multi-line Syntax Patterns
    - Method chaining patterns
    - Builder pattern implementations
    - Fluent interface structures
    - String interpolation and formatting
    - Method overloading resolution

    d. Error Handling Patterns
    - Try/catch combinations with exception hierarchies
    - Using statements for resource management
    - Nullable reference types usage
    - Exception handling best practices
    - Custom exception handling

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-syntax-completion"
- language: "c_sharp"
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
2. Include Debug.Assert statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same method/class as the code being tested
4. DO NOT create separate assertion methods or classes
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

Using Directive Requirements:
1. Do NOT include using directives unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included using directive must serve a clear purpose
3. Do not include "just in case" using directives that aren't used
4. All required using directives must appear in the prefix section
5. If a using directive is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include "using System.Diagnostics;" for Debug.Assert statements

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

The pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C# code
2. All assertions must pass when code is run
3. Include all necessary using directives
4. Mock external dependencies
5. Clean up resources properly using using statements
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL NEWLINE HANDLING - READ CAREFULLY:
1. For proper JSON string escaping, represent newlines as "\\n" (backslash + n)
2. When writing this in the Python prompt, use "\\\\n" (double backslash + n)
3. Example of CORRECT newline escaping in the JSON output:
   "prefix": "using System;\nusing System.Collections.Generic;\n"
4. Example of CORRECT way to write this in the Python string:
   "prefix": "using System;\\nusing System.Collections.Generic;\\n"
5. NEVER use actual newline characters in your JSON string values
6. Ensure all code blocks are properly terminated and have consistent indentation

CODE FORMATTING REQUIREMENTS:
1. Make sure all C# code uses standard C# formatting conventions
2. Use consistent 4-space indentation throughout the code
3. Properly close all code blocks, methods, classes, and namespaces
4. All code must be syntactically valid C# when the prefix + golden_completion + suffix are combined
5. Test the combined code mentally to verify it will compile and run correctly

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of methods or classes
2. ALL code must be contained within proper C# scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within methods (such as Main, Test, or other methods)
5. ALWAYS ensure code is properly nested within appropriate class and method structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and methods are properly matched
9. DO NOT leave any code statements outside of method bodies
10. Place all assertions within appropriate methods (Main, Test, etc.)

CRITICAL ASSERTION PLACEMENT:
1. All Debug.Assert statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same method as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use Debug.Assert(condition, "message") format for all assertions
7. Make sure System.Diagnostics is imported for Debug.Assert statements

ADDITIONAL CRITICAL REQUIREMENTS:
1. When preparing your prefix, golden_completion, and suffix, ensure they can be combined into a valid C# program without syntax errors.
2. If your prefix defines a class or namespace:
   - The golden_completion must continue within that same class/namespace scope
   - The suffix must continue and properly close that same class/namespace scope
3. Avoid defining the same class or method in both prefix and suffix
4. Make sure all namespaces, classes, and methods are properly opened and closed across the combined code
5. The prefix should typically set up the context (beginning of methods/classes)
6. The golden_completion should provide the middle part
7. The suffix should close all open scopes and add assertions
8. Test the combined code mentally to verify it compiles and runs properly

Example of GOOD structure:
- Prefix: Defines namespace, class, method signature and first part of method body
- Golden completion: Middle part of the method implementation
- Suffix: Final part of method implementation + assertions + method closing + class closing + namespace closing

Example of BAD structure:
- Defining the same class in both prefix and suffix
- Not properly closing namespaces or classes
- Having overlapping code between golden_completion and suffix
- Having inconsistent indentation between the three parts

Requirements:
1. The scenario should demonstrate complex syntax patterns
2. The completion section should focus on language-specific structures
3. The pattern should follow proper indentation and nesting rules
4. Ground truth should maintain consistent formatting
5. Assertions should verify structural integrity
6. Include comments indicating expected syntax and formatting

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-syntax-completion", "language": "c_sharp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": ""}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you verified that NO code exists outside of methods or classes?
9. Have you included all assertions DIRECTLY IN THE SUFFIX code?
10. Have you verified that assertions will pass when the code is executed?
11. Is the assertions field included with an empty string value ("assertions": "")?
12. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- NEVER place code at the global/namespace level - all code must be inside methods
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

NL2CODE_CODE2NL_SYSTEM_PROMPT = """
You are an expert C# developer tasked with creating benchmark examples for testing bidirectional translation between code and natural language capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to translate between code and documentation in both directions.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C# that passes all assertions.

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
    - Resource management (using, IDisposable, memory management)
2. Ensure patterns demonstrate clear alignment between documentation and implementation, with the following requirements (alternate between these):
    For Code-to-Natural Language (50% of test cases):
    - Generate comprehensive documentation for:
        * Method implementations
        * Class definitions
        * Namespace-level code
        * Complex algorithms
        * Error handling logic
    - Documentation should include:
        * Detailed XML documentation comments
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
    - All code must be fully executable C#
    - All assertions must pass when code is run
    - Include necessary using directives
    - Handle resources properly with using statements
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
between C# code and documentation effectively. The scenario should include:

Generate a single JSONL entry testing code-to-comment and comment-to-code capabilities.


Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-code2NL-NL2code"
- language: "c_sharp"
- prefix: The segment that establishes the code-comment relationship before the completion
- suffix: The segment that follows the completion with code or comments  - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: The accurate completion that translates between code and comments and that maintains consistency with prefix/suffix and will pass all assertions
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
2. Include Debug.Assert statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same method/class as the code being tested
4. DO NOT create separate assertion methods or classes
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

Using Directive Requirements:
1. Do NOT include using directives unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included using directive must serve a clear purpose
3. Do not include "just in case" using directives that aren't used
4. All required using directives must appear in the prefix section
5. If a using directive is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include "using System.Diagnostics;" for Debug.Assert statements

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
1. Must be fully executable C# code
2. All assertions must pass when code is run
3. Include all necessary using directives
4. Mock external dependencies
5. Clean up resources properly using using statements
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL NEWLINE HANDLING - READ CAREFULLY:
1. For proper JSON string escaping, represent newlines as "\\n" (backslash + n)
2. When writing this in the Python prompt, use "\\\\n" (double backslash + n)
3. Example of CORRECT newline escaping in the JSON output:
   "prefix": "using System;\nusing System.Collections.Generic;\n"
4. Example of CORRECT way to write this in the Python string:
   "prefix": "using System;\\nusing System.Collections.Generic;\\n"
5. NEVER use actual newline characters in your JSON string values
6. Ensure all code blocks are properly terminated and have consistent indentation

CODE FORMATTING REQUIREMENTS:
1. Make sure all C# code uses standard C# formatting conventions
2. Use consistent 4-space indentation throughout the code
3. Properly close all code blocks, methods, classes, and namespaces
4. All code must be syntactically valid C# when the prefix + golden_completion + suffix are combined
5. Test the combined code mentally to verify it will compile and run correctly

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of methods or classes
2. ALL code must be contained within proper C# scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within methods (such as Main, Test, or other methods)
5. ALWAYS ensure code is properly nested within appropriate class and method structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and methods are properly matched
9. DO NOT leave any code statements outside of method bodies
10. Place all assertions within appropriate methods (Main, Test, etc.)

CRITICAL ASSERTION PLACEMENT:
1. All Debug.Assert statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same method as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use Debug.Assert(condition, "message") format for all assertions
7. Make sure System.Diagnostics is imported for Debug.Assert statements

ADDITIONAL CRITICAL REQUIREMENTS:
1. When preparing your prefix, golden_completion, and suffix, ensure they can be combined into a valid C# program without syntax errors.
2. If your prefix defines a class or namespace:
   - The golden_completion must continue within that same class/namespace scope
   - The suffix must continue and properly close that same class/namespace scope
3. Avoid defining the same class or method in both prefix and suffix
4. Make sure all namespaces, classes, and methods are properly opened and closed across the combined code
5. The prefix should typically set up the context (beginning of methods/classes)
6. The golden_completion should provide the middle part
7. The suffix should close all open scopes and add assertions
8. Test the combined code mentally to verify it compiles and runs properly

Example of GOOD structure:
- Prefix: Defines namespace, class, method signature and first part of method body
- Golden completion: Middle part of the method implementation
- Suffix: Final part of method implementation + assertions + method closing + class closing + namespace closing

Example of BAD structure:
- Defining the same class in both prefix and suffix
- Not properly closing namespaces or classes
- Having overlapping code between golden_completion and suffix
- Having inconsistent indentation between the three parts

Documentation Assertion Requirements:
1. When testing generated documentation:
- Use string checks for key terms: 'Assert.IsTrue(docString.Contains("key_term"));'
- Check for presence of required sections: 'Assert.IsTrue(docString.Contains("<param>"));'
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
- Use standard C# assertion mechanisms or testing frameworks (MSTest, NUnit, xUnit, etc.)
- Ensure all assertions pass

Requirements:
1. The scenario should demonstrate clear documentation patterns
2. The completion section should focus on bidirectional translation
3. The pattern should follow XML documentation or other C# documentation best practices
4. Ground truth should maintain consistency between code and comments
5. Assertions should verify documentation accuracy
6. Include examples of both code-to-comment and comment-to-code tasks

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-code2NL-NL2code", "language": "c_sharp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": ""}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you verified that NO code exists outside of methods or classes?
9. Have you included all assertions DIRECTLY IN THE SUFFIX code?
10. Have you verified that assertions will pass when the code is executed?
11. Is the assertions field included with an empty string value ("assertions": "")?
12. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- NEVER place code at the global/namespace level - all code must be inside methods
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

CODE_PURPOSE_UNDERSTANDING_SYSTEM_PROMPT = """
You are an expert C# developer tasked with creating benchmark examples for testing semantic understanding and code purpose comprehension capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to understand and continue code based on its underlying business logic and domain context.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C# that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical scenarios that test understanding of code intent and business purpose. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - String/text manipulation
    - Functional programming 
    - LINQ/collections
    - Lambda expressions/method references
    - Data structures
    - OOP patterns
    - Exception handling
    - Multithreading/async-await
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
    - All code must be fully executable C#
    - All assertions must pass when code is run
    - Include necessary using statements
    - Follow proper resource management with using statements
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
continue C# code based on its semantic meaning and business context. The scenario should include:

Generate a single JSONL entry testing code purpose understanding capabilities. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - String/text manipulation
    - Functional programming 
    - LINQ/collections
    - Lambda expressions/method references
    - Data structures
    - OOP patterns
    - Exception handling
    - Multithreading/async-await
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

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-code-purpose-understanding"
- language: "c_sharp"
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
2. Include Debug.Assert statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same method/class as the code being tested
4. DO NOT create separate assertion methods or classes
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

Import Requirements:
1. Do NOT include using statements unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included using statement must serve a clear purpose
3. Do not include "just in case" using statements that aren't used
4. All required using statements must appear in the prefix section
5. If a using statement is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include "using System.Diagnostics;" for Debug.Assert statements

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

The semantic pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the semantic pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C# code
2. All assertions must pass when run
3. Include all necessary using statements
4. Mock external dependencies
5. Follow proper resource management
6. Handle exceptions appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL NEWLINE HANDLING - READ CAREFULLY:
1. For proper JSON string escaping, represent newlines as "\\n" (backslash + n)
2. When writing this in the Python prompt, use "\\\\n" (double backslash + n)
3. Example of CORRECT newline escaping in the JSON output:
   "prefix": "using System;\nusing System.Collections.Generic;\n"
4. Example of CORRECT way to write this in the Python string:
   "prefix": "using System;\\nusing System.Collections.Generic;\\n"
5. NEVER use actual newline characters in your JSON string values
6. Ensure all code blocks are properly terminated and have consistent indentation

CODE FORMATTING REQUIREMENTS:
1. Make sure all C# code uses standard C# formatting conventions
2. Use consistent 4-space indentation throughout the code
3. Properly close all code blocks, methods, classes, and namespaces
4. All code must be syntactically valid C# when the prefix + golden_completion + suffix are combined
5. Test the combined code mentally to verify it will compile and run correctly

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of methods or classes
2. ALL code must be contained within proper C# scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within methods (such as Main, Test, or other methods)
5. ALWAYS ensure code is properly nested within appropriate class and method structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and methods are properly matched
9. DO NOT leave any code statements outside of method bodies
10. Place all assertions within appropriate methods (Main, Test, etc.)

CRITICAL ASSERTION PLACEMENT:
1. All Debug.Assert statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same method as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use Debug.Assert(condition, "message") format for all assertions
7. Make sure System.Diagnostics is imported for Debug.Assert statements

ADDITIONAL CRITICAL REQUIREMENTS:
1. When preparing your prefix, golden_completion, and suffix, ensure they can be combined into a valid C# program without syntax errors.
2. If your prefix defines a class or namespace:
   - The golden_completion must continue within that same class/namespace scope
   - The suffix must continue and properly close that same class/namespace scope
3. Avoid defining the same class or method in both prefix and suffix
4. Make sure all namespaces, classes, and methods are properly opened and closed across the combined code
5. The prefix should typically set up the context (beginning of methods/classes)
6. The golden_completion should provide the middle part
7. The suffix should close all open scopes and add assertions
8. Test the combined code mentally to verify it compiles and runs properly

Example of GOOD structure:
- Prefix: Defines namespace, class, method signature and first part of method body
- Golden completion: Middle part of the method implementation
- Suffix: Final part of method implementation + assertions + method closing + class closing + namespace closing

Example of BAD structure:
- Defining the same class in both prefix and suffix
- Not properly closing namespaces or classes
- Having overlapping code between golden_completion and suffix
- Having inconsistent indentation between the three parts

Requirements:
1. The scenario should demonstrate clear business purpose
2. The completion section should focus on domain-specific logic
3. The pattern should follow appropriate business rules and domain conventions
4. Ground truth should maintain semantic consistency
5. Assertions should verify business logic correctness
6. Include comments indicating expected business behavior and domain context

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-code-purpose-understanding", "language": "c_sharp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you verified that NO code exists outside of methods or classes?
9. Have you included all assertions DIRECTLY IN THE SUFFIX code?
10. Have you verified that assertions will pass when the code is executed?
11. Is the assertions field included with an empty string value ("assertions": "")?
12. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- NEVER place code at the global/namespace level - all code must be inside methods
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

LOW_CONTEXT_SYSTEM_PROMPT = """
You are an expert C# developer tasked with creating benchmark examples for testing low-context pattern matching capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to recognize and continue established patterns in code with minimal surrounding context.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C# that passes all assertions.

Key Responsibilities:
1. Generate diverse, practical low-context scenarios from these categories (rotate through them):
    - Data structure manipulation (arrays, Lists, Dictionaries, HashSets)
    - String processing and text manipulation
    - Object-oriented patterns (classes, inheritance, polymorphism)
    - Generic programming constructs (generics)
    - Error handling and exception patterns
    - Resource management patterns (using statements)
    - Iterator and collection patterns
    - Delegate and functional programming patterns
    - Algorithm implementation and .NET Collections usage
    - Async/await and Task-based patterns
    - Generic programming constructs (generics)
    - Error handling and exception patterns
    - Iterator and collection patterns
    - Delegate and functional programming patterns
2. Ensure patterns are clear and identifiable even with minimal context
3. Create ground truth completions that represent best practices while handling potential ambiguity
4. Write assertions that meaningfully test both pattern adherence and functionality across multiple valid completions where applicable
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C#
    - All assertions must pass when code is run
    - Include necessary using directives
    - Handle cleanup of resources
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
1. Focus on universal, standardized programming patterns
2. Test the model's ability to handle ambiguity and make reasonable assumptions
3. Ensure patterns follow widely-used conventions that are recognizable with minimal context
4. Include multiple valid completions in assertions where appropriate
5. Keep code minimal while still maintaining semantic clarity
6. The combined length of prefix and suffix should be 10-20 lines total for true low-context scenarios
"""

LOW_CONTEXT_USER_PROMPT = """
You are helping create a benchmark for low-context code pattern matching capabilities. Your task is to generate a coding scenario that tests an LLM's ability to recognize and
complete patterns in C# code with minimal surrounding context. The scenario should include:

Generate a single JSONL entry testing low-context capabilities. Choose from one of these categories (rotate through them):
- Data structure manipulation (arrays, Lists, Dictionaries, HashSets)
- String processing and text manipulation
- Object-oriented patterns (classes, inheritance, polymorphism)
- Generic programming constructs (generics)
- Error handling and exception patterns
- Resource management patterns (using statements)
- Iterator and collection patterns
- Delegate and functional programming patterns
- Algorithm implementation and .NET Collections usage
- Async/await and Task-based patterns
- Generic programming constructs (generics with complex constraints and variance)
- Error handling and exception patterns (beyond basic try/catch)
- Iterator and collection patterns (custom enumerators and specialized iterators)
- Delegate and functional programming patterns (higher-order functions, closures, currying)

STRICTLY PROHIBITED EXAMPLES - DO NOT GENERATE:
1. Basic list operations (adding items, summing, filtering simple conditions)
2. Simple string formatting or concatenation (like $"Hello, {name}!")
3. Basic lambda expressions (like (x, y) => x + y)
4. Trivial yield return sequences (like yield return 1, 2, 3)
5. Simple filtering operations (like returning even numbers)
6. Basic arithmetic operations or comparisons
7. Any example that could be solved by pattern matching without understanding

REQUIRED COMPLEXITY LEVEL:
Instead, you MUST create examples that demonstrate advanced C# patterns such as:

For Generic Programming:
- Covariance and contravariance with in/out type parameters
- Complex generic constraints (where T : class, IComparable<T>, new())
- Generic type inference with multiple type parameters
- Higher-kinded generics with nested type parameters
- Generic specialization patterns

For Error Handling:
- Exception filters with when clauses
- Custom exception hierarchies with specific catch blocks
- Using finally blocks with complex resource management
- Exception bubbling patterns with inner exceptions
- Fault-tolerant retry mechanisms

For Iterator Patterns:
- Custom IEnumerator<T> implementations
- Stateful iterators with complex yield logic
- Lazy evaluation patterns with deferred execution
- Paging or batching iterators
- Composite or nested iterator patterns

For Functional Programming:
- Function composition with higher-order functions
- Partial application and currying implementations
- Monadic patterns (Maybe/Option/Result types)
- Function memoization or caching
- Complex LINQ query expressions with multiple joins/groupings

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-low-context"  
- language: "c_sharp"
- prefix: The code that comes before the completion (may or may not establish the pattern)
- suffix: The code that follows the completion (may or may not establish the pattern) - should be DIFFERENT from the golden completion AND should include necessary assertions
- golden_completion: Multiple valid completions that maintain consistency with prefix/suffix and will pass all assertions
- LLM_justification: Explain why this is a good test case and the context behind it
- assertions: Leave this field as an empty string - all assertions should be integrated into the suffix code

CRITICAL COMPLEXITY VALIDATION:
Before submitting your example, verify that it meets these criteria:
1. Would this example challenge a senior C# developer?
2. Does it require understanding of advanced language features?
3. Is it significantly more complex than basic list operations or string formatting?
4. Does it demonstrate a pattern that would be found in production-quality code?
5. Would it be impossible to solve correctly through simple pattern matching?
6. Does it require genuine understanding of C# language semantics?

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
2. Include Debug.Assert statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same method/class as the code being tested
4. DO NOT create separate assertion methods or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

CRITICAL LOW CONTEXT REQUIREMENTS:
1. The prefix and suffix combined should be ONLY 10-20 lines total for true low-context scenarios
2. Focus on concise, universally recognizable patterns that can be understood with minimal context
3. Keep the context deliberately minimal while ensuring the pattern is still identifiable
4. Use clear but brief code that establishes a recognizable pattern
5. The pattern should be non-trivial but recognizable to C# developers

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Using Directive Requirements:
1. Do NOT include using directives unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included using directive must serve a clear purpose
3. Do not include "just in case" using directives that aren't used
4. All required using directives must appear in the prefix section
5. If a using directive is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include "using System.Diagnostics;" for Debug.Assert statements

Indentation requirements:
1. All code sections must maintain consistent indentation
2. If code is inside a method/class:
- The prefix should establish the correct indentation level
- The golden_completion must match the prefix's indentation
- The suffix must maintain the same indentation context
- Assertions should be at the appropriate scope level
3. Ensure proper indentation when exiting blocks
4. All code blocks must be properly closed

The golden completion should demonstrate understanding and correct usage of the low-context pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C# code
2. All assertions must pass when run
3. Include all necessary using directives
4. Mock external dependencies
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL NEWLINE HANDLING - READ CAREFULLY:
1. For proper JSON string escaping, represent newlines as "\\n" (backslash + n)
2. When writing this in the Python prompt, use "\\\\n" (double backslash + n)
3. Example of CORRECT newline escaping in the JSON output:
   "prefix": "using System;\nusing System.Collections.Generic;\n"
4. Example of CORRECT way to write this in the Python string:
   "prefix": "using System;\\nusing System.Collections.Generic;\\n"
5. NEVER use actual newline characters in your JSON string values
6. Ensure all code blocks are properly terminated and have consistent indentation

CODE FORMATTING REQUIREMENTS:
1. Make sure all C# code uses standard C# formatting conventions
2. Use consistent 4-space indentation throughout the code
3. Properly close all code blocks, methods, classes, and namespaces
4. All code must be syntactically valid C# when the prefix + golden_completion + suffix are combined
5. Test the combined code mentally to verify it will compile and run correctly

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of methods or classes
2. ALL code must be contained within proper C# scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within methods (such as Main, Test, or other methods)
5. ALWAYS ensure code is properly nested within appropriate class and method structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and methods are properly matched
9. DO NOT leave any code statements outside of method bodies
10. Place all assertions within appropriate methods (Main, Test, etc.)

CRITICAL ASSERTION PLACEMENT:
1. All Debug.Assert statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same method as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use Debug.Assert(condition, "message") format for all assertions
7. Make sure System.Diagnostics is imported for Debug.Assert statements

ADDITIONAL CRITICAL REQUIREMENTS:
1. When preparing your prefix, golden_completion, and suffix, ensure they can be combined into a valid C# program without syntax errors.
2. If your prefix defines a class or namespace:
   - The golden_completion must continue within that same class/namespace scope
   - The suffix must continue and properly close that same class/namespace scope
3. Avoid defining the same class or method in both prefix and suffix
4. Make sure all namespaces, classes, and methods are properly opened and closed across the combined code
5. The prefix should typically set up the context (beginning of methods/classes)
6. The golden_completion should provide the middle part
7. The suffix should close all open scopes and add assertions
8. Test the combined code mentally to verify it compiles and runs properly

Example of GOOD structure:
- Prefix: Defines namespace, class, method signature and first part of method body
- Golden completion: Middle part of the method implementation
- Suffix: Final part of method implementation + assertions + method closing + class closing + namespace closing

Example of BAD structure:
- Defining the same class in both prefix and suffix
- Not properly closing namespaces or classes
- Having overlapping code between golden_completion and suffix
- Having inconsistent indentation between the three parts

Requirements:
1. The scenario should demonstrate a clear pattern recognizable with minimal context
2. The completion section should focus on universal programming patterns
3. The pattern should follow widely-used conventions and standard library knowledge
4. Ground truth should acknowledge multiple valid completions where appropriate
5. Assertions should verify all acceptable pattern variations
6. Include comments indicating potential ambiguities and alternative completions

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-low-context", "language": "c_sharp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Have you used clear distinctions between golden_completion and suffix?
7. Have you verified that NO code exists outside of methods or classes?
8. Have you included all assertions DIRECTLY IN THE SUFFIX code?
9. Have you verified that assertions will pass when the code is executed?
10. Is the assertions field included with an empty string value ("assertions": "")?
11. Have you verified that ALL required fields are present in your JSON?
12. Have you verified your example is NOT one of the prohibited trivial examples?
13. Does your example meet ALL the complexity validation criteria?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- KEEP COMBINED PREFIX AND SUFFIX TO 10-20 LINES TOTAL
- NEVER place code at the global/namespace level - all code must be inside methods
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

PATTERN_MATCHING_SYSTEM_PROMPT = """
You are an expert C# developer tasked with creating benchmark examples for testing pattern matching capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to recognize and continue established patterns in code.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C# that passes all assertions.

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
    - Generic programming
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
    - All code must be fully executable C#
    - All assertions must pass when code is run
    - Include necessary using statements
    - Handle resource management properly
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
1. Focus on realistic, practical scenarios
2. Avoid patterns that are too project-specific
3. Ensure patterns are clear enough to be recognized by an LLM
4. Include edge cases in assertions where relevant
5. Keep code self-contained and independently verifiable
6. Leverage C#-specific features like LINQ, async/await, expression-bodied members, and pattern matching where appropriate
"""

PATTERN_MATCHING_USER_PROMPT = """
You are helping create a benchmark for code pattern matching capabilities. Your task is to generate a coding scenario that tests an LLM's ability to recognize and
complete patterns in C# code. The scenario should include:

Generate a single JSONL entry testing pattern matching capabilities. Choose ONE scenario from EACH list:
    Technical Pattern (choose ONE):
    - String/text manipulation
    - Functional programming 
    - Iterators/generators
    - Higher-order functions
    - Data structures
    - OOP patterns
    - Error handling
    - Memory management
    - Generic programming
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

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-pattern-matching"
- language: "c_sharp"
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
2. Include Debug.Assert statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same method/class as the code being tested
4. DO NOT create separate assertion methods or classes
5. Place assertions immediately after the code that should be tested
6. Never duplicate any golden_completion code in the suffix
7. The assertions must pass when the combined prefix + golden_completion + suffix is run

Critical Pattern Matching Requirements:
1. A CLEAR, IDENTIFIABLE PATTERN MUST be established in either the prefix or suffix
2. The golden_completion MUST follow this established pattern (not create a new one)
3. The pattern should be specific enough that random code wouldn't work
4. Include at least 2-3 examples of the pattern in the prefix to establish it
5. Ensure the pattern follows recognizable conventions in the chosen domain
6. The pattern should be evident to anyone familiar with C#

Critical Requirements for Avoiding Duplication:
1. The golden_completion field should ONLY contain the solution code that fills in the gap
2. The suffix must contain DIFFERENT code that follows after the completion
3. Do NOT repeat any golden_completion code in the suffix
4. The suffix field should NEVER duplicate the golden_completion code
5. There should be a clear DISTINCTION between what goes in golden_completion vs suffix
6. Ensure clear SEPARATION between completion and suffix content

Import Requirements:
1. Do NOT include using statements unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every included using statement must serve a clear purpose
3. Do not include "just in case" using statements that aren't used
4. All required using statements must appear in the prefix section
5. If a using statement is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include "using System.Diagnostics;" for Debug.Assert statements

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
1. Must be fully executable C# code
2. All assertions must pass when run
3. Include all necessary using statements
4. Mock external dependencies when needed
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL NEWLINE HANDLING - READ CAREFULLY:
1. For proper JSON string escaping, represent newlines as "\\n" (backslash + n)
2. When writing this in the Python prompt, use "\\\\n" (double backslash + n)
3. Example of CORRECT newline escaping in the JSON output:
   "prefix": "using System;\nusing System.Collections.Generic;\n"
4. Example of CORRECT way to write this in the Python string:
   "prefix": "using System;\\nusing System.Collections.Generic;\\n"
5. NEVER use actual newline characters in your JSON string values
6. Ensure all code blocks are properly terminated and have consistent indentation

CODE FORMATTING REQUIREMENTS:
1. Make sure all C# code uses standard C# formatting conventions
2. Use consistent 4-space indentation throughout the code
3. Properly close all code blocks, methods, classes, and namespaces
4. All code must be syntactically valid C# when the prefix + golden_completion + suffix are combined
5. Test the combined code mentally to verify it will compile and run correctly

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of methods or classes
2. ALL code must be contained within proper C# scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within methods (such as Main, Test, or other methods)
5. ALWAYS ensure code is properly nested within appropriate class and method structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and methods are properly matched
9. DO NOT leave any code statements outside of method bodies
10. Place all assertions within appropriate methods (Main, Test, etc.)

CRITICAL ASSERTION PLACEMENT:
1. All Debug.Assert statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same method as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use Debug.Assert(condition, "message") format for all assertions
7. Make sure System.Diagnostics is imported for Debug.Assert statements

ADDITIONAL CRITICAL REQUIREMENTS:
1. When preparing your prefix, golden_completion, and suffix, ensure they can be combined into a valid C# program without syntax errors.
2. If your prefix defines a class or namespace:
   - The golden_completion must continue within that same class/namespace scope
   - The suffix must continue and properly close that same class/namespace scope
3. Avoid defining the same class or method in both prefix and suffix
4. Make sure all namespaces, classes, and methods are properly opened and closed across the combined code
5. The prefix should typically set up the context (beginning of methods/classes)
6. The golden_completion should provide the middle part
7. The suffix should close all open scopes and add assertions
8. Test the combined code mentally to verify it compiles and runs properly

Example of GOOD structure:
- Prefix: Defines namespace, class, method signature and first part of method body
- Golden completion: Middle part of the method implementation
- Suffix: Final part of method implementation + assertions + method closing + class closing + namespace closing

Example of BAD structure:
- Defining the same class in both prefix and suffix
- Not properly closing namespaces or classes
- Having overlapping code between golden_completion and suffix
- Having inconsistent indentation between the three parts

Requirements:
1. The scenario MUST demonstrate a clear, identifiable pattern
2. The completion section should be non-trivial but focused on pattern matching
3. The pattern should follow C# best practices and common conventions
4. Ground truth should demonstrate the ideal pattern continuation
5. Assertions should verify both pattern adherence and functionality
6. Include comments indicating the expected pattern continuation

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-pattern-matching", "language": "c_sharp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": "..."}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you verified that NO code exists outside of methods or classes?
9. Have you included all assertions DIRECTLY IN THE SUFFIX code?
10. Have you verified that assertions will pass when the code is executed?
11. Is the assertions field included with an empty string value ("assertions": "")?
12. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/catch blocks if needed
- Maintain correct execution order
- NEVER place code at the global/namespace level - all code must be inside methods
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field
- ENSURE A CLEAR PATTERN IS ESTABLISHED that the golden completion must follow

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""

API_USAGE_SYSTEM_PROMPT = """
You are an expert C# developer tasked with creating benchmark examples for testing rare API usage and uncommon library function capabilities in large language models.
Your role is to generate high-quality, realistic coding scenarios that effectively test an LLM's ability to recognize and continue established patterns in code involving uncommon APIs and library functions.

Your output should be a single JSON object formatted as a JSONL entry. The code must be fully executable C# that compiles and runs correctly.

Key Responsibilities:
1. Generate diverse examples from these API categories (rotate through them, don't focus only on file operations or network protocols):
    - Machine learning libraries (ML.NET, TensorFlow.NET, CNTK)
    - .NET Core libraries (System.Text.Json, System.Threading.Channels)
    - Semantic Kernel and AI integration (.NET SDK for OpenAI)
    - Web API integration (GitHub, Twitter, Slack, Discord)
    - Cloud services (Azure, AWS SDK, GCP, Firebase)
    - Azure services (Azure Cosmos DB, Azure Functions, Azure App Service)
    - Database interfaces (Entity Framework Core, Dapper, MongoDB, Redis)
    - File formats and parsing (XML, JSON, CSV, YAML)
    - Web frameworks (ASP.NET Core, Blazor, Minimal APIs, Aspire)
    - Network protocols (gRPC, SignalR, WebSockets)
    - UI frameworks (WPF, WinUI, MAUI, Xamarin, Avalonia)
    - Scientific computing (.NET Numerics, Math.NET)
    - Security/cryptography APIs
    - Debugging/profiling tools
    - Text processing (advanced regex, encoding)
    - Concurrent programming (TPL, Parallel LINQ, Channels)
    - Cross-platform development (Xamarin to MAUI migration)
    - Legacy/deprecated APIs

2. Ensure patterns are clear and identifiable even with uncommon or deprecated APIs
3. Create ground truth completions that represent best practices while handling API versioning
4. Write assertions that meaningfully test both API correctness and parameter ordering
5. Provide clear justification for why the example makes a good test case
6. Ensure code quality:
    - All code must be fully executable C#
    - All assertions must pass when code is run
    - Include necessary using directives
    - Handle cleanup of resources with proper disposal
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
complete patterns in C# code involving uncommon or deprecated APIs.

Generate a single JSONL entry testing rare API usage capabilities. Choose from one of these categories (rotate through them, don't focus only on file operations or network protocols):
    - Machine learning libraries (ML.NET, TensorFlow.NET, CNTK)
    - .NET Core libraries (System.Text.Json, System.Threading.Channels)
    - Semantic Kernel and AI integration (.NET SDK for OpenAI)
    - Web API integration (GitHub, Twitter, Slack, Discord)
    - Cloud services (Azure, AWS SDK, GCP, Firebase)
    - Azure services (Azure Cosmos DB, Azure Functions, Azure App Service)
    - Database interfaces (Entity Framework Core, Dapper, MongoDB, Redis)
    - File formats and parsing (XML, JSON, CSV, YAML)
    - Web frameworks (ASP.NET Core, Blazor, Minimal APIs, Aspire)
    - Network protocols (gRPC, SignalR, WebSockets)
    - UI frameworks (WPF, WinUI, MAUI, Xamarin, Avalonia)
    - Scientific computing (.NET Numerics, Math.NET)
    - Security/cryptography APIs
    - Debugging/profiling tools
    - Text processing (advanced regex, encoding)
    - Concurrent programming (TPL, Parallel LINQ, Channels)
    - Cross-platform development (Xamarin to MAUI migration)
    - Legacy/deprecated APIs

Required JSON fields:
- id: A unique numeric identifier
- testsource: Use "devbench-api-usage"  
- language: "c_sharp"
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
2. Include Debug.Assert statements DIRECTLY IN THE SUFFIX at the appropriate places
3. All assertions must be placed in the same method/class as the code being tested
4. DO NOT create separate assertion methods or classes
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

Using Directive Requirements:
1. Do NOT include using directives unless they are ACTUALLY USED in at least one of:
   - prefix
   - suffix (including assertions)
   - golden_completion
2. Every using directive must serve a clear purpose
3. Do not include "just in case" directives that aren't used
4. All required using directives must appear in the prefix section
5. If a using directive is only needed for the golden_completion, it must still appear in the prefix
6. Make sure to include "using System.Diagnostics;" for Debug.Assert statements

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
3. Ensure proper dedenting when exiting blocks
4. All code blocks must be properly closed

The API pattern can be established either in the prefix or suffix code.
The golden completion should demonstrate understanding and correct usage of the API pattern regardless of where it is established.

Code requirements:
1. Must be fully executable C# code
2. All assertions must pass when run
3. Include all necessary using directives
4. Mock external dependencies
5. Clean up resources properly
6. Handle errors appropriately
7. Assertions must be placed BEFORE cleanup code
8. Resource cleanup must be in the suffix AFTER all assertions
9. All assertions must complete before any cleanup occurs

CRITICAL NEWLINE HANDLING - READ CAREFULLY:
1. For proper JSON string escaping, represent newlines as "\\n" (backslash + n)
2. When writing this in the Python prompt, use "\\\\n" (double backslash + n)
3. Example of CORRECT newline escaping in the JSON output:
   "prefix": "using System;\nusing System.Collections.Generic;\n"
4. Example of CORRECT way to write this in the Python string:
   "prefix": "using System;\\nusing System.Collections.Generic;\\n"
5. NEVER use actual newline characters in your JSON string values
6. Ensure all code blocks are properly terminated and have consistent indentation

CODE FORMATTING REQUIREMENTS:
1. Make sure all C# code uses standard C# formatting conventions
2. Use consistent 4-space indentation throughout the code
3. Properly close all code blocks, methods, classes, and namespaces
4. All code must be syntactically valid C# when the prefix + golden_completion + suffix are combined
5. Test the combined code mentally to verify it will compile and run correctly

CRITICAL CODE STRUCTURE REQUIREMENTS:
1. NEVER place code outside of methods or classes
2. ALL code must be contained within proper C# scope boundaries
3. DO NOT place assertions or standalone code statements at the global/namespace level
4. ALL assertions must be contained within methods (such as Main, Test, or other methods)
5. ALWAYS ensure code is properly nested within appropriate class and method structures
6. NEVER generate code that would compile as a partial class
7. NEVER duplicate class definitions - each class must be defined only once
8. Verify that the beginning and end of classes and methods are properly matched
9. DO NOT leave any code statements outside of method bodies
10. Place all assertions within appropriate methods (Main, Test, etc.)

CRITICAL ASSERTION PLACEMENT:
1. All Debug.Assert statements must be placed DIRECTLY IN THE SUFFIX code
2. Assertions should be placed immediately after the code that needs to be verified
3. Assertions must be within the same method as the code being tested
4. Assertions must be executed BEFORE any cleanup code
5. Assertions must be properly indented to match the surrounding code structure
6. Use Debug.Assert(condition, "message") format for all assertions
7. Make sure System.Diagnostics is imported for Debug.Assert statements

ADDITIONAL CRITICAL REQUIREMENTS:
1. When preparing your prefix, golden_completion, and suffix, ensure they can be combined into a valid C# program without syntax errors.
2. If your prefix defines a class or namespace:
   - The golden_completion must continue within that same class/namespace scope
   - The suffix must continue and properly close that same class/namespace scope
3. Avoid defining the same class or method in both prefix and suffix
4. Make sure all namespaces, classes, and methods are properly opened and closed across the combined code
5. The prefix should typically set up the context (beginning of methods/classes)
6. The golden_completion should provide the middle part
7. The suffix should close all open scopes and add assertions
8. Test the combined code mentally to verify it compiles and runs properly

Example of GOOD structure:
- Prefix: Defines namespace, class, method signature and first part of method body
- Golden completion: Middle part of the method implementation
- Suffix: Final part of method implementation + assertions + method closing + class closing + namespace closing

Example of BAD structure:
- Defining the same class in both prefix and suffix
- Not properly closing namespaces or classes
- Having overlapping code between golden_completion and suffix
- Having inconsistent indentation between the three parts

Requirements:
1. The scenario should demonstrate a clear pattern recognizable with the given context
2. The completion section should focus on rare library functions
3. The pattern should follow correct API conventions across different versions
4. Ground truth should demonstrate proper parameter ordering
5. Assertions should verify API behavior and parameter correctness
6. Include comments indicating API version compatibility and parameter requirements

Format your response as a single line JSON object with newlines escaped appropriately.

Example format:
{"id": "1", "testsource": "devbench-api-usage", "language": "c_sharp", "prefix": "...", "suffix": "...", "golden_completion": "...", "LLM_justification": "...", "assertions": ""}

VALIDATION CHECKLIST BEFORE SUBMITTING:
1. Have you properly escaped ALL special characters?
2. Is your entire response a single, valid JSON object?
3. Are all string values properly quoted and terminated?
4. Have you verified there are no unescaped newlines in your strings?
5. Have you checked for balanced quotes and braces?
6. Is your prefix at least 50-60 lines of code?
7. Have you used clear distinctions between golden_completion and suffix?
8. Have you verified that NO code exists outside of methods or classes?
9. Have you included all assertions DIRECTLY IN THE SUFFIX code?
10. Have you verified that assertions will pass when the code is executed?
11. Is the assertions field included with an empty string value ("assertions": "")?
12. Have you verified that ALL required fields are present in your JSON?

Important:
- Never place cleanup code before assertions
- Keep all verification code before any cleanup
- Ensure resources exist when assertions run
- Use proper try/finally blocks if needed
- Maintain correct execution order
- NEVER place code at the global/namespace level - all code must be inside methods
- ALL ASSERTIONS SHOULD BE IN THE SUFFIX, not in a separate assertions field

Ensure the example is self-contained and can be evaluated independently. All assertions must pass when run.
Use proper escaping for newlines/quotes and maintain indentation in the escaped strings.

"""