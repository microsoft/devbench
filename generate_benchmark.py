import os
import base64
from openai import AzureOpenAI  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import dotenv
from typing import Dict, List, Tuple, Set
import re
import ast
import subprocess
import sys
import importlib
import pkg_resources
from prompts import python_prompts, javascript_prompts, c_sharp_prompts, cpp_prompts, typescript_prompts, java_prompts
from tree_sitter_languages import get_parser
import json
import argparse
import time
import math

def comb(n, k):
    """Calculate binomial coefficient n choose k"""
    if k > n or k < 0:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)  # Take advantage of symmetry
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result

dotenv.load_dotenv()

def execute_test_cases(jsonl_files: List[str], language="python", verbose=True, report_file=None) -> Dict:
    """
    Execute test cases from the benchmark JSONL files for any supported language.
    
    Args:
        jsonl_files: List of JSONL file paths to process
        language: Programming language of the test cases (default: python)
        verbose: Whether to print detailed information during execution
        report_file: Path to file for saving detailed test results
        
    Returns:
        Dict: Summary of execution results
    """
    results = {
        "total_cases": 0,
        "successful_cases": 0,
        "failed_cases": 0,
        "failures": []
    }
    
    # Open report file if specified
    report_fp = None
    if report_file:
        try:
            report_fp = open(report_file, 'w', encoding='utf-8')
            report_fp.write(f"{language.upper()} BENCHMARK TEST RESULTS\n")
            report_fp.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"Error opening report file: {e}")
            report_fp = None
    
    try:
        for jsonl_file in jsonl_files:
            if verbose:
                print(f"\nProcessing {jsonl_file}...")
            
            if report_fp:
                report_fp.write(f"\nFILE: {jsonl_file}\n")
                report_fp.write("-" * 80 + "\n")
            
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        try:
                            test_case = json.loads(line)
                            results["total_cases"] += 1
                            
                            # Debug test case details
                            if verbose:
                                print(f"Running test case #{i} (ID: {test_case['id']})...")
                            
                            # Get test case components
                            prefix = test_case["prefix"]
                            golden_completion = test_case["golden_completion"]
                            suffix = test_case["suffix"]
                            assertions = test_case.get("assertions", "")
                            
                            # Write test case info to report
                            if report_fp:
                                report_fp.write(f"\nTEST CASE #{i} (ID: {test_case['id']})\n")
                                report_fp.write(f"  Source: {test_case.get('testsource', 'Unknown')}\n\n")
                            
                            # Execute the test case with language-specific function
                            if language.lower() == "java":
                                success, error_msg = run_java_test_case(
                                    prefix, golden_completion, suffix, assertions, verbose
                                )
                            elif language.lower() == "javascript":
                                success, error_msg = run_javascript_test_case(
                                    prefix, golden_completion, suffix, assertions, verbose
                                )
                            elif language.lower() == "typescript":
                                success, error_msg = run_typescript_test_case(
                                    prefix, golden_completion, suffix, assertions, verbose
                                )
                            elif language.lower() == "c_sharp" or language.lower() == "csharp" or language.lower() == "c#":
                                success, error_msg = run_csharp_test_case(
                                    prefix, golden_completion, suffix, assertions, verbose
                                )
                            elif language.lower() == "cpp" or language.lower() == "c++":
                                success, error_msg = run_cpp_test_case(
                                    prefix, golden_completion, suffix, assertions, verbose
                                )
                            else:  # Default to Python for other languages
                                success, error_msg = run_python_test_case(
                                    prefix, golden_completion, suffix, assertions, verbose
                                )
                            
                            if success:
                                results["successful_cases"] += 1
                                if verbose:
                                    print(f"Test case #{i} (ID: {test_case['id']}) passed ✓")
                                if report_fp:
                                    report_fp.write("  RESULT: PASS\n\n")
                            else:
                                results["failed_cases"] += 1
                                results["failures"].append({
                                    "file": jsonl_file,
                                    "test_id": test_case['id'],
                                    "error": error_msg
                                })
                                if verbose:
                                    print(f"Test case #{i} (ID: {test_case['id']}) failed")
                                    print(f"  Error: {error_msg}")
                                if report_fp:
                                    report_fp.write("  RESULT: FAIL\n")
                                    report_fp.write(f"  ERROR: {error_msg}\n\n")
                                    
                                    # Include the test case code in the report for debugging
                                    report_fp.write("  PREFIX CODE:\n")
                                    report_fp.write("  " + prefix.replace("\n", "\n  ") + "\n\n")
                                    report_fp.write("  GOLDEN COMPLETION:\n")
                                    report_fp.write("  " + golden_completion.replace("\n", "\n  ") + "\n\n")
                                    report_fp.write("  SUFFIX CODE:\n")
                                    report_fp.write("  " + suffix.replace("\n", "\n  ") + "\n\n")
                                    report_fp.write("  ASSERTIONS:\n")
                                    report_fp.write("  " + assertions.replace("\n", "\n  ") + "\n\n")
                        
                        except Exception as e:
                            results["failed_cases"] += 1
                            results["failures"].append({
                                "file": jsonl_file,
                                "test_id": f"{i}",
                                "error": str(e)
                            })
                            if verbose:
                                print(f"Error processing test case #{i}: {str(e)}")
                            if report_fp:
                                report_fp.write(f"\nTEST CASE #{i}\n")
                                report_fp.write("  RESULT: ERROR\n")
                                report_fp.write(f"  ERROR: {str(e)}\n\n")
            except Exception as e:
                print(f"Error processing file {jsonl_file}: {str(e)}")
                if report_fp:
                    report_fp.write(f"\nERROR processing file: {str(e)}\n\n")
    
    finally:
        # Write summary to report file
        if report_fp:
            try:
                report_fp.write("\n" + "="*80 + "\n")
                report_fp.write("EXECUTION SUMMARY\n")
                report_fp.write("="*80 + "\n")
                report_fp.write(f"Total test cases: {results['total_cases']}\n")
                report_fp.write(f"Successful test cases: {results['successful_cases']}\n")
                report_fp.write(f"Failed test cases: {results['failed_cases']}\n\n")
                
                if results["failures"]:
                    report_fp.write("Failed test cases:\n")
                    for i, failure in enumerate(results["failures"], 1):
                        report_fp.write(f"  {i}. {failure['file']} - Test ID: {failure['test_id']}\n")
                        report_fp.write(f"     Error: {failure['error']}\n\n")
            except Exception as e:
                print(f"Error writing summary to report file: {e}")
            
            # Close report file
            try:
                report_fp.close()
                if verbose:
                    print(f"\nDetailed test results saved to {report_file}")
            except Exception as e:
                print(f"Error closing report file: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"Total test cases: {results['total_cases']}")
    print(f"Successful test cases: {results['successful_cases']}")
    print(f"Failed test cases: {results['failed_cases']}")
    
    if results["failures"]:
        print("\nFailed test cases:")
        for i, failure in enumerate(results["failures"][:10], 1):  # Show first 10 failures
            print(f"  {i}. {failure['file']} - Test ID: {failure['test_id']}")
            print(f"     Error: {failure['error']}")
        
        if len(results["failures"]) > 10:
            print(f"  ... and {len(results['failures']) - 10} more failures")
    
    return results

def run_python_test_case(prefix: str, golden_completion: str, suffix: str, 
                         assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a Python test case by creating a temporary file and executing it.
    
    Args:
        prefix: Prefix code
        golden_completion: Golden completion code
        suffix: Suffix code
        assertions: Assertion code
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    import uuid
    import random
    
    # Generate unique identifiers to avoid race conditions
    unique_id = str(uuid.uuid4())[:8]
    
    # Add matplotlib non-interactive mode to prevent plt.show() from blocking
    matplotlib_header = f"""
# Added automatically to prevent matplotlib from blocking
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
# Override plt.show to prevent blocking
original_show = plt.show
def non_blocking_show(*args, **kwargs):
    plt.savefig('temp_plot_{unique_id}.png')  # Use unique filename
    plt.close()
plt.show = non_blocking_show
"""
    
    # Add code to load API keys from environment
    env_vars_header = """
# Added automatically to provide access to environment variables
import os

# Configure more robust HTTP client settings to reduce timeouts
import asyncio
try:
    # Increase default timeouts for HTTP operations
    import tornado.httpclient
    original_fetch = tornado.httpclient.AsyncHTTPClient.fetch
    async def robust_fetch(self, request, *args, **kwargs):
        # Add timeout and retry logic
        if isinstance(request, str):
            request = tornado.httpclient.HTTPRequest(request, connect_timeout=10, request_timeout=20)
        elif hasattr(request, 'connect_timeout'):
            request.connect_timeout = max(request.connect_timeout or 0, 10)
            request.request_timeout = max(request.request_timeout or 0, 20)
        return await original_fetch(self, request, *args, **kwargs)
    tornado.httpclient.AsyncHTTPClient.fetch = robust_fetch
except:
    pass  # Ignore if tornado is not available
"""

    # Environment variables are inherited from the parent process
    # No need to manually inject them
    
    # Combine all code sections
    combined_code = f"""{matplotlib_header}
{env_vars_header}

{prefix}
{golden_completion}
{suffix}

# Run assertions
{assertions}
"""
    
    # Create a temporary python file to execute with unique name
    temp_file = f"temp_test_execution_{unique_id}.py"
    try:
        # Add a small random delay to reduce race conditions on network requests
        time.sleep(random.uniform(0.1, 0.5))
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Run the code with the current environment variables and a timeout
        try:
            process = subprocess.run(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=os.environ.copy(),  # Pass the current environment variables to the subprocess
                timeout=timeout  # Add timeout parameter
            )
            
            if process.returncode != 0:
                error = process.stderr.strip()
                # Check if it's an import error
                if "ImportError" in error or "ModuleNotFoundError" in error:
                    # Extract the missing module name
                    match = re.search(r"No module named '([^']+)'", error)
                    if match:
                        module_name = match.group(1).split('.')[0]
                        if verbose:
                            print(f"  Missing dependency: {module_name}, attempting to install...")
                        
                        # Try to install the module
                        install_process = subprocess.run(
                            [sys.executable, "-m", "pip", "install", module_name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False
                        )
                        
                        if install_process.returncode == 0:
                            if verbose:
                                print(f"  Successfully installed {module_name}, retrying test case...")
                            
                            # Retry running the test
                            return run_python_test_case(prefix, golden_completion, suffix, assertions, verbose, timeout)
                        else:
                            return False, f"Failed to install dependency {module_name}: {install_process.stderr.strip()}"
                
                return False, f"Execution failed: {error}"
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            # Handle timeout case
            if verbose:
                print(f"  Test case execution timed out after {timeout} seconds")
            return False, f"Execution timed out after {timeout} seconds"
            
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        # Clean up temporary files - with retry logic for Windows
        for attempt in range(5):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                break
            except PermissionError:
                # If file is still in use, wait briefly and retry
                time.sleep(0.5)
                if attempt == 4:  # Last attempt
                    print(f"Warning: Could not remove temporary file {temp_file}")
                    
        # Clean up unique plot file
        plot_file = f'temp_plot_{unique_id}.png'
        if os.path.exists(plot_file):
            try:
                os.remove(plot_file)
            except:
                print(f"Warning: Could not remove temporary plot file {plot_file}")

def run_java_test_case_simple(prefix: str, golden_completion: str, suffix: str, 
                       assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a Java test case by creating a temporary file, compiling with javac, and executing.
    
    Args:
        prefix: Prefix code (before the completion)
        golden_completion: Golden completion code 
        suffix: Suffix code (after the completion)
        assertions: Assertion code (currently unused, handled in suffix)
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    import uuid
    import tempfile
    import shutil
    
    # Generate unique identifier to avoid race conditions
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"java_test_{unique_id}_")
    
    try:
        # Combine all code sections with proper newlines to avoid concatenation issues
        # Add newlines if not already present to ensure proper code separation
        prefix_clean = prefix.rstrip()
        suffix_clean = suffix.lstrip()
        
        # If golden_completion doesn't start with newline and prefix doesn't end with one, add it
        if not prefix.endswith('\n') and not golden_completion.startswith('\n'):
            combined_code = f"{prefix_clean}\n{golden_completion}{suffix_clean}"
        else:
            combined_code = f"{prefix}{golden_completion}{suffix}"
        
        # Extract class name from the code to determine filename
        class_name = "TestCase"  # Default fallback
        import re
        class_match = re.search(r'public\s+class\s+(\w+)', combined_code)
        if class_match:
            class_name = class_match.group(1)
        
        # Create Java source file
        java_file = os.path.join(temp_dir, f"{class_name}.java")
        
        if verbose:
            print(f"  Creating Java file: {java_file}")
            print(f"  Class name: {class_name}")
        
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Enable assertions for execution (-ea flag)
        compile_command = ["javac", java_file]
        run_command = ["java", "-ea", "-cp", temp_dir, class_name]
        
        if verbose:
            print(f"  Compile command: {' '.join(compile_command)}")
            print(f"  Run command: {' '.join(run_command)}")
        
        try:
            # Compile the Java file
            compile_process = subprocess.run(
                compile_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout
            )
            
            if compile_process.returncode != 0:
                compile_error = compile_process.stderr.strip()
                if verbose:
                    print(f"  Compilation failed: {compile_error}")
                return False, f"Compilation failed: {compile_error}"
            
            if verbose:
                print("  Compilation successful, running test...")
            
            # Run the compiled Java program
            run_process = subprocess.run(
                run_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout
            )
            
            if run_process.returncode != 0:
                runtime_error = run_process.stderr.strip()
                if verbose:
                    print(f"  Runtime error: {runtime_error}")
                # Check if it's an assertion error
                if "AssertionError" in runtime_error:
                    return False, f"Assertion failed: {runtime_error}"
                else:
                    return False, f"Runtime error: {runtime_error}"
            
            if verbose:
                output = run_process.stdout.strip()
                if output:
                    print(f"  Program output: {output}")
                print("  Test completed successfully")
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  Test execution timed out after {timeout} seconds")
            return False, f"Execution timed out after {timeout} seconds"
            
    except Exception as e:
        if verbose:
            print(f"  Unexpected error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"
    
    finally:
        # Clean up temporary directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")

def run_java_test_case_gradle(prefix: str, golden_completion: str, suffix: str, 
                             assertions: str = "", verbose=True, timeout=60) -> Tuple[bool, str]:
    """
    Run a Java test case using Gradle for complex cases with dependencies and packages.
    Uses Gradle to build/compile with dependencies, then runs the main method directly.
    """
    import uuid
    import tempfile
    import shutil
    import re
    
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"java_gradle_test_{unique_id}_")
    
    try:
        # Combine code sections
        prefix_clean = prefix.rstrip()
        suffix_clean = suffix.lstrip()
        
        if not prefix.endswith('\n') and not golden_completion.startswith('\n'):
            combined_code = f"{prefix_clean}\n{golden_completion}{suffix_clean}"
        else:
            combined_code = f"{prefix}{golden_completion}{suffix}"
        
        # Extract package and class name
        package_match = re.search(r'^\s*package\s+([\w.]+);', combined_code, re.MULTILINE)
        package_name = package_match.group(1) if package_match else "devbench.test"
        
        class_match = re.search(r'public\s+class\s+(\w+)', combined_code)
        class_name = class_match.group(1) if class_match else "TestCase"
        
        # If no package declaration, add one
        if not package_match:
            combined_code = f"package {package_name};\n\n{combined_code}"
        
        # Create Gradle directory structure - use src/main/java instead of src/test/java
        src_dir = os.path.join(temp_dir, "src", "main", "java", *package_name.split('.'))
        os.makedirs(src_dir, exist_ok=True)
        
        # Write Java file
        java_file = os.path.join(src_dir, f"{class_name}.java")
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Common dependencies for Java benchmarks
        dependencies = []
        
        # Check for specific libraries in imports
        if 'org.apache.commons' in combined_code:
            dependencies.append("implementation 'org.apache.commons:commons-lang3:3.12.0'")
            # Also add Commons IO if needed
            if 'org.apache.commons.io' in combined_code:
                dependencies.append("implementation 'commons-io:commons-io:2.11.0'")
            # Also add Commons DBCP2 if needed
            if 'org.apache.commons.dbcp2' in combined_code:
                dependencies.append("implementation 'org.apache.commons:commons-dbcp2:2.9.0'")
                dependencies.append("implementation 'com.h2database:h2:2.1.214'")  # H2 database for testing
            # Also add Commons DBCP (older version) if needed
            if 'org.apache.commons.dbcp' in combined_code:
                dependencies.append("implementation 'commons-dbcp:commons-dbcp:1.4'")
                dependencies.append("implementation 'com.h2database:h2:2.1.214'")  # H2 database for testing
            # Also add Commons Compress if needed
            if 'org.apache.commons.compress' in combined_code:
                dependencies.append("implementation 'org.apache.commons:commons-compress:1.21'")            
        if 'org.junit' in combined_code:
            dependencies.append("implementation 'junit:junit:4.13.2'")
        if 'com.fasterxml.jackson' in combined_code:
            dependencies.append("implementation 'com.fasterxml.jackson.core:jackson-core:2.15.2'")
            dependencies.append("implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'")
            dependencies.append("implementation 'com.fasterxml.jackson.core:jackson-annotations:2.15.2'")
        if 'com.google.common' in combined_code:
            dependencies.append("implementation 'com.google.guava:guava:31.1-jre'")
        if 'org.json' in combined_code:
            dependencies.append("implementation 'org.json:json:20210307'")
        if 'javax.xml.bind' in combined_code or 'jakarta.xml.bind' in combined_code:
            # Use widely compatible JAXB implementation
            dependencies.append("implementation 'javax.xml.bind:jaxb-api:2.3.1'")
            dependencies.append("implementation 'com.sun.xml.bind:jaxb-core:2.3.0.1'")
            dependencies.append("implementation 'com.sun.xml.bind:jaxb-impl:2.3.1'")
            dependencies.append("implementation 'javax.activation:activation:1.1.1'")
        if 'org.hibernate' in combined_code:
            dependencies.append("implementation 'org.hibernate:hibernate-core:5.6.15.Final'")
            dependencies.append("implementation 'com.h2database:h2:2.1.214'")  # H2 database for testing
        if 'org.jdom2' in combined_code:
            dependencies.append("implementation 'org.jdom:jdom2:2.0.6'")
        if 'org.apache.poi' in combined_code:
            dependencies.append("implementation 'org.apache.poi:poi:5.2.3'")
            dependencies.append("implementation 'org.apache.poi:poi-ooxml:5.2.3'")
        if 'com.google.gson' in combined_code:
            dependencies.append("implementation 'com.google.code.gson:gson:2.10.1'")
        if 'org.dom4j' in combined_code:
            dependencies.append("implementation 'org.dom4j:dom4j:2.1.4'")
        if 'org.apache.logging.log4j' in combined_code:
            dependencies.append("implementation 'org.apache.logging.log4j:log4j-core:2.20.0'")
            dependencies.append("implementation 'org.apache.logging.log4j:log4j-api:2.20.0'")
        if 'org.springframework' in combined_code:
            dependencies.append("implementation 'org.springframework:spring-context:5.3.23'")
            dependencies.append("implementation 'org.springframework:spring-core:5.3.23'")
            dependencies.append("implementation 'org.springframework:spring-beans:5.3.23'")
        
        # Create build.gradle - simplified without test configuration
        build_gradle_content = f"""
plugins {{
    id 'java'
    id 'application'
}}

repositories {{
    mavenCentral()
}}

dependencies {{
    {chr(10).join('    ' + dep for dep in dependencies)}
}}

java {{
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}}

application {{
    mainClass = '{package_name}.{class_name}'
}}
"""
        
        with open(os.path.join(temp_dir, "build.gradle"), 'w') as f:
            f.write(build_gradle_content)
        
        if verbose:
            print(f"  Using Gradle for dependencies")
            print(f"  Package: {package_name}")
            print(f"  Class: {class_name}")
            print(f"  Dependencies: {len(dependencies)}")
        
        # Step 1: Build with Gradle to compile and resolve dependencies
        build_cmd = ['gradle', 'build', '--no-daemon', '--console=plain']
        if verbose:
            print(f"  Building: {' '.join(build_cmd)}")
        
        build_result = subprocess.run(
            build_cmd,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if build_result.returncode != 0:
            error_output = build_result.stdout + build_result.stderr
            if "cannot find symbol" in error_output or "package does not exist" in error_output:
                return False, f"Compilation failed: {error_output[-300:]}"
            else:
                return False, f"Gradle build failed: {error_output[-200:]}"
        
        # Step 2: Get the classpath from Gradle
        classpath_cmd = ['gradle', 'printClasspath', '--no-daemon', '--console=plain']
        
        # Add a task to print classpath to build.gradle
        with open(os.path.join(temp_dir, "build.gradle"), 'a') as f:
            f.write("""

task printClasspath {
    doLast {
        println configurations.runtimeClasspath.asPath
    }
}
""")
        
        classpath_result = subprocess.run(
            classpath_cmd,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Extract classpath from output (last line that looks like a classpath)
        classpath = ""
        if classpath_result.returncode == 0:
            lines = classpath_result.stdout.strip().split('\n')
            for line in reversed(lines):
                if '.jar' in line and ('/' in line or '\\' in line):
                    classpath = line.strip()
                    break
        
        # Add build output directory to classpath
        build_classes_dir = os.path.join(temp_dir, "build", "classes", "java", "main")
        if classpath:
            full_classpath = f"{build_classes_dir}{os.pathsep}{classpath}"
        else:
            full_classpath = build_classes_dir
        
        # Step 3: Run the Java class directly with assertions enabled
        java_cmd = ['java', '-ea', '-cp', full_classpath, f'{package_name}.{class_name}']
        
        if verbose:
            print(f"  Running: {' '.join(java_cmd[:4])} [classpath] {java_cmd[-1]}")
        
        run_result = subprocess.run(
            java_cmd,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if verbose and run_result.stdout:
            print(f"  Program output: {run_result.stdout.strip()}")
        
        if run_result.returncode == 0:
            if verbose:
                print("  Gradle test completed successfully")
            return True, ""
        else:
            error_output = run_result.stdout + run_result.stderr
            
            # Check for common error patterns
            if "AssertionError" in error_output:
                return False, f"Assertion failed: {error_output.strip()}"
            elif "Exception" in error_output:
                return False, f"Runtime exception: {error_output.strip()}"
            else:
                return False, f"Program failed: {error_output.strip()}"
                
    except subprocess.TimeoutExpired:
        return False, f"Gradle execution timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Gradle error: {str(e)}"
    finally:
        # Clean up
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up Gradle temp directory")
        except Exception as e:
            print(f"Warning: Could not remove Gradle temp directory {temp_dir}: {str(e)}")

def run_javascript_test_case(prefix: str, golden_completion: str, suffix: str, 
                             assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a JavaScript test case by creating a temporary file and executing it with Node.js.
    
    Args:
        prefix: Prefix code
        golden_completion: Golden completion code
        suffix: Suffix code
        assertions: Assertion code
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    import uuid
    import random
    import tempfile
    import shutil
    import re
    
    # Generate unique identifiers to avoid race conditions
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"js_test_{unique_id}_")
    
    try:
        # Combine all code sections
        # Environment variables are inherited from parent process
        combined_code = f"""{prefix}
{golden_completion}
{suffix}

// Run assertions
{assertions}
"""
        
        # Create a temporary JavaScript file
        js_file = os.path.join(temp_dir, f"test_{unique_id}.js")
        
        if verbose:
            print(f"  Creating JavaScript file: {js_file}")
        
        # Add a small random delay to reduce race conditions on network requests
        time.sleep(random.uniform(0.1, 0.3))
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Ensure we get the same PATH as your shell by prioritizing NVM paths
        env = os.environ.copy()
        # IMPORTANT: Replace [NODE-BIN-PATH] with your Node.js binary path
        # Example: "/Users/yourname/.nvm/versions/node/v22.17.0/bin" or "/usr/local/bin"
        nvm_bin_path = "[NODE-BIN-PATH]"
        
        # Prepend Node path to ensure we get the working node/npm
        if nvm_bin_path != "[NODE-BIN-PATH]":  # Only prepend if user has configured it
            if "PATH" in env:
                env["PATH"] = f"{nvm_bin_path}:{env['PATH']}"
            else:
                env["PATH"] = nvm_bin_path
            
        if verbose:
            # Now check what we get with the updated PATH
            import shutil
            # Temporarily update PATH for this check
            original_path = os.environ.get("PATH", "")
            os.environ["PATH"] = env["PATH"]
            
            node_path = shutil.which("node")
            npm_path = shutil.which("npm") 
            print(f"  Node path: {node_path}")
            print(f"  npm path: {npm_path}")
            
            # Restore original PATH
            os.environ["PATH"] = original_path
        
        # Try execution with dependency installation if needed
        # Allow up to 5 attempts to handle multiple missing dependencies
        for attempt in range(5):  # Allow more attempts for multiple dependencies
            try:
                # Run the code with Node.js
                process = subprocess.run(
                    ["node", js_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    env=env,
                    timeout=timeout,
                    cwd=temp_dir
                )
                
                if process.returncode == 0:
                    # Success!
                    return True, ""
                
                # There was an error - check if it's a missing module
                error = process.stderr.strip()
                
                # Check if it's a module not found error (allow installation on any attempt)
                if "Cannot find module" in error or "MODULE_NOT_FOUND" in error or "Cannot find package" in error:
                    # Extract the missing module name
                    patterns = [
                        r"Cannot find module '([^']+)'",
                        r"Cannot find package '([^']+)' imported from",
                        r"Error: Cannot find module '([^']+)'",
                        r"MODULE_NOT_FOUND.*'([^']+)'"
                    ]
                    
                    module_name = None
                    for pattern in patterns:
                        match = re.search(pattern, error)
                        if match:
                            module_name = match.group(1)
                            # Remove any path components to get just the package name
                            # For scoped packages (@scope/package), preserve both scope and package
                            if '/' in module_name:
                                if module_name.startswith('@'):
                                    # Scoped package: keep @scope/package
                                    parts = module_name.split('/')
                                    if len(parts) >= 2:
                                        module_name = parts[0] + '/' + parts[1]
                                else:
                                    # Regular package: just take first part
                                    module_name = module_name.split('/')[0]
                            break
                    
                    if module_name:
                        if verbose:
                            print(f"  Missing dependency: {module_name}, attempting to install...")
                        
                        # Simple npm install - works in your shell!
                        if verbose:
                            print(f"  Installing with: npm install {module_name}")
                        
                        # Try to install the module using npm
                        install_process = subprocess.run(
                            ["npm", "install", module_name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                            cwd=temp_dir,
                            env=env
                        )
                        
                        if install_process.returncode == 0:
                            if verbose:
                                print(f"  Successfully installed {module_name}, retrying execution...")
                            # Continue to next attempt
                            continue
                        else:
                            return False, f"Failed to install dependency {module_name}: {install_process.stderr.strip()}"
                
                # Different error or second attempt failed
                if "SyntaxError" in error:
                    return False, f"JavaScript syntax error: {error}"
                elif "ReferenceError" in error:
                    return False, f"JavaScript reference error: {error}"
                elif "TypeError" in error:
                    return False, f"JavaScript type error: {error}"
                else:
                    return False, f"JavaScript execution failed: {error}"
                    
            except subprocess.TimeoutExpired:
                if verbose:
                    print(f"  Test case execution timed out after {timeout} seconds")
                return False, f"Execution timed out after {timeout} seconds"
        
        # Should not reach here after 5 attempts
        return False, "Failed to execute test case after multiple dependency installation attempts"
            
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        # Clean up temporary directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")

def run_typescript_test_case(prefix: str, golden_completion: str, suffix: str, 
                             assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a TypeScript test case by compiling it to JavaScript and executing with Node.js.
    
    Args:
        prefix: Prefix code
        golden_completion: Golden completion code
        suffix: Suffix code
        assertions: Assertion code
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    import uuid
    import random
    import tempfile
    import shutil
    import re
    
    # Generate unique identifiers to avoid race conditions
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"ts_test_{unique_id}_")
    
    try:
        # Combine all code sections for TypeScript
        # Environment variables are inherited from parent process
        combined_code = f"""{prefix}
{golden_completion}
{suffix}

// Run assertions
{assertions}
"""
        
        # Create a temporary TypeScript file
        ts_file = os.path.join(temp_dir, f"test_{unique_id}.ts")
        js_file = os.path.join(temp_dir, f"test_{unique_id}.js")
        
        if verbose:
            print(f"  Creating TypeScript file: {ts_file}")
        
        # Add a small random delay to reduce race conditions on network requests
        time.sleep(random.uniform(0.1, 0.3))
        
        with open(ts_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Ensure we get the same PATH as your shell by prioritizing NVM paths
        env = os.environ.copy()
        # IMPORTANT: Replace [NODE-BIN-PATH] with your Node.js binary path
        # Example: "/Users/yourname/.nvm/versions/node/v22.17.0/bin" or "/usr/local/bin"
        nvm_bin_path = "[NODE-BIN-PATH]"
        
        # Prepend Node path to ensure we get the working node/npm/npx
        if nvm_bin_path != "[NODE-BIN-PATH]":  # Only prepend if user has configured it
            if "PATH" in env:
                env["PATH"] = f"{nvm_bin_path}:{env['PATH']}"
            else:
                env["PATH"] = nvm_bin_path
            
        # First, install TypeScript and Node types in the temp directory
        if verbose:
            print(f"  Installing TypeScript and Node types in temp directory...")
        
        install_ts_process = subprocess.run(
            ["npm", "install", "typescript", "@types/node"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=env,
            timeout=30,
            cwd=temp_dir
        )
        
        if install_ts_process.returncode != 0:
            if verbose:
                print(f"  Warning: Could not install TypeScript locally, will try to use global installation")
        
        # Try compilation with dependency installation if needed
        # Allow up to 5 attempts to handle multiple missing dependencies
        for compile_attempt in range(5):
            if verbose and compile_attempt > 0:
                print(f"  Retrying TypeScript compilation (attempt {compile_attempt + 1})...")
            elif verbose:
                print(f"  Compiling TypeScript to JavaScript...")
            
            # Compile TypeScript to JavaScript using tsc
            compile_process = subprocess.run(
                ["npx", "tsc", ts_file, "--outDir", temp_dir, "--target", "ES2020", "--module", "commonjs", "--esModuleInterop", "--allowSyntheticDefaultImports", "--skipLibCheck"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=env,
                timeout=30,
                cwd=temp_dir
            )
            
            if compile_process.returncode == 0:
                # Compilation succeeded!
                break
                
            # Compilation failed - check if it's due to missing modules
            compile_error = compile_process.stderr.strip()
            compile_output = compile_process.stdout.strip()
            full_error = compile_error if compile_error else compile_output
            
            # Check for missing module errors
            if "Cannot find module" in full_error or "Cannot resolve" in full_error:
                # Extract module name from TypeScript error
                patterns = [
                    r"Cannot find module '([^']+)'",
                    r"Cannot resolve '([^']+)'",
                    r"Could not find a declaration file for module '([^']+)'"
                ]
                
                module_name = None
                for pattern in patterns:
                    match = re.search(pattern, full_error)
                    if match:
                        module_name = match.group(1)
                        # Remove any path components or file extensions
                        # For scoped packages (@scope/package), preserve both scope and package
                        if '/' in module_name:
                            if module_name.startswith('@'):
                                # Scoped package: keep @scope/package
                                parts = module_name.split('/')
                                if len(parts) >= 2:
                                    module_name = parts[0] + '/' + parts[1]
                            else:
                                # Regular package: just take first part
                                module_name = module_name.split('/')[0]
                        if module_name.endswith('.js'):
                            module_name = module_name[:-3]
                        break
                
                if module_name:
                    if verbose:
                        print(f"  Missing dependency: {module_name}, attempting to install...")
                    
                    # Install both the module and its type definitions
                    packages_to_install = [module_name]
                    # Also try to install @types package (may not exist, that's OK)
                    types_package = f"@types/{module_name}"
                    
                    if verbose:
                        print(f"  Installing: npm install {module_name}")
                    
                    install_process = subprocess.run(
                        ["npm", "install", module_name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                        cwd=temp_dir,
                        env=env
                    )
                    
                    if install_process.returncode == 0:
                        if verbose:
                            print(f"  Successfully installed {module_name}")
                        
                        # Try to install types package (don't fail if it doesn't exist)
                        install_types = subprocess.run(
                            ["npm", "install", types_package],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                            cwd=temp_dir,
                            env=env
                        )
                        if install_types.returncode == 0 and verbose:
                            print(f"  Also installed {types_package}")
                        
                        # Continue to retry compilation
                        continue
                    else:
                        # Couldn't install the package
                        if verbose:
                            print(f"  Failed to install {module_name}")
                        # Continue to try compilation anyway
                        continue
            
            # If we've exhausted attempts or it's not a missing module error, fail
            if compile_attempt == 4:  # Last attempt
                if verbose:
                    print(f"  TypeScript compilation failed: {full_error}")
                    if compile_output and compile_error:
                        print(f"  Stdout: {compile_output}")
                return False, f"TypeScript compilation failed: {full_error}"
        
        if verbose:
            print(f"  TypeScript compiled successfully, executing JavaScript...")
        
        # Now execute the compiled JavaScript file
        # Try execution with dependency installation if needed
        for attempt in range(5):  # Allow more attempts for multiple dependencies
            try:
                # Run the compiled JavaScript with Node.js
                process = subprocess.run(
                    ["node", js_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    env=env,
                    timeout=timeout,
                    cwd=temp_dir
                )
                
                if process.returncode == 0:
                    # Success!
                    return True, ""
                
                # There was an error - check if it's a missing module
                error = process.stderr.strip()
                
                # Check if it's a module not found error (allow installation on any attempt)
                if "Cannot find module" in error or "MODULE_NOT_FOUND" in error or "Cannot find package" in error:
                    # Extract the missing module name
                    patterns = [
                        r"Cannot find module '([^']+)'",
                        r"Cannot find package '([^']+)' imported from",
                        r"Error: Cannot find module '([^']+)'",
                        r"MODULE_NOT_FOUND.*'([^']+)'"
                    ]
                    
                    module_name = None
                    for pattern in patterns:
                        match = re.search(pattern, error)
                        if match:
                            module_name = match.group(1)
                            # Remove any path components to get just the package name
                            # For scoped packages (@scope/package), preserve both scope and package
                            if '/' in module_name:
                                if module_name.startswith('@'):
                                    # Scoped package: keep @scope/package
                                    parts = module_name.split('/')
                                    if len(parts) >= 2:
                                        module_name = parts[0] + '/' + parts[1]
                                else:
                                    # Regular package: just take first part
                                    module_name = module_name.split('/')[0]
                            break
                    
                    if module_name:
                        if verbose:
                            print(f"  Missing dependency: {module_name}, attempting to install...")
                        
                        # Simple npm install
                        if verbose:
                            print(f"  Installing with: npm install {module_name}")
                        
                        # Try to install the module using npm
                        install_process = subprocess.run(
                            ["npm", "install", module_name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                            cwd=temp_dir,
                            env=env
                        )
                        
                        if install_process.returncode == 0:
                            if verbose:
                                print(f"  Successfully installed {module_name}, retrying execution...")
                            # Continue to next attempt
                            continue
                        else:
                            return False, f"Failed to install dependency {module_name}: {install_process.stderr.strip()}"
                
                # Different error or second attempt failed
                if "SyntaxError" in error:
                    return False, f"JavaScript syntax error: {error}"
                elif "ReferenceError" in error:
                    return False, f"JavaScript reference error: {error}"
                elif "TypeError" in error:
                    return False, f"JavaScript type error: {error}"
                else:
                    return False, f"JavaScript execution failed: {error}"
                    
            except subprocess.TimeoutExpired:
                if verbose:
                    print(f"  Test case execution timed out after {timeout} seconds")
                return False, f"Execution timed out after {timeout} seconds"
        
        # Should not reach here after 5 attempts
        return False, "Failed to execute test case after multiple dependency installation attempts"
            
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        # Clean up temporary directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")

def run_java_test_case(prefix: str, golden_completion: str, suffix: str, 
                       assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a Java test case with automatic dependency detection and build tool selection.
    Uses simple javac for basic cases, Gradle for complex cases with dependencies.
    """
    import re
    
    # Combine code to analyze
    combined_code = f"{prefix}{golden_completion}{suffix}"
    
    # Detect if we need external dependencies or complex setup
    needs_build_tool = False
    
    # Check for external dependencies (non-standard Java libraries)
    external_imports = [
        'org.apache.commons',
        'com.google.common', 
        'org.junit',
        'org.json',
        'com.fasterxml.jackson',
        'org.springframework',
        'org.hibernate',
        'org.jdom2',
        'org.apache.poi',
        'com.google.gson',
        'org.dom4j',
        'org.apache.logging.log4j',  # Apache Log4j2
        'javax.xml.bind',  # JAXB was removed from JDK 11+, needs external dependency
        'jakarta.xml.bind'  # Jakarta JAXB (modern replacement)
    ]
    
    for ext_import in external_imports:
        if ext_import in combined_code:
            needs_build_tool = True
            if verbose:
                print(f"  Detected external dependency: {ext_import}")
            break
    
    # Check for package declaration  
    package_match = re.search(r'^\s*package\s+([\w.]+);', combined_code, re.MULTILINE)
    if package_match:
        needs_build_tool = True
        if verbose:
            print(f"  Detected package declaration: {package_match.group(1)}")
    
    # Route to appropriate execution method
    if needs_build_tool:
        if verbose:
            print("  Using Gradle for complex case...")
        return run_java_test_case_gradle(prefix, golden_completion, suffix, assertions, verbose, timeout)
    else:
        if verbose:
            print("  Using simple javac for basic case...")
        return run_java_test_case_simple(prefix, golden_completion, suffix, assertions, verbose, timeout)

def run_csharp_test_case_simple(prefix: str, golden_completion: str, suffix: str, 
                                assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a C# test case by creating a temporary .cs file and executing with dotnet run.
    
    Args:
        prefix: Prefix code (before the completion)
        golden_completion: Golden completion code 
        suffix: Suffix code (after the completion)
        assertions: Assertion code (currently unused, handled in suffix)
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    import uuid
    import tempfile
    import shutil
    import re
    
    # Generate unique identifier to avoid race conditions
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"cs_test_{unique_id}_")
    
    try:
        # Combine all code sections with proper newlines to avoid concatenation issues
        prefix_clean = prefix.rstrip()
        suffix_clean = suffix.lstrip()
        
        # If golden_completion doesn't start with newline and prefix doesn't end with one, add it
        if not prefix.endswith('\n') and not golden_completion.startswith('\n'):
            combined_code = f"{prefix_clean}\n{golden_completion}{suffix_clean}"
        else:
            combined_code = f"{prefix}{golden_completion}{suffix}"
        
        # Extract class name from the code to determine if we have a full program structure
        class_name = "TestCase"  # Default fallback
        class_match = re.search(r'public\s+class\s+(\w+)|class\s+(\w+)', combined_code)
        if class_match:
            class_name = class_match.group(1) or class_match.group(2)
        
        # Check if code contains Main method
        has_main = bool(re.search(r'static\s+void\s+Main|static\s+Task\s+Main|static\s+async\s+Task\s+Main', combined_code))
        
        # If no Main method found, wrap in a simple console application
        if not has_main:
            # Wrap the code in a Main method
            combined_code = f"""
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

public class {class_name}
{{
    public static void Main(string[] args)
    {{
        {combined_code}
        
        // Run assertions if any
        {assertions if assertions else ""}
    }}
}}
"""
        
        # Create project directory and files
        project_name = f"TestProject_{unique_id}"
        project_dir = os.path.join(temp_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create .csproj file for dotnet project
        csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>"""
        
        csproj_file = os.path.join(project_dir, f"{project_name}.csproj")
        with open(csproj_file, 'w', encoding='utf-8') as f:
            f.write(csproj_content)
        
        # Create C# source file
        cs_file = os.path.join(project_dir, "Program.cs")
        
        if verbose:
            print(f"  Creating C# file: {cs_file}")
            print(f"  Class name: {class_name}")
        
        with open(cs_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Use dotnet run to compile and execute
        run_command = ["dotnet", "run", "--project", project_dir]
        
        if verbose:
            print(f"  Run command: {' '.join(run_command)}")
        
        try:
            # Run the C# program with dotnet
            run_process = subprocess.run(
                run_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout
            )
            
            if run_process.returncode != 0:
                runtime_error = run_process.stderr.strip()
                if verbose:
                    print(f"  Runtime error: {runtime_error}")
                # Check for compilation errors
                if "error CS" in runtime_error:
                    return False, f"Compilation error: {runtime_error}"
                # Check if it's an assertion error
                elif "AssertionException" in runtime_error or "Assert" in runtime_error:
                    return False, f"Assertion failed: {runtime_error}"
                else:
                    return False, f"Runtime error: {runtime_error}"
            
            if verbose:
                output = run_process.stdout.strip()
                if output:
                    print(f"  Program output: {output}")
                print("  Test completed successfully")
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  Test execution timed out after {timeout} seconds")
            return False, f"Execution timed out after {timeout} seconds"
            
    except Exception as e:
        if verbose:
            print(f"  Unexpected error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"
    
    finally:
        # Clean up temporary directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")

def run_csharp_test_case_dotnet(prefix: str, golden_completion: str, suffix: str, 
                                assertions: str = "", verbose=True, timeout=60) -> Tuple[bool, str]:
    """
    Run a C# test case using dotnet for complex cases with NuGet dependencies.
    Uses dotnet to build/compile with dependencies, then runs the compiled program.
    """
    import uuid
    import tempfile
    import shutil
    import re
    
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"cs_dotnet_test_{unique_id}_")
    
    try:
        # Combine code sections
        prefix_clean = prefix.rstrip()
        suffix_clean = suffix.lstrip()
        
        if not prefix.endswith('\n') and not golden_completion.startswith('\n'):
            combined_code = f"{prefix_clean}\n{golden_completion}{suffix_clean}"
        else:
            combined_code = f"{prefix}{golden_completion}{suffix}"
        
        # Extract namespace and class name
        namespace_match = re.search(r'namespace\s+([\w.]+)', combined_code)
        namespace_name = namespace_match.group(1) if namespace_match else "TestNamespace"
        
        class_match = re.search(r'public\s+class\s+(\w+)|class\s+(\w+)', combined_code)
        class_name = (class_match.group(1) or class_match.group(2)) if class_match else "TestCase"
        
        # Check if code contains Main method
        has_main = bool(re.search(r'static\s+void\s+Main|static\s+Task\s+Main|static\s+async\s+Task\s+Main', combined_code))
        
        # If no namespace declaration and no Main, add structure
        if not namespace_match and not has_main:
            combined_code = f"""
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace {namespace_name}
{{
    public class {class_name}
    {{
        public static void Main(string[] args)
        {{
            {combined_code}
            
            // Run assertions if any
            {assertions if assertions else ""}
        }}
    }}
}}
"""
        
        # Create project directory
        project_name = f"TestProject_{unique_id}"
        project_dir = os.path.join(temp_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Detect required NuGet packages from imports
        packages = []
        
        # Check for common NuGet package namespaces
        if 'Newtonsoft.Json' in combined_code:
            packages.append('<PackageReference Include="Newtonsoft.Json" Version="13.0.3" />')
        if 'NUnit' in combined_code:
            packages.append('<PackageReference Include="NUnit" Version="3.13.3" />')
        if 'xunit' in combined_code.lower():
            packages.append('<PackageReference Include="xunit" Version="2.4.2" />')
        if 'Microsoft.EntityFrameworkCore' in combined_code:
            packages.append('<PackageReference Include="Microsoft.EntityFrameworkCore" Version="7.0.0" />')
        if 'UseInMemoryDatabase' in combined_code:
            packages.append('<PackageReference Include="Microsoft.EntityFrameworkCore.InMemory" Version="7.0.0" />')
        if 'System.Data.SqlClient' in combined_code:
            packages.append('<PackageReference Include="System.Data.SqlClient" Version="4.8.5" />')
        if 'RestSharp' in combined_code:
            packages.append('<PackageReference Include="RestSharp" Version="110.2.0" />')
        if 'Dapper' in combined_code:
            packages.append('<PackageReference Include="Dapper" Version="2.0.123" />')
        if 'Serilog' in combined_code:
            packages.append('<PackageReference Include="Serilog" Version="3.1.1" />')
        if 'AutoMapper' in combined_code:
            packages.append('<PackageReference Include="AutoMapper" Version="12.0.1" />')
        if 'FluentValidation' in combined_code:
            packages.append('<PackageReference Include="FluentValidation" Version="11.8.0" />')
        if 'Microsoft.ML' in combined_code:
            packages.append('<PackageReference Include="Microsoft.ML" Version="3.0.1" />')
        if 'Azure.AI.TextAnalytics' in combined_code:
            packages.append('<PackageReference Include="Azure.AI.TextAnalytics" Version="5.3.0" />')
        if 'Microsoft.Azure.Cosmos' in combined_code:
            packages.append('<PackageReference Include="Microsoft.Azure.Cosmos" Version="3.35.4" />')
        if 'Microsoft.Azure.Documents' in combined_code or 'DocumentClient' in combined_code:
            packages.append('<PackageReference Include="Microsoft.Azure.DocumentDB.Core" Version="2.22.0" />')
        if 'MongoDB.Bson' in combined_code or 'MongoDB.Driver' in combined_code:
            packages.append('<PackageReference Include="MongoDB.Driver" Version="2.22.0" />')
        if 'Azure.Identity' in combined_code:
            packages.append('<PackageReference Include="Azure.Identity" Version="1.10.4" />')
        if 'Azure.Security.KeyVault' in combined_code:
            packages.append('<PackageReference Include="Azure.Security.KeyVault.Secrets" Version="4.5.0" />')
        if 'Azure.Storage.Blobs' in combined_code:
            packages.append('<PackageReference Include="Azure.Storage.Blobs" Version="12.19.1" />')
        if 'Azure.Data.Tables' in combined_code:
            packages.append('<PackageReference Include="Azure.Data.Tables" Version="12.8.3" />')
        
        # Create .csproj file with dependencies
        packages_section = '\n    '.join(packages) if packages else ""
        
        csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  {"<ItemGroup>" if packages else ""}
    {packages_section}
  {"</ItemGroup>" if packages else ""}
</Project>"""
        
        csproj_file = os.path.join(project_dir, f"{project_name}.csproj")
        with open(csproj_file, 'w', encoding='utf-8') as f:
            f.write(csproj_content)
        
        # Write C# file
        cs_file = os.path.join(project_dir, "Program.cs")
        with open(cs_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        if verbose:
            print(f"  Using dotnet with dependencies")
            print(f"  Namespace: {namespace_name}")
            print(f"  Class: {class_name}")
            print(f"  NuGet packages: {len(packages)}")
        
        # Step 1: Build with dotnet to compile and restore dependencies
        build_cmd = ['dotnet', 'build', project_dir, '--configuration', 'Release']
        if verbose:
            print(f"  Building: {' '.join(build_cmd)}")
        
        build_result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if build_result.returncode != 0:
            error_output = build_result.stdout + build_result.stderr
            if "error CS" in error_output:
                return False, f"Compilation failed: {error_output[-500:]}"
            else:
                return False, f"Build failed: {error_output[-200:]}"
        
        # Step 2: Run the compiled program
        run_cmd = ['dotnet', 'run', '--project', project_dir, '--configuration', 'Release', '--no-build']
        
        if verbose:
            print(f"  Running: {' '.join(run_cmd)}")
        
        run_result = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if verbose and run_result.stdout:
            print(f"  Program output: {run_result.stdout.strip()}")
        
        if run_result.returncode == 0:
            if verbose:
                print("  Test completed successfully")
            return True, ""
        else:
            error_output = run_result.stdout + run_result.stderr
            
            # Check for common error patterns
            if "AssertionException" in error_output or "Assert" in error_output:
                return False, f"Assertion failed: {error_output.strip()}"
            elif "Exception" in error_output:
                return False, f"Runtime exception: {error_output.strip()}"
            else:
                return False, f"Program failed: {error_output.strip()}"
                
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        # Clean up
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up temporary directory")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")

def run_cpp_test_case(prefix: str, golden_completion: str, suffix: str, 
                      assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a C++ test case by creating a temporary file, compiling with g++, and executing.
    
    Args:
        prefix: Prefix code (before the completion)
        golden_completion: Golden completion code 
        suffix: Suffix code (after the completion)
        assertions: Assertion code (currently unused, handled in suffix)
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    import uuid
    import tempfile
    import shutil
    import re
    
    # Generate unique identifier to avoid race conditions
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"cpp_test_{unique_id}_")
    
    try:
        # Combine all code sections with proper newlines to avoid concatenation issues
        prefix_clean = prefix.rstrip()
        suffix_clean = suffix.lstrip()
        
        # If golden_completion doesn't start with newline and prefix doesn't end with one, add it
        if not prefix.endswith('\n') and not golden_completion.startswith('\n'):
            combined_code = f"{prefix_clean}\n{golden_completion}{suffix_clean}"
        else:
            combined_code = f"{prefix}{golden_completion}{suffix}"
        
        # Add common includes if not present to ensure basic functionality
        common_includes = [
            "#include <iostream>",
            "#include <cassert>", 
            "#include <string>",
            "#include <vector>",
            "#include <algorithm>"
        ]
        
        # Check if we need to add any missing includes
        includes_to_add = []
        for include in common_includes:
            if include not in combined_code and not any(simplified in combined_code for simplified in [include.split('<')[1].split('>')[0]]):
                includes_to_add.append(include)
        
        # Add missing includes at the top if needed
        if includes_to_add:
            includes_section = '\n'.join(includes_to_add) + '\n\n'
            combined_code = includes_section + combined_code
        
        # Ensure we have a main function if none exists
        if 'int main(' not in combined_code and 'int main()' not in combined_code:
            # Wrap the code in a main function
            combined_code = f"""
#include <iostream>
#include <cassert>
#include <string>
#include <vector>
#include <algorithm>

int main() {{
    {combined_code}
    
    // Run assertions if any
    {assertions if assertions else ""}
    
    return 0;
}}
"""
        else:
            # If there's already a main function, just add assertions at the end if any
            if assertions:
                # Insert assertions before the return statement in main
                lines = combined_code.split('\n')
                main_found = False
                brace_count = 0
                insertion_point = len(lines) - 1
                
                for i, line in enumerate(lines):
                    if 'int main(' in line or 'int main()' in line:
                        main_found = True
                    if main_found:
                        brace_count += line.count('{') - line.count('}')
                        if brace_count == 0 and main_found:
                            # Find the return statement before this point
                            for j in range(i, -1, -1):
                                if 'return' in lines[j]:
                                    insertion_point = j
                                    break
                            break
                
                # Insert assertions before return
                lines.insert(insertion_point, f"    // Assertions\n    {assertions}")
                combined_code = '\n'.join(lines)
        
        # Create C++ source file
        cpp_file = os.path.join(temp_dir, f"test_{unique_id}.cpp")
        exe_file = os.path.join(temp_dir, f"test_{unique_id}")
        
        if verbose:
            print(f"  Creating C++ file: {cpp_file}")
        
        with open(cpp_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Try different compilers in order of preference
        compilers = ['g++', 'clang++', 'c++']
        compiler_found = None
        
        for compiler in compilers:
            try:
                # Test if compiler is available
                test_process = subprocess.run(
                    [compiler, '--version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                if test_process.returncode == 0:
                    compiler_found = compiler
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        if not compiler_found:
            return False, "No C++ compiler found (tried g++, clang++, c++)"
        
        # Compile the C++ file with common library paths
        compile_command = [
            compiler_found, 
            cpp_file, 
            '-o', exe_file,
            '-std=c++17',  # Use C++17 standard
            '-Wall',       # Enable warnings
            '-O2'          # Optimization
        ]
        
        # IMPORTANT: Replace [CPP-INCLUDE-PATHS] with your system's include paths if needed
        # Example paths for macOS with Homebrew:
        #   '/opt/homebrew/include', '/usr/local/include'
        # Example paths for Linux:
        #   '/usr/include', '/usr/local/include'
        # Leave as empty list if you don't need external libraries
        common_include_paths = []  # [CPP-INCLUDE-PATHS]
        
        # Add standard system paths that commonly exist
        standard_paths = ['/usr/local/include', '/usr/include']
        for path in standard_paths:
            if os.path.exists(path):
                compile_command.extend(['-I', path])
        
        # Add any user-configured paths
        for path in common_include_paths:
            if os.path.exists(path):
                compile_command.extend(['-I', path])
        
        # IMPORTANT: Replace [CPP-LIB-PATHS] with your system's library paths if needed
        # Example paths for macOS with Homebrew:
        #   '/opt/homebrew/lib', '/usr/local/lib'
        # Example paths for Linux:
        #   '/usr/lib', '/usr/local/lib'
        # Leave as empty list if you don't need external libraries
        common_lib_paths = []  # [CPP-LIB-PATHS]
        
        # Add standard system paths that commonly exist
        standard_lib_paths = ['/usr/local/lib', '/usr/lib']
        for path in standard_lib_paths:
            if os.path.exists(path):
                compile_command.extend(['-L', path])
        
        # Add any user-configured paths
        for path in common_lib_paths:
            if os.path.exists(path):
                compile_command.extend(['-L', path])
        
        # Detect and link common libraries based on includes in the code
        if 'openssl/' in combined_code.lower():
            # OpenSSL libraries
            compile_command.extend(['-lssl', '-lcrypto'])
        if 'boost/' in combined_code.lower():
            # Common Boost libraries
            compile_command.extend(['-lboost_system', '-lboost_filesystem'])
        if 'pthread' in combined_code.lower() or 'std::thread' in combined_code:
            # Threading support
            compile_command.extend(['-lpthread'])
        if '<curl/' in combined_code.lower():
            # libcurl
            compile_command.extend(['-lcurl'])
        if 'harfbuzz/' in combined_code.lower() or '<hb' in combined_code.lower():
            # HarfBuzz and FreeType libraries
            compile_command.extend(['-lharfbuzz', '-lfreetype'])
        elif 'ft2build.h' in combined_code or 'FT_' in combined_code:
            # FreeType library only
            compile_command.extend(['-lfreetype'])
        if 'sqlite3.h' in combined_code or 'sqlite3_' in combined_code:
            # SQLite3 library
            compile_command.extend(['-lsqlite3'])
        if 'opencv2/' in combined_code.lower() or 'cv::' in combined_code:
            # OpenCV libraries - start with core, add modules based on usage
            opencv_libs = ['-lopencv_core']
            if 'cv::ml::' in combined_code or '#include <opencv2/ml.hpp>' in combined_code:
                opencv_libs.append('-lopencv_ml')
            if 'imread' in combined_code or 'imwrite' in combined_code or 'VideoCapture' in combined_code:
                opencv_libs.extend(['-lopencv_imgcodecs', '-lopencv_imgproc'])
            if 'imshow' in combined_code or 'waitKey' in combined_code or 'namedWindow' in combined_code:
                opencv_libs.append('-lopencv_highgui')
            if 'detectAndCompute' in combined_code or 'matchFeatures' in combined_code:
                opencv_libs.append('-lopencv_features2d')
            compile_command.extend(opencv_libs)
        if '#include <armadillo>' in combined_code or 'arma::' in combined_code:
            # Armadillo library - requires armadillo library
            compile_command.extend(['-larmadillo'])
        if 'Python.h' in combined_code or 'Py_' in combined_code:
            # Python C API - use python3-config if available
            try:
                # Try to find python3-config in PATH
                python_config = 'python3-config'
                
                # Get Python include paths
                python_includes = subprocess.check_output([python_config, '--includes'], text=True).strip()
                for include in python_includes.split():
                    if include.startswith('-I'):
                        compile_command.extend(['-I', include[2:]])
                
                # Get Python linking flags with embedding support
                try:
                    python_ldflags = subprocess.check_output([python_config, '--ldflags', '--embed'], text=True).strip()
                except subprocess.CalledProcessError:
                    # Fallback for older Python versions without --embed
                    python_ldflags = subprocess.check_output([python_config, '--ldflags'], text=True).strip()
                
                i = 0
                flags = python_ldflags.split()
                while i < len(flags):
                    flag = flags[i]
                    if flag.startswith('-L'):
                        compile_command.extend(['-L', flag[2:]])
                    elif flag.startswith('-l'):
                        compile_command.append(flag)
                    elif flag == '-framework' and i + 1 < len(flags):
                        compile_command.extend(['-framework', flags[i + 1]])
                        i += 1  # Skip the next flag as it's the framework name
                    elif flag.startswith('-framework'):
                        compile_command.append(flag)
                    i += 1
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback: just try to link against python3
                # User may need to configure include/lib paths in common_include_paths above
                compile_command.extend(['-lpython3'])
        
        if verbose:
            print(f"  Compile command: {' '.join(compile_command)}")
        
        try:
            # Compile the C++ file
            compile_process = subprocess.run(
                compile_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout
            )
            
            if compile_process.returncode != 0:
                compile_error = compile_process.stderr.strip()
                if verbose:
                    print(f"  Compilation failed: {compile_error}")
                return False, f"Compilation failed: {compile_error}"
            
            if verbose:
                print("  Compilation successful, running test...")
            
            # Run the compiled executable
            run_process = subprocess.run(
                [exe_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout
            )
            
            if run_process.returncode != 0:
                runtime_error = run_process.stderr.strip()
                if verbose:
                    print(f"  Runtime error: {runtime_error}")
                # Check if it's an assertion error
                if "assertion" in runtime_error.lower() or "assert" in runtime_error.lower():
                    return False, f"Assertion failed: {runtime_error}"
                else:
                    return False, f"Runtime error: {runtime_error}"
            
            if verbose:
                output = run_process.stdout.strip()
                if output:
                    print(f"  Program output: {output}")
                print("  Test completed successfully")
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  Test execution timed out after {timeout} seconds")
            return False, f"Execution timed out after {timeout} seconds"
            
    except Exception as e:
        if verbose:
            print(f"  Unexpected error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"
    
    finally:
        # Clean up temporary directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                if verbose:
                    print(f"  Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")

def run_csharp_test_case(prefix: str, golden_completion: str, suffix: str, 
                        assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a C# test case with automatic dependency detection and build tool selection.
    Uses simple dotnet run for basic cases, dotnet with NuGet for complex cases with dependencies.
    """
    import re
    
    # Combine code to analyze
    combined_code = f"{prefix}{golden_completion}{suffix}"
    
    # Detect if we need external dependencies or complex setup
    needs_nuget = False
    
    # Check for external dependencies (NuGet packages)
    external_namespaces = [
        'Newtonsoft.Json',
        'NUnit',
        'xunit',
        'Microsoft.EntityFrameworkCore',
        'System.Data.SqlClient',
        'RestSharp',
        'Dapper',
        'Serilog',
        'AutoMapper',
        'FluentValidation',
        'Microsoft.Extensions.DependencyInjection',
        'Microsoft.AspNetCore',
        'MongoDB.Driver',
        'StackExchange.Redis',
        'Microsoft.ML',
        'Azure',
        'Azure.AI.TextAnalytics',
        'Microsoft.Azure.Cosmos'
    ]
    
    for ext_namespace in external_namespaces:
        if ext_namespace in combined_code:
            needs_nuget = True
            if verbose:
                print(f"  Detected external dependency: {ext_namespace}")
            break
    
    # Check for namespace declaration (indicates more complex structure)
    namespace_match = re.search(r'namespace\s+([\w.]+)', combined_code)
    if namespace_match and any(ext in namespace_match.group(1) for ext in ['Test', 'Benchmark', 'Company']):
        needs_nuget = True
        if verbose:
            print(f"  Detected namespace declaration: {namespace_match.group(1)}")
    
    # Route to appropriate execution method
    if needs_nuget:
        if verbose:
            print("  Using dotnet with NuGet for complex case...")
        return run_csharp_test_case_dotnet(prefix, golden_completion, suffix, assertions, verbose, timeout)
    else:
        if verbose:
            print("  Using simple dotnet run for basic case...")
        return run_csharp_test_case_simple(prefix, golden_completion, suffix, assertions, verbose, timeout)

def display_test_case(json_str: str) -> None:
    """
    Parse and display a test case JSONL entry in a readable format.
    
    Args:
        json_str: The JSON string containing the test case
    """
    import json
    
    # Remove markdown code block markers if present
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    try:
        test_case = json.loads(json_str)
        
        print("=" * 80)
        print(f"Test Case ID: {test_case['id']}")
        print(f"Source: {test_case['testsource']}")
        print(f"Language: {test_case['language']}")
        print("=" * 80)
        
        print("\nPREFIX CODE:")
        print("-" * 40)
        print(test_case['prefix'])
        
        print("\nGOLDEN COMPLETION:")
        print("-" * 40)
        print(test_case['golden_completion'])
        
        print("\nSUFFIX CODE:")
        print("-" * 40)
        print(test_case['suffix'])
        
        print("\nJUSTIFICATION:")
        print("-" * 40)
        print(test_case['LLM_justification'])
        
        print("\nASSERTIONS:")
        print("-" * 40)
        print(test_case['assertions'])
        print("=" * 80)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except KeyError as e:
        print(f"Missing required field in JSON: {e}")

def validate_test_case(json_str: str, language="python") -> dict:
    """
    Validate a test case JSONL entry by testing the combined code execution.
    
    Args:
        json_str: The JSON string containing the test case
        language: The programming language of the test case
        
    Returns:
        dict: Validation results for the complete test case
    """
    import json
    import ast
    
    result = {
        "syntax_valid": False,
    }
    
    # Remove markdown code block markers if present
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    try:

        try:
            display_test_case(json_str)
        except Exception as debug_e:
            print(f"DEBUG error: {str(debug_e)}")

        test_case = json.loads(json_str)
        
        # Combine all code sections
        combined_code = f"""
{test_case['prefix']}

{test_case['golden_completion']}

{test_case['suffix']}

{test_case['assertions']}
"""
        
        if language.lower() == "python":
            try:
                ast.parse(combined_code)
                result["syntax_valid"] = True
            except SyntaxError as e:
                print(f"Syntax error in combined code: {str(e)}")
                return result
        else:
            parser = get_parser(language.lower())

            processed_code = combined_code.encode("utf-8", errors="ignore").decode("utf-8")
            tree = parser.parse(bytes(processed_code, "utf-8"))
            if tree.root_node.has_error:
                print(f"Syntax error in combined code")

                error_nodes = []
                
                def collect_error_nodes(node):
                    if node.has_error:
                        error_nodes.append(node)
                    for child in node.children:
                        collect_error_nodes(child)
                
                collect_error_nodes(tree.root_node)
                
                # Print first 3 error nodes
                for i, node in enumerate(error_nodes[:3]):
                    print(f"Error node {i}: {node.type} at line {node.start_point[0]+1}")

                return result
            else:
                result["syntax_valid"] = True
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    return result

def display_validation_results(json_str: str, language="python") -> None:
    """
    Display test case validation results in a clear format.
    """
    results = validate_test_case(json_str, language)
    
    print("\nVALIDATION RESULTS:")
    print("=" * 40)
    print(f"Syntax Valid: {results['syntax_valid']}")

    print("=" * 40)

def process_jsonl_file(input_file: str, output_file: str) -> None:
    """
    Process each line in a JSONL file and write formatted test cases to a text file.
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output text file
    """
    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line_number, line in enumerate(f_in, 1):
                # Write separator for each test case
                f_out.write(f"\n{'='*80}\n")
                f_out.write(f"Test Case #{line_number}\n")
                f_out.write(f"{'='*80}\n\n")
                
                # Redirect stdout to capture output from display functions
                from io import StringIO
                import sys
                
                # Create string buffer to capture output
                output_buffer = StringIO()
                # Save original stdout
                original_stdout = sys.stdout
                # Redirect stdout to buffer
                sys.stdout = output_buffer
                
                try:
                    # Call display functions
                    display_test_case(line)
                    
                    # Get captured output and write to file
                    output = output_buffer.getvalue()
                    f_out.write(output)
                    
                except Exception as e:
                    f_out.write(f"Error processing test case: {str(e)}\n")
                
                finally:
                    # Restore original stdout
                    sys.stdout = original_stdout
                    output_buffer.close()

def find_jsonl_files(directory):
    """
    Find all JSONL files in the specified directory (excluding _formatted.jsonl files).
    
    Args:
        directory: Path to the directory to search
        
    Returns:
        List of JSONL file paths
    """
    jsonl_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.jsonl') and not file.endswith('_formatted.jsonl'):
                jsonl_files.append(os.path.join(root, file))
    return jsonl_files

def calculate_pass_at_k(n: int, c: int, k: int) -> float:
    """
    Calculate pass@k using the formula: pass@k := E[1 - comb(n-c, k) / comb(n, k)]
    
    Args:
        n: Total number of samples
        c: Number of correct samples
        k: Number of samples to consider
        
    Returns:
        pass@k score
    """
    if n - c < k:
        return 1.0
    return 1.0 - (comb(n - c, k) / comb(n, k))

def execute_model_completions(benchmark_jsonl_files: List[str], models_dir="completions/python", 
                             verbose=True, report_file=None, models_filter=None, json_output_file=None, 
                             pass_at_k=1) -> Dict:
    """
    Execute Python test cases using model completions instead of golden completions.
    
    Args:
        benchmark_jsonl_files: List of benchmark JSONL file paths to process
        models_dir: Directory containing model completions
        verbose: Whether to print detailed information during execution
        report_file: Path to file for saving detailed test results
        models_filter: List of model names to filter by (if None, all models are used)
        json_output_file: Path to JSON file for saving detailed results
        pass_at_k: Number of samples to consider for pass@k evaluation
        
    Returns:
        Dict: Summary of execution results by model
    """
    results = {
        "total_cases": 0,
        "models": {},
        "categories": {},  # Track test cases by category
        "pass_at_k": pass_at_k  # Store the k value used
    }
    
    # Track detailed per-test-case results for JSON output
    detailed_results = {
        "total_cases": 0,
        "models": {},
        "categories": {}  # Track detailed category results
    }
    
    # Open report file if specified
    report_fp = None
    if report_file:
        try:
            report_fp = open(report_file, 'w', encoding='utf-8')
            report_fp.write("MODEL COMPLETIONS BENCHMARK TEST RESULTS\n")
            report_fp.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"Error opening report file: {e}")
            report_fp = None
    
    try:
        # Fix model filtering to be consistent
        if models_filter:
            # Convert to lowercase for case-insensitive matching
            models_filter = [model.lower() for model in models_filter]
        
        for benchmark_file in benchmark_jsonl_files:
            if verbose:
                print(f"\nProcessing benchmark file: {benchmark_file}...")
            
            if report_fp:
                report_fp.write(f"\nBENCHMARK FILE: {benchmark_file}\n")
                report_fp.write("-" * 80 + "\n")
            
            # Extract category from benchmark path, handling nested directories
            path_parts = benchmark_file.split(os.sep)
            category = None
            for i, part in enumerate(path_parts):
                if part.endswith('.jsonl'):
                    # Use immediate parent directory as category
                    category = path_parts[i-1]
                    
                    # Skip the "benchmark" and language directories in the category path
                    # Just use the actual category name (like "api_usage")
                    break
            
            if not category:
                if verbose:
                    print(f"Could not determine category from {benchmark_file}, skipping...")
                continue
            
            if verbose:
                print(f"Extracted category: {category}")
            
            # Initialize category tracking in results if not already present
            if category not in results["categories"]:
                results["categories"][category] = {
                    "total_cases": 0,
                    "models": {}
                }
                detailed_results["categories"][category] = {
                    "total_cases": 0,
                    "models": {}
                }
            
            # For api_usage/api_usage.jsonl, we want to find api_usage/api_usage-*.jsonl
            base_name = os.path.basename(benchmark_file).replace('.jsonl', '')
            completion_dir = os.path.join(models_dir, category)
            os.makedirs(completion_dir, exist_ok=True)
            
            if verbose:
                print(f"Looking for model completions in directory: {completion_dir}")
                print(f"Base name for completion files: {base_name}")
            
            # Find all model completion files for this category
            model_files = {}
            for file in os.listdir(completion_dir):
                if file.startswith(f"{base_name}-") and file.endswith('.jsonl'):
                    # Extract model name from file name
                    model_name = file.replace(f"{base_name}-", "").replace(".jsonl", "")
                    
                    # Skip if models_filter is provided and this model doesn't match any filter
                    if models_filter and not any(model_filter in model_name.lower() for model_filter in models_filter):
                        if verbose:
                            print(f"  Skipping model {model_name} - not in requested models list")
                        continue
                    
                    model_files[model_name] = os.path.join(completion_dir, file)
                    
                    # Initialize model results if not already present
                    if model_name not in results["models"]:
                        results["models"][model_name] = {
                            "successful_cases": 0,
                            "failed_cases": 0,
                            "timeout_cases": 0,
                            "failures": [],
                            "pass_at_k_cases": [],  # Store individual test case results for pass@k calculation
                            "total_completions": 0,
                            "correct_completions": 0
                        }
                        detailed_results["models"][model_name] = {
                            "test_cases": [],
                            "summary": {}
                        }
                    
                    # Initialize model results for this category
                    if model_name not in results["categories"][category]["models"]:
                        results["categories"][category]["models"][model_name] = {
                            "successful_cases": 0,
                            "failed_cases": 0,
                            "timeout_cases": 0,
                            "pass_at_k_cases": [],
                            "total_completions": 0,
                            "correct_completions": 0
                        }
                        detailed_results["categories"][category]["models"][model_name] = {
                            "test_cases": []
                        }
            
            if not model_files:
                if verbose:
                    print(f"No model completion files found for {base_name} in {completion_dir}, skipping...")
                continue
            
            if verbose:
                print(f"Found {len(model_files)} model completion files for {base_name}:")
                for model, path in model_files.items():
                    print(f"  - {model}: {path}")
            
            # Load benchmark test cases
            benchmark_tests = []
            try:
                with open(benchmark_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        benchmark_tests.append(json.loads(line))
                
                if verbose:
                    print(f"Loaded {len(benchmark_tests)} benchmark test cases from {benchmark_file}")
            except Exception as e:
                print(f"Error loading benchmark test cases from {benchmark_file}: {str(e)}")
                continue
            
            # Update total cases count for this category
            results["categories"][category]["total_cases"] += len(benchmark_tests)
            detailed_results["categories"][category]["total_cases"] += len(benchmark_tests)
            
            # Collect all model completions first for debugging comparison
            all_model_completions = {}
            for model_name, model_file in model_files.items():
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        model_completions = []
                        for line in f:
                            json_data = json.loads(line)
                            # Check if we have multiple completions (for pass@k evaluation)
                            completions_list = json_data.get(f"{model_name}_completions", None)
                            if completions_list and isinstance(completions_list, list) and len(completions_list) > 1:
                                # Multiple completions available - store the whole entry with completions list
                                model_completions.append(json_data)
                            else:
                                # Single completion - extract completion using the model name as the key
                                completion = json_data.get(model_name, "")
                                model_completions.append({"completion": completion})
                    all_model_completions[model_name] = model_completions
                    if verbose:
                        print(f"Loaded {len(model_completions)} completions from {model_file}")
                except Exception as e:
                    print(f"Error loading completions from {model_file}: {str(e)}")
            
            # Check if completions are actually different (debugging code can remain the same)
            if verbose and len(all_model_completions) > 1:
                print("\nCOMPARING MODEL COMPLETIONS (SAMPLE):")
                # Take the first few test cases as samples
                if benchmark_tests and all(model_name in all_model_completions and all_model_completions[model_name] for model_name in model_files):
                    for idx in range(min(3, len(benchmark_tests))):  # Check first 3 test cases
                        print(f"\nTEST CASE #{idx+1} (ID: {benchmark_tests[idx]['id']}) COMPLETION COMPARISON:")
                        completions_are_same = True
                        first_completion = None
                        
                        for i, model_name in enumerate(model_files):
                            if idx < len(all_model_completions[model_name]):
                                current_completion = all_model_completions[model_name][idx].get("completion", "")
                                if i == 0:
                                    first_completion = current_completion
                                    print(f"  {model_name} (first 80 chars): {first_completion[:80]}")
                                else:
                                    if current_completion != first_completion:
                                        completions_are_same = False
                                    print(f"  {model_name} (first 80 chars): {current_completion[:80]}")
                                    if current_completion == first_completion:
                                        print("  WARNING: Same as first model")
                        
                        if completions_are_same:
                            print("  WARNING: ALL MODELS HAVE IDENTICAL COMPLETIONS FOR THIS TEST CASE!")
                        else:
                            print("  Models have different completions for this test case.")
            
            # Now load each model's completions and run the tests
            for model_name, model_completions in all_model_completions.items():
                if verbose:
                    print(f"\nEvaluating model: {model_name}")
                
                if report_fp:
                    report_fp.write(f"\nMODEL: {model_name}\n")
                    report_fp.write("-" * 40 + "\n")
                
                if len(model_completions) != len(benchmark_tests):
                    print(f"WARNING: Number of completions ({len(model_completions)}) does not match benchmark tests ({len(benchmark_tests)})")
                
                # Run tests for each benchmark case with the corresponding model completion(s)
                for i, (benchmark, completion_data) in enumerate(zip(benchmark_tests, model_completions), 1):
                    results["total_cases"] += 1
                    detailed_results["total_cases"] += 1
                    
                    if verbose:
                        print(f"Running test case #{i} (ID: {benchmark['id']}) with model {model_name}...")
                    
                    # Get test case components from benchmark
                    prefix = benchmark["prefix"]
                    
                    # Check if we have multiple completions (for pass@k evaluation)
                    completions_list = completion_data.get(f"{model_name}_completions", None)
                    if completions_list and len(completions_list) > 1:
                        # Multiple completions available
                        model_completions_for_test = completions_list
                        if verbose:
                            print(f"Model {model_name} has {len(model_completions_for_test)} completions for this test case")
                    else:
                        # Single completion
                        model_completion = completion_data.get("completion", completion_data.get(model_name, ""))
                        model_completions_for_test = [model_completion]
                        if verbose:
                            print(f"Model {model_name} completion (truncated to 100 chars):")
                            print(f"  {model_completion[:100]}" + ("..." if len(model_completion) > 100 else ""))
                    
                    suffix = benchmark["suffix"]
                    assertions = benchmark.get("assertions", "")
                    
                    # Write test case info to report
                    if report_fp:
                        report_fp.write(f"\nTEST CASE #{i} (ID: {benchmark['id']})\n")
                        report_fp.write(f"  Source: {benchmark.get('testsource', 'Unknown')}\n\n")
                    
                    # Execute the test case with the model's completion(s)
                    completion_results = []
                    correct_count = 0
                    total_count = len(model_completions_for_test)
                    
                    for comp_idx, model_completion in enumerate(model_completions_for_test):
                        # Add delay between executions of the same test case to prevent resource conflicts
                        if comp_idx > 0:
                            time.sleep(0.2)  # Small delay between completions
                            
                        # Detect language from benchmark data and route to appropriate test execution function
                        test_language = benchmark.get("language", "python").lower()
                        
                        if test_language == "java":
                            success, error_msg = run_java_test_case(
                                prefix, model_completion, suffix, assertions, verbose=False, timeout=30
                            )
                        elif test_language == "javascript":
                            success, error_msg = run_javascript_test_case(
                                prefix, model_completion, suffix, assertions, verbose=False, timeout=30
                            )
                        elif test_language == "typescript":
                            success, error_msg = run_typescript_test_case(
                                prefix, model_completion, suffix, assertions, verbose=False, timeout=30
                            )
                        elif test_language == "c_sharp" or test_language == "csharp" or test_language == "c#":
                            success, error_msg = run_csharp_test_case(
                                prefix, model_completion, suffix, assertions, verbose=False, timeout=30
                            )
                        elif test_language == "cpp" or test_language == "c++":
                            success, error_msg = run_cpp_test_case(
                                prefix, model_completion, suffix, assertions, verbose=False, timeout=30
                            )
                        else:  # Default to Python for other languages (python, etc.)
                            success, error_msg = run_python_test_case(
                                prefix, model_completion, suffix, assertions, verbose=False, timeout=30
                            )
                        
                        # Check if timeout occurred
                        is_timeout = "timed out" in error_msg.lower()
                        
                        completion_results.append({
                            "completion_index": comp_idx,
                            "success": success,
                            "error": error_msg if not success else None,
                            "is_timeout": is_timeout if not success else False
                        })
                        
                        if success:
                            correct_count += 1
                    
                    # Calculate pass@k for this test case
                    if total_count >= pass_at_k:
                        pass_at_k_score = calculate_pass_at_k(total_count, correct_count, pass_at_k)
                    else:
                        # If we don't have enough completions, use what we have
                        pass_at_k_score = 1.0 if correct_count > 0 else 0.0
                    
                    # Determine overall success for this test case (at least one completion passed)
                    overall_success = correct_count > 0
                    
                    # Create detailed test case result entry
                    test_case_result = {
                        "test_id": benchmark['id'],
                        "file": benchmark_file,
                        "category": category,
                        "success": overall_success,
                        "total_completions": total_count,
                        "correct_completions": correct_count,
                        "pass_at_k_score": pass_at_k_score,
                        "completion_results": completion_results
                    }
                    detailed_results["models"][model_name]["test_cases"].append(test_case_result)
                    detailed_results["categories"][category]["models"][model_name]["test_cases"].append(test_case_result)
                    
                    # Update pass@k tracking
                    results["models"][model_name]["pass_at_k_cases"].append(pass_at_k_score)
                    results["models"][model_name]["total_completions"] += total_count
                    results["models"][model_name]["correct_completions"] += correct_count
                    
                    results["categories"][category]["models"][model_name]["pass_at_k_cases"].append(pass_at_k_score)
                    results["categories"][category]["models"][model_name]["total_completions"] += total_count
                    results["categories"][category]["models"][model_name]["correct_completions"] += correct_count
                    
                    if overall_success:
                        # Update global model success stats
                        results["models"][model_name]["successful_cases"] += 1
                        
                        # Update category-specific success stats
                        results["categories"][category]["models"][model_name]["successful_cases"] += 1
                        
                        if verbose:
                            print(f"Test case #{i} (ID: {benchmark['id']}) passed with model {model_name} ({correct_count}/{total_count} completions correct, pass@{pass_at_k}={pass_at_k_score:.3f})")
                        if report_fp:
                            report_fp.write(f"  RESULT: PASS (pass@{pass_at_k}={pass_at_k_score:.3f})\n\n")
                    else:
                        # Update global model failure stats
                        results["models"][model_name]["failed_cases"] += 1
                        
                        # Check for timeouts in any completion
                        has_timeout = any(cr["is_timeout"] for cr in completion_results)
                        if has_timeout:
                            results["models"][model_name]["timeout_cases"] += 1
                        
                        # Update category-specific failure stats
                        results["categories"][category]["models"][model_name]["failed_cases"] += 1
                        if has_timeout:
                            results["categories"][category]["models"][model_name]["timeout_cases"] += 1
                        
                        # Get the error from the first failed completion for the failure record
                        first_error = next((cr["error"] for cr in completion_results if cr["error"]), "Unknown error")
                        results["models"][model_name]["failures"].append({
                            "file": benchmark_file,
                            "category": category,
                            "test_id": benchmark['id'],
                            "error": first_error,
                            "is_timeout": has_timeout,
                            "correct_completions": correct_count,
                            "total_completions": total_count
                        })
                        
                        if verbose:
                            print(f"Test case #{i} (ID: {benchmark['id']}) failed with model {model_name} ({correct_count}/{total_count} completions correct, pass@{pass_at_k}={pass_at_k_score:.3f})")
                            print(f"  Error from first failed completion: {first_error[:100]}")
                            if has_timeout:
                                print("  REASON: TIMEOUT OCCURRED in at least one completion")
                        
                        if report_fp:
                            report_fp.write(f"  RESULT: FAIL (pass@{pass_at_k}={pass_at_k_score:.3f})\n")
                            report_fp.write(f"  Correct completions: {correct_count}/{total_count}\n")
                            report_fp.write(f"  First error: {first_error}\n\n")
                
                # Write model summary to report
                if report_fp:
                    report_fp.write(f"\nSUMMARY FOR MODEL: {model_name}\n")
                    report_fp.write("-" * 40 + "\n")
                    total = results["models"][model_name]["successful_cases"] + results["models"][model_name]["failed_cases"]
                    success_rate = results["models"][model_name]["successful_cases"] / total * 100 if total > 0 else 0
                    
                    # Calculate average pass@k score
                    pass_at_k_scores = results["models"][model_name]["pass_at_k_cases"]
                    avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                    
                    report_fp.write(f"Success rate: {success_rate:.2f}%\n")
                    report_fp.write(f"Average pass@{pass_at_k}: {avg_pass_at_k:.3f}\n")
                    report_fp.write(f"Total completions generated: {results['models'][model_name]['total_completions']}\n")
                    report_fp.write(f"Correct completions: {results['models'][model_name]['correct_completions']}\n")
                    report_fp.write(f"Successful test cases: {results['models'][model_name]['successful_cases']}\n")
                    report_fp.write(f"Failed test cases: {results['models'][model_name]['failed_cases']}\n")
                    timeout_pct = results["models"][model_name]["timeout_cases"] / max(results["models"][model_name]["failed_cases"], 1) * 100 if results["models"][model_name]["failed_cases"] > 0 else 0
                    report_fp.write(f"Timeout failures: {results['models'][model_name]['timeout_cases']} ({timeout_pct:.1f}% of failures)\n\n")
    
    finally:
        # Write overall summary to report file
        if report_fp:
            try:
                report_fp.write("\n" + "="*80 + "\n")
                report_fp.write("OVERALL EXECUTION SUMMARY\n")
                report_fp.write("="*80 + "\n")
                report_fp.write(f"Total test cases: {results['total_cases']}\n\n")
                
                report_fp.write("RESULTS BY MODEL:\n")
                for model_name, model_results in results["models"].items():
                    total = model_results["successful_cases"] + model_results["failed_cases"]
                    success_rate = model_results["successful_cases"] / total * 100 if total > 0 else 0
                    
                    # Calculate average pass@k score
                    pass_at_k_scores = model_results["pass_at_k_cases"]
                    avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                    
                    report_fp.write(f"{model_name}:\n")
                    report_fp.write(f"  Success rate: {success_rate:.2f}%\n")
                    report_fp.write(f"  Average pass@{pass_at_k}: {avg_pass_at_k:.3f}\n")
                    report_fp.write(f"  Total completions: {model_results['total_completions']}\n")
                    report_fp.write(f"  Correct completions: {model_results['correct_completions']}\n")
                    report_fp.write(f"  Successful test cases: {model_results['successful_cases']}\n")
                    report_fp.write(f"  Failed test cases: {model_results['failed_cases']}\n")
                    report_fp.write(f"  Timeout failures: {model_results['timeout_cases']} ({model_results['timeout_cases']/max(model_results['failed_cases'], 1)*100:.1f}% of failures)\n\n")
                
                # Add category breakdown for each model
                report_fp.write("\nRESULTS BY CATEGORY:\n")
                for category, category_results in results["categories"].items():
                    report_fp.write(f"\nCategory: {category}\n")
                    report_fp.write("-" * 50 + "\n")
                    report_fp.write(f"Total test cases: {category_results['total_cases']}\n\n")
                    
                    # Sort models by pass@k score in this category
                    category_model_rates = []
                    for model_name, model_category_results in category_results["models"].items():
                        total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
                        if total > 0:
                            success_rate = model_category_results["successful_cases"] / total * 100
                            # Calculate average pass@k score for this category
                            pass_at_k_scores = model_category_results["pass_at_k_cases"]
                            avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                            category_model_rates.append((model_name, avg_pass_at_k, success_rate, model_category_results))
                    
                    # Sort by pass@k score in descending order
                    category_model_rates.sort(key=lambda x: x[1], reverse=True)
                    
                    for model_name, avg_pass_at_k, success_rate, model_category_results in category_model_rates:
                        total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
                        timeout_pct = model_category_results["timeout_cases"] / max(model_category_results["failed_cases"], 1) * 100 if model_category_results["failed_cases"] > 0 else 0
                        
                        report_fp.write(f"  {model_name}:\n")
                        report_fp.write(f"    Pass@{pass_at_k}: {avg_pass_at_k:.3f}\n")
                        report_fp.write(f"    Success rate: {success_rate:.2f}%\n")
                        report_fp.write(f"    Successful test cases: {model_category_results['successful_cases']}/{total}\n")
                        report_fp.write(f"    Timeout failures: {model_category_results['timeout_cases']} ({timeout_pct:.1f}% of failures)\n")
                
                report_fp.write("\nFAILURES BY MODEL:\n")
                for model_name, model_results in results["models"].items():
                    if model_results["failures"]:
                        report_fp.write(f"{model_name}:\n")
                        for i, failure in enumerate(model_results["failures"], 1):
                            report_fp.write(f"  {i}. Category: {failure['category']} - Test ID: {failure['test_id']}\n")
                            report_fp.write(f"     Error: {failure['error']}\n\n")
            except Exception as e:
                print(f"Error writing summary to report file: {e}")
            
            # Close report file
            try:
                report_fp.close()
                if verbose:
                    print(f"\nDetailed test results saved to {report_file}")
            except Exception as e:
                print(f"Error closing report file: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"Total test cases: {results['total_cases']}")
    print("\nRESULTS BY MODEL:")
    
    # Sort models by pass@k score
    model_pass_at_k_rates = []
    for model_name, model_results in results["models"].items():
        total = model_results["successful_cases"] + model_results["failed_cases"]
        success_rate = model_results["successful_cases"] / total * 100 if total > 0 else 0
        
        # Calculate average pass@k score
        pass_at_k_scores = model_results["pass_at_k_cases"]
        avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
        
        model_pass_at_k_rates.append((model_name, avg_pass_at_k, success_rate, model_results))
    
    # Sort by pass@k score in descending order
    model_pass_at_k_rates.sort(key=lambda x: x[1], reverse=True)
    
    for model_name, avg_pass_at_k, success_rate, model_results in model_pass_at_k_rates:
        print(f"{model_name}:")
        print(f"  Pass@{pass_at_k}: {avg_pass_at_k:.3f}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Total completions: {model_results['total_completions']}")
        print(f"  Correct completions: {model_results['correct_completions']}")
        print(f"  Successful test cases: {model_results['successful_cases']}")
        print(f"  Failed test cases: {model_results['failed_cases']}")
        print(f"  Timeout failures: {model_results['timeout_cases']} ({model_results['timeout_cases']/max(model_results['failed_cases'], 1)*100:.1f}% of failures)")
    
    # Print category breakdown
    print("\nRESULTS BY CATEGORY:")
    
    # Sort categories by name for consistent output
    sorted_categories = sorted(results["categories"].keys())
    
    for category in sorted_categories:
        category_results = results["categories"][category]
        print(f"\nCategory: {category}")
        print("-" * 50)
        print(f"Total test cases: {category_results['total_cases']}")
        
        # Sort models by pass@k score in this category
        category_model_rates = []
        for model_name, model_category_results in category_results["models"].items():
            total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
            if total > 0:
                success_rate = model_category_results["successful_cases"] / total * 100
                # Calculate average pass@k score for this category
                pass_at_k_scores = model_category_results["pass_at_k_cases"]
                avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                category_model_rates.append((model_name, avg_pass_at_k, success_rate, model_category_results))
        
        # Sort by pass@k score in descending order
        category_model_rates.sort(key=lambda x: x[1], reverse=True)
        
        for model_name, avg_pass_at_k, success_rate, model_category_results in category_model_rates:
            total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
            timeout_pct = model_category_results["timeout_cases"] / max(model_category_results["failed_cases"], 1) * 100 if model_category_results["failed_cases"] > 0 else 0
            
            print(f"  {model_name}:")
            print(f"    Pass@{pass_at_k}: {avg_pass_at_k:.3f}")
            print(f"    Success rate: {success_rate:.2f}%")
            print(f"    Successful test cases: {model_category_results['successful_cases']}/{total}")
            print(f"    Timeout failures: {model_category_results['timeout_cases']} ({timeout_pct:.1f}% of failures)")
    
    # Write results to JSON file if specified
    if json_output_file:
        try:
            # Prepare final JSON output with calculated metrics
            json_output = {
                "total_cases": detailed_results["total_cases"],
                "models": {},
                "categories": {}
            }
            
            # Add overall model summaries
            for model_name, model_results in results["models"].items():
                total = model_results["successful_cases"] + model_results["failed_cases"]
                success_rate = model_results["successful_cases"] / total * 100 if total > 0 else 0
                timeout_pct = model_results["timeout_cases"] / max(model_results["failed_cases"], 1) * 100 if model_results["failed_cases"] > 0 else 0
                
                json_output["models"][model_name] = {
                    "success_rate": round(success_rate, 2),
                    "successful_cases": model_results["successful_cases"],
                    "failed_cases": model_results["failed_cases"],
                    "timeout_cases": model_results["timeout_cases"],
                    "timeout_percentage": round(timeout_pct, 1),
                    "test_cases": detailed_results["models"][model_name]["test_cases"]
                }
            
            # Add category breakdowns
            for category, category_results in results["categories"].items():
                json_output["categories"][category] = {
                    "total_cases": category_results["total_cases"],
                    "models": {}
                }
                
                for model_name, model_category_results in category_results["models"].items():
                    total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
                    if total > 0:
                        success_rate = model_category_results["successful_cases"] / total * 100
                        timeout_pct = model_category_results["timeout_cases"] / max(model_category_results["failed_cases"], 1) * 100 if model_category_results["failed_cases"] > 0 else 0
                        
                        json_output["categories"][category]["models"][model_name] = {
                            "success_rate": round(success_rate, 2),
                            "successful_cases": model_category_results["successful_cases"],
                            "failed_cases": model_category_results["failed_cases"],
                            "total_cases": total,
                            "timeout_cases": model_category_results["timeout_cases"],
                            "timeout_percentage": round(timeout_pct, 1),
                            "test_cases": detailed_results["categories"][category]["models"][model_name]["test_cases"]
                        }
            
            with open(json_output_file, 'w', encoding='utf-8') as json_fp:
                json.dump(json_output, json_fp, indent=2)
                
            if verbose:
                print(f"\nJSON results saved to {json_output_file}")
                
        except Exception as e:
            print(f"Error writing results to JSON file: {e}")
    
    return results

def main():
    # Using GPT-4o to generate the benchmark test cases
    endpoint = os.getenv("ENDPOINT_URL", "[ANONYMIZED-ENDPOINT-1]")  
    deployment = os.getenv("DEPLOYMENT_NAME", "[ANONYMIZED-DEPLOYMENT-1]")  

    # Initialize Azure OpenAI Service client with Entra ID authentication
    token_provider = get_bearer_token_provider(  
        DefaultAzureCredential(),  
        "https://cognitiveservices.azure.com/.default"
    )  
    
    client = AzureOpenAI(  
        azure_endpoint=endpoint,  
        azure_ad_token_provider=token_provider,  
        api_version="2024-05-01-preview",  
    )
    
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Generate or execute benchmark test cases')
    parser.add_argument('--execute', action='store_true', help='Execute test cases')
    parser.add_argument('--verbose', action='store_true', help='Print detailed information during execution')
    parser.add_argument('--categories', type=str, help='Comma-separated list of test categories to execute (e.g., api_usage,code_purpose_understanding)')
    parser.add_argument('--report', default="benchmark_report.txt", type=str, help='Path to output file for detailed test results')
    parser.add_argument('--id', type=str, help='Run a specific test case with the given ID')
    parser.add_argument('--model-eval', action='store_true', help='Evaluate model completions against benchmark test cases')
    parser.add_argument('--models', type=str, help='Comma-separated list of model names to evaluate (e.g., 4o_mini,gpt_3.5_turbo)')
    parser.add_argument('--json-output', type=str, help='Path to output JSON file for detailed test results')
    parser.add_argument('--models-dir', type=str, default=None, 
                       help='Directory containing model completions (default: completions/{language})')
    parser.add_argument('--pass-at-k', type=int, default=1,
                       help='Evaluate pass@k where k is the number of samples to consider (default: 1)')
    # Arguments for benchmark generation
    parser.add_argument('--generate', action='store_true', help='Generate benchmark test cases')
    parser.add_argument('--completions', type=int, default=10, help='Number of completions to generate')
    parser.add_argument('--language', type=str, default='python', choices=['python', 'javascript', 'c_sharp', 'cpp', 'typescript', 'java', 'all'], 
                        help='Programming language for benchmark generation or execution (use "all" for all languages)')
    parser.add_argument('--output', type=str, help='Custom output file path for generated benchmarks')
    parser.add_argument('--prompt-type', type=str, default='api_usage', 
                        help='Type of prompt to use (e.g., api_usage, code_purpose_understanding)')
    
    args = parser.parse_args()
    
    if args.execute:
        # Print information about API keys when executing test cases
        if args.categories and "api_usage" in args.categories:
            print("\nNOTE: API Usage test cases may require API keys. Add your API keys to a .env file")
            print("in the root directory with the format API_KEY=your_api_key. These will be")
            print("available to the test cases during execution.\n")
        
        # Handle 'all' language option for non-model-eval execution
        if args.language == 'all' and not args.model_eval:
            print("Error: --language all is only supported with --model-eval")
            print("Please specify a specific language for golden completion execution.")
            return
        
        # Set default models_dir if not provided
        if not args.models_dir:
            if args.language == 'all':
                # For 'all', we'll set the base directory and add language subdirs later
                args.models_dir = 'completions'
            else:
                args.models_dir = f'completions/{args.language}'
        
        # Find all JSONL files in the benchmark directory for the specified language
        if args.language != 'all':
            benchmark_dir = f"benchmark/{args.language}"
            jsonl_files = find_jsonl_files(benchmark_dir)
            print(f"Found {len(jsonl_files)} JSONL files for {args.language} execution.")
        else:
            jsonl_files = []  # Will be populated per language in model_eval section
        
        # Filter files by category if specified
        if args.categories:
            categories = args.categories.split(',')
            filtered_files = []
            
            for file in jsonl_files:
                if any(category in file for category in categories):
                    filtered_files.append(file)
            
            if not filtered_files:
                print(f"No files matching the categories: {args.categories}")
                return
            
            print(f"Found {len(filtered_files)} files matching the categories: {args.categories}")
            jsonl_files = filtered_files
        
        # If a specific test ID is provided, filter for just that test case
        if args.id:
            print(f"Looking for test case with ID: {args.id}")
            # We'll collect the test case here if found
            found_test_case = None
            found_file_path = None
            
            # Search through all relevant files for the specified test ID
            for jsonl_file in jsonl_files:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            test_case = json.loads(line)
                            if str(test_case.get('id')) == str(args.id):
                                found_test_case = test_case
                                found_file_path = jsonl_file
                                print(f"Found test case with ID {args.id} in file {jsonl_file}")
                                break
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid JSON at line {line_num} in {jsonl_file}")
                
                if found_test_case:
                    break
            
            if not found_test_case:
                print(f"No test case found with ID: {args.id}")
                return
            
            # Set up a temporary JSONL file with just the one test case
            temp_jsonl = "temp_single_test.jsonl"
            with open(temp_jsonl, 'w', encoding='utf-8') as f:
                f.write(json.dumps(found_test_case) + '\n')
            
            try:
                # Execute just this single test case
                results = execute_test_cases(
                    [temp_jsonl],
                    language=args.language,
                    verbose=args.verbose,
                    report_file=args.report
                )
                
                # Print source file information
                print(f"\nTest case ID {args.id} from file: {found_file_path}")
                
                return
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_jsonl):
                    os.remove(temp_jsonl)
        
        # If model evaluation is requested
        if args.model_eval:
            print("Evaluating model completions against benchmark test cases...")
            # Filter models if specified
            models_filter = args.models.split(',') if args.models else None
            
            # If language is 'all', process all languages
            if args.language == 'all':
                all_languages = ['python', 'javascript', 'c_sharp', 'cpp', 'typescript', 'java']
                overall_results = {
                    "total_cases": 0,
                    "models": {},
                    "categories": {},
                    "languages": {},
                    "pass_at_k": args.pass_at_k
                }
                
                for lang in all_languages:
                    print(f"\n{'='*60}")
                    print(f"Processing language: {lang.upper()}")
                    print(f"{'='*60}")
                    
                    # Find benchmark files for this language
                    lang_benchmark_dir = f"benchmark/{lang}"
                    lang_jsonl_files = find_jsonl_files(lang_benchmark_dir)
                    
                    if not lang_jsonl_files:
                        print(f"No benchmark files found for {lang}, skipping...")
                        continue
                    
                    # Set models_dir for this language
                    # Always append language subdirectory when processing all languages
                    lang_models_dir = f"{args.models_dir}/{lang}"
                    
                    if not os.path.exists(lang_models_dir):
                        print(f"No completions directory found at {lang_models_dir}, skipping...")
                        continue
                        
                    print(f"Found {len(lang_jsonl_files)} JSONL files for {lang} execution.")
                    print(f"Looking for completions in: {lang_models_dir}")
                    
                    # Execute for this language
                    lang_report_file = args.report.replace('.txt', f'_{lang}.txt') if args.report and args.report != "benchmark_report.txt" else None
                    lang_json_file = args.json_output.replace('.json', f'_{lang}.json') if args.json_output else None
                    
                    lang_results = execute_model_completions(
                        lang_jsonl_files,
                        models_dir=lang_models_dir,
                        verbose=args.verbose,
                        report_file=lang_report_file,
                        models_filter=models_filter,
                        json_output_file=lang_json_file,
                        pass_at_k=args.pass_at_k
                    )
                    
                    # Aggregate results
                    overall_results["languages"][lang] = lang_results
                    overall_results["total_cases"] += lang_results.get("total_cases", 0)
                    
                    # Aggregate model results
                    for model_name, model_data in lang_results.get("models", {}).items():
                        if model_name not in overall_results["models"]:
                            overall_results["models"][model_name] = {
                                "successful_cases": 0,
                                "failed_cases": 0,
                                "timeout_cases": 0,
                                "pass_at_k_cases": []
                            }
                        overall_results["models"][model_name]["successful_cases"] += model_data.get("successful_cases", 0)
                        overall_results["models"][model_name]["failed_cases"] += model_data.get("failed_cases", 0)
                        overall_results["models"][model_name]["timeout_cases"] += model_data.get("timeout_cases", 0)
                        overall_results["models"][model_name]["pass_at_k_cases"].extend(model_data.get("pass_at_k_cases", []))
                    
                    # Aggregate category results
                    for category, cat_data in lang_results.get("categories", {}).items():
                        if category not in overall_results["categories"]:
                            overall_results["categories"][category] = {
                                "total_cases": 0,
                                "models": {}
                            }
                        overall_results["categories"][category]["total_cases"] += cat_data.get("total_cases", 0)
                        
                        for model_name, model_cat_data in cat_data.get("models", {}).items():
                            if model_name not in overall_results["categories"][category]["models"]:
                                overall_results["categories"][category]["models"][model_name] = {
                                    "successful_cases": 0,
                                    "failed_cases": 0,
                                    "timeout_cases": 0,
                                    "pass_at_k_cases": []
                                }
                            overall_results["categories"][category]["models"][model_name]["successful_cases"] += model_cat_data.get("successful_cases", 0)
                            overall_results["categories"][category]["models"][model_name]["failed_cases"] += model_cat_data.get("failed_cases", 0)
                            overall_results["categories"][category]["models"][model_name]["timeout_cases"] += model_cat_data.get("timeout_cases", 0)
                            overall_results["categories"][category]["models"][model_name]["pass_at_k_cases"].extend(model_cat_data.get("pass_at_k_cases", []))
                
                # Print overall summary
                print(f"\n{'='*80}")
                print("OVERALL SUMMARY (ALL LANGUAGES)")
                print(f"{'='*80}")
                print(f"Total test cases: {overall_results['total_cases']}")
                
                print(f"\nRESULTS BY MODEL (OVERALL):")
                for model_name, model_data in overall_results["models"].items():
                    total = model_data["successful_cases"] + model_data["failed_cases"]
                    if total > 0:
                        pass_at_k_scores = model_data["pass_at_k_cases"]
                        avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                        success_rate = model_data["successful_cases"] / total * 100
                        print(f"\n{model_name}:")
                        print(f"  Pass@{args.pass_at_k}: {avg_pass_at_k:.3f}")
                        print(f"  Success rate: {success_rate:.2f}%")
                        print(f"  Successful: {model_data['successful_cases']}/{total}")
                
                print(f"\nRESULTS BY CATEGORY (OVERALL):")
                for category, cat_data in overall_results["categories"].items():
                    print(f"\nCategory: {category}")
                    print(f"  Total cases: {cat_data['total_cases']}")
                    for model_name, model_cat_data in cat_data["models"].items():
                        total = model_cat_data["successful_cases"] + model_cat_data["failed_cases"]
                        if total > 0:
                            pass_at_k_scores = model_cat_data["pass_at_k_cases"]
                            avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                            success_rate = model_cat_data["successful_cases"] / total * 100
                            print(f"    {model_name}: Pass@{args.pass_at_k}={avg_pass_at_k:.3f}, Success={success_rate:.1f}%")
                
                print(f"\nRESULTS BY LANGUAGE:")
                for lang, lang_data in overall_results["languages"].items():
                    print(f"\n{lang.upper()}:")
                    for model_name, model_data in lang_data.get("models", {}).items():
                        total = model_data["successful_cases"] + model_data["failed_cases"]
                        if total > 0:
                            pass_at_k_scores = model_data["pass_at_k_cases"]
                            avg_pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0.0
                            success_rate = model_data["successful_cases"] / total * 100
                            print(f"  {model_name}: Pass@{args.pass_at_k}={avg_pass_at_k:.3f}, Success={success_rate:.1f}% ({model_data['successful_cases']}/{total})")
                
                # Save overall JSON if specified
                if args.json_output:
                    with open(args.json_output, 'w') as f:
                        json.dump(overall_results, f, indent=2)
                    print(f"\nOverall JSON results saved to {args.json_output}")
                
                return
            
            # Single language evaluation (existing code)
            execute_model_completions(
                jsonl_files,
                models_dir=args.models_dir,
                verbose=args.verbose,
                report_file=args.report,
                models_filter=models_filter,
                json_output_file=args.json_output,
                pass_at_k=args.pass_at_k
            )
            return
        
        # Otherwise, execute golden completions as before
        execute_test_cases(
            jsonl_files,
            language=args.language,
            verbose=args.verbose,
            report_file=args.report
        )
        return
    
    # Generate benchmark test cases if --generate is used
    if args.generate:
        valid_completions = 0
        total_completions = args.completions
        LANGUAGE = args.language.lower()
        
        # Determine prompt module based on language
        prompt_module = None
        if LANGUAGE == 'python':
            prompt_module = python_prompts
        elif LANGUAGE == 'javascript':
            prompt_module = javascript_prompts
        elif LANGUAGE == 'c_sharp':
            prompt_module = c_sharp_prompts
        elif LANGUAGE == 'cpp':
            prompt_module = cpp_prompts
        elif LANGUAGE == 'typescript':
            prompt_module = typescript_prompts
        elif LANGUAGE == 'java':
            prompt_module = java_prompts
        else:
            print(f"Unsupported language: {LANGUAGE}")
            return
        
        # Get the correct prompts based on prompt type
        prompt_type = args.prompt_type.upper()
        try:
            SYSTEM_PROMPT = getattr(prompt_module, f"{prompt_type}_SYSTEM_PROMPT")
            USER_PROMPT = getattr(prompt_module, f"{prompt_type}_USER_PROMPT")
        except AttributeError:
            print(f"Prompt type '{args.prompt_type}' not found for language '{LANGUAGE}'")
            print("Available prompt types for this language:")
            for attr in dir(prompt_module):
                if attr.endswith("_SYSTEM_PROMPT"):
                    print(f"  - {attr.replace('_SYSTEM_PROMPT', '').lower()}")
            return
        
        # Set output file path
        if args.output:
            output_file = args.output
        else:
            # Create default path: benchmark/{language}/{prompt_type}/{prompt_type}.jsonl
            prompt_type_dir = args.prompt_type.lower()
            os.makedirs(f"benchmark/{LANGUAGE}/{prompt_type_dir}", exist_ok=True)
            output_file = f"benchmark/{LANGUAGE}/{prompt_type_dir}/{prompt_type_dir}.jsonl"
        
        print(f"Generating {total_completions} benchmark test cases for {LANGUAGE} using {args.prompt_type} prompts")
        print(f"Output will be saved to: {output_file}")
        
        while valid_completions < total_completions:
            try:
                # Prompt the AI with a message
                messages = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": USER_PROMPT
                    }
                ]

                completion = client.chat.completions.create(  
                    model=deployment,  
                    messages=messages,
                    max_tokens=4000,  
                    temperature=0.7,  
                    top_p=0.95,  
                    frequency_penalty=0,  
                    presence_penalty=0,
                    stop=None,  
                    stream=False  
                )

                response_content = completion.choices[0].message.content
                results = validate_test_case(response_content, LANGUAGE)

                if results["syntax_valid"]:
                    # Append to JSONL file
                    with open(output_file, 'a') as f:
                        cleaned_response = response_content.replace("```json", "").replace("```", "").strip()
                        json_obj = json.loads(cleaned_response)
                        json_line = json.dumps(json_obj)

                        f.write(json_line + '\n')
                    
                    valid_completions += 1
                    print(f"Valid completion {valid_completions}/{total_completions} saved")
                    
                    # Display the test case and validation results
                    print("\nTest Case Details:")
                    display_test_case(response_content)
                    display_validation_results(response_content, LANGUAGE)
                else:
                    print("Invalid syntax - retrying...")

            except Exception as e:
                print(f"Error occurred: {str(e)}")
                continue
        
        print(f"\nCompleted! {valid_completions} valid completions have been saved to {output_file}")

        # Process the generated JSONL file
        output_txt_file = output_file.replace('.jsonl', '_formatted.txt')
        print(f"\nGenerating formatted output in {output_txt_file}...")
        process_jsonl_file(output_file, output_txt_file)
        print("Formatting complete!")
        return
        
    # If neither --execute nor --generate are specified, print help
    parser.print_help()

if __name__ == "__main__":
    main()
