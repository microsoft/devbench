"""
Compute Pass@1 for all paper models from saved completions.

Reads completion JSONL files from ../completions/{language}/{category}/ and
benchmark tasks from ../benchmark/{language}/{category}/, executes each
completion against the task's hidden assertions, and computes Pass@1 scores.

Outputs summary tables matching paper Tables 5 (by category) and 9 (by language),
plus a detailed JSON file with per-task results.

Usage:
  python compute_pass_at_1.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Paper models only
MODELS = ['gpt-5.5', 'gpt-5.4-mini', 'gpt-5.4-nano', 'claude-opus-4-7',
          'claude-sonnet-4-6', 'deepseek-v4-pro', 'llama-4-maverick',
          'mistral-medium-3.5', 'qwen3.6-27b']
LANGUAGES = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c_sharp']
CATEGORIES = ['api_usage', 'code2NL_NL2code', 'code_purpose_understanding',
              'low_context', 'pattern_matching', 'syntax_completion']


def pass_at_k(n, c, k=1):
    """Compute pass@k from n samples with c correct."""
    if n - c < k:
        return 1.0
    result = 1.0
    for i in range(k):
        result *= (n - c - i) / (n - i)
    return 1.0 - result


# ---------------------------------------------------------------------------
# Language runners with proper assertion injection
# (ported from the battle-tested eval_poc.py)
# ---------------------------------------------------------------------------

def _extract_code(text):
    """Extract code from markdown code blocks if present.

    Robust to any language tag (including ``` c_sharp ```), unclosed/truncated
    fences (e.g. cut off at max_tokens or reasoning-model prose), and stray lone
    fence lines. A naive enumerated-tag regex silently left ``` c_sharp ``` fences
    in the code, which then failed to compile and was scored as a false 0.
    """
    if not text:
        return text
    # 1) A properly closed fenced block with ANY language tag (or none).
    m = re.search(r'```[^\n]*\n(.*?)```', text, re.DOTALL)
    if m:
        code = m.group(1)
    else:
        # 2) Opening fence but no close (truncated at max_tokens / reasoning prose).
        m = re.search(r'```[^\n]*\n(.*)$', text, re.DOTALL)
        code = m.group(1) if m else text
    # 3) Remove any leftover lone fence lines (e.g. a stray trailing ``` ).
    code = re.sub(r'^\s*```[^\n]*$', '', code, flags=re.MULTILINE)
    return code


def run_test_python(prefix, completion, suffix, assertions, timeout=30):
    combined = f"{prefix}{completion}{suffix}\n{assertions}"
    temp_dir = tempfile.mkdtemp(prefix="py_eval_")
    py_file = os.path.join(temp_dir, "test.py")
    try:
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write("import matplotlib\nmatplotlib.use('Agg')\n" + combined)
        r = subprocess.run(
            [sys.executable, py_file],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "MPLBACKEND": "Agg"}
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout)[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _find_tool(name, env_var=None):
    """Find a tool binary: check env var override, then PATH, then common locations."""
    if env_var:
        val = os.environ.get(env_var)
        if val and os.path.isfile(val):
            return val
    p = shutil.which(name)
    if p:
        return p
    if name == "node":
        nvm = os.path.expanduser("~/.nvm/versions/node")
        if os.path.isdir(nvm):
            for v in sorted(os.listdir(nvm), reverse=True):
                candidate = os.path.join(nvm, v, "bin", "node")
                if os.path.isfile(candidate):
                    return candidate
    return name


_node_path = None
_javac_path = None
_java_path = None


def run_test_js(prefix, completion, suffix, assertions, timeout=30):
    global _node_path
    if _node_path is None:
        _node_path = _find_tool("node", "NODE_PATH")
    combined = f"{prefix}{completion}{suffix}\n{assertions}"
    temp_dir = tempfile.mkdtemp(prefix="js_eval_")
    js_file = os.path.join(temp_dir, "test.js")
    try:
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(combined)
        r = subprocess.run(
            [_node_path, js_file],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout)[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_test_ts(prefix, completion, suffix, assertions, timeout=30):
    global _node_path
    if _node_path is None:
        _node_path = _find_tool("node", "NODE_PATH")
    combined = f"{prefix}{completion}{suffix}\n{assertions}"
    temp_dir = tempfile.mkdtemp(prefix="ts_eval_")
    ts_file = os.path.join(temp_dir, "test.ts")
    js_file = os.path.join(temp_dir, "test.js")
    try:
        subprocess.run(
            ["npm", "install", "typescript@5", "@types/node"],
            capture_output=True, cwd=temp_dir, timeout=30
        )
        with open(ts_file, 'w', encoding='utf-8') as f:
            f.write(combined)
        npx = shutil.which("npx") or "npx"
        comp = subprocess.run(
            [npx, "tsc", ts_file, "--types", "node",
             "--esModuleInterop", "--moduleResolution", "node",
             "--target", "es2020", "--module", "commonjs", "--outDir", temp_dir],
            capture_output=True, text=True, timeout=30, cwd=temp_dir
        )
        if comp.returncode != 0:
            return False, f"Compile error: {comp.stderr[:300]}"
        r = subprocess.run(
            [_node_path, js_file],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout)[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- Java assertion injection ---

def _find_main_end_java(code):
    """Find the closing brace of main(), skipping string/char literals."""
    main_match = re.search(r'public\s+static\s+void\s+main\s*\(', code)
    if not main_match:
        return -1
    brace_start = code.find('{', main_match.start())
    if brace_start == -1:
        return -1
    depth = 0
    in_string = False
    in_char = False
    escaped = False
    for i in range(brace_start, len(code)):
        c = code[i]
        if escaped:
            escaped = False
            continue
        if c == '\\':
            escaped = True
            continue
        if c == '"' and not in_char:
            in_string = not in_string
            continue
        if c == "'" and not in_string:
            in_char = not in_char
            continue
        if in_string or in_char:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1


def _inject_assertions_java(base, assertions):
    """Inject assertions: try static {} first (compile check), fall back to main()-end."""
    idx = base.rfind('}')
    if idx != -1:
        static_ver = base[:idx] + "\nstatic {\n" + assertions + "\n}\n}\n"
        class_match = re.search(r'public\s+class\s+(\w+)', static_ver)
        cn = class_match.group(1) if class_match else "TestCase"
        javac = _find_tool("javac", "JAVAC_PATH")
        td = tempfile.mkdtemp(prefix="java_chk_")
        jf = os.path.join(td, f"{cn}.java")
        try:
            with open(jf, 'w') as f:
                f.write(static_ver)
            r = subprocess.run([javac, jf], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return static_ver
        except Exception:
            pass
        finally:
            shutil.rmtree(td, ignore_errors=True)
    main_end = _find_main_end_java(base)
    if main_end != -1:
        return base[:main_end] + "\n" + assertions + "\n" + base[main_end:]
    if idx != -1:
        return base[:idx] + "\nstatic {\n" + assertions + "\n}\n}\n"
    return base + "\n" + assertions


def run_test_java(prefix, completion, suffix, assertions, timeout=30):
    base = f"{prefix}{completion}{suffix}"
    if assertions.strip():
        combined = _inject_assertions_java(base, assertions)
    else:
        combined = base
    temp_dir = tempfile.mkdtemp(prefix="java_eval_")
    try:
        class_name = "TestCase"
        class_match = re.search(r'public\s+class\s+(\w+)', combined)
        if class_match:
            class_name = class_match.group(1)
        java_file = os.path.join(temp_dir, f"{class_name}.java")
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(combined)
        javac = _find_tool("javac", "JAVAC_PATH")
        java_bin = _find_tool("java", "JAVA_PATH")
        comp = subprocess.run(
            [javac, java_file],
            capture_output=True, text=True, timeout=timeout
        )
        if comp.returncode != 0:
            return False, f"Compile error: {comp.stderr[:300]}"
        r = subprocess.run(
            [java_bin, "-ea", "-cp", temp_dir, class_name],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout)[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- C++ assertion injection (skips comments during brace counting) ---

def _inject_assertions_cpp(code, assertions):
    main_match = re.search(r'\bint\s+main\s*\(', code)
    if not main_match:
        return code + f"\nint main() {{\n{assertions}\nreturn 0;\n}}\n"
    brace_start = code.find('{', main_match.start())
    if brace_start == -1:
        return code + f"\n{assertions}"
    depth = 0
    in_string = False
    in_char = False
    escaped = False
    main_end = -1
    last_top_level_return = -1
    i = brace_start
    while i < len(code):
        c = code[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if c == '\\' and (in_string or in_char):
            escaped = True
            i += 1
            continue
        if not in_string and not in_char:
            if c == '/' and i + 1 < len(code):
                if code[i + 1] == '/':
                    nl = code.find('\n', i + 2)
                    i = nl + 1 if nl != -1 else len(code)
                    continue
                if code[i + 1] == '*':
                    end = code.find('*/', i + 2)
                    i = end + 2 if end != -1 else len(code)
                    continue
        if c == '"' and not in_char:
            in_string = not in_string
            i += 1
            continue
        if c == "'" and not in_string:
            in_char = not in_char
            i += 1
            continue
        if in_string or in_char:
            i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                main_end = i
                break
        elif depth == 1 and code.startswith('return', i):
            before = code[i - 1] if i > 0 else ' '
            after = code[i + len('return')] if i + len('return') < len(code) else ' '
            if not (before.isalnum() or before == '_') and not (after.isalnum() or after == '_'):
                last_top_level_return = i
        i += 1
    if main_end == -1:
        return code + f"\n{assertions}"
    insert_at = last_top_level_return if last_top_level_return != -1 else main_end
    return code[:insert_at] + f"\n// Run assertions\n{assertions}\n" + code[insert_at:]


def _find_cpp_compiler():
    for compiler in ["g++", "clang++", "c++"]:
        path = shutil.which(compiler)
        if path:
            return path
    return "g++"


_cpp_compiler = None


def run_test_cpp(prefix, completion, suffix, assertions, timeout=60):
    global _cpp_compiler
    if _cpp_compiler is None:
        _cpp_compiler = _find_cpp_compiler()
    combined = f"{prefix}{completion}{suffix}"
    if assertions.strip():
        combined = _inject_assertions_cpp(combined, assertions)
    temp_dir = tempfile.mkdtemp(prefix="cpp_eval_")
    cpp_file = os.path.join(temp_dir, "test.cpp")
    exe_file = os.path.join(temp_dir, "test")
    try:
        with open(cpp_file, 'w', encoding='utf-8') as f:
            f.write(combined)
        comp = subprocess.run(
            [_cpp_compiler, "-std=c++17", "-O2", "-o", exe_file, cpp_file, "-lpthread"],
            capture_output=True, text=True, timeout=timeout
        )
        if comp.returncode != 0:
            return False, f"Compile error: {comp.stderr[:300]}"
        r = subprocess.run(
            [exe_file], capture_output=True, text=True, timeout=timeout
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout)[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- C# assertion injection (handles comments, verbatim/interpolated strings) ---

def _inject_assertions_csharp(code, assertions):
    main_match = re.search(r'\b(?:static\s+(?:void|int|async\s+Task(?:<int>)?)\s+Main)\s*\(', code)
    if not main_match:
        return code + f"\n// Run assertions\n{assertions}\n"
    brace_start = code.find('{', main_match.start())
    if brace_start == -1:
        return code + f"\n{assertions}"
    depth = 0
    in_string = False
    in_verbatim = False
    in_char = False
    escaped = False
    main_end = -1
    last_top_level_return = -1
    i = brace_start
    while i < len(code):
        c = code[i]
        if in_verbatim:
            if c == '"':
                if i + 1 < len(code) and code[i + 1] == '"':
                    i += 2
                    continue
                in_verbatim = False
            i += 1
            continue
        if escaped:
            escaped = False
            i += 1
            continue
        if c == '\\' and (in_string or in_char):
            escaped = True
            i += 1
            continue
        if not in_string and not in_char:
            if c == '/' and i + 1 < len(code):
                if code[i + 1] == '/':
                    nl = code.find('\n', i + 2)
                    i = nl + 1 if nl != -1 else len(code)
                    continue
                if code[i + 1] == '*':
                    end = code.find('*/', i + 2)
                    i = end + 2 if end != -1 else len(code)
                    continue
            if c in ('@', '$') and i + 1 < len(code) and code[i + 1] == '"':
                in_verbatim = True
                i += 2
                continue
            if c == '$' and i + 1 < len(code) and code[i + 1] == '@' and i + 2 < len(code) and code[i + 2] == '"':
                in_verbatim = True
                i += 3
                continue
        if c == '"' and not in_char:
            in_string = not in_string
            i += 1
            continue
        if c == '\'' and not in_string:
            in_char = not in_char
            i += 1
            continue
        if in_string or in_char:
            i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                main_end = i
                break
        elif depth == 1 and code.startswith('return', i):
            before = code[i - 1] if i > 0 else ' '
            after = code[i + len('return')] if i + len('return') < len(code) else ' '
            if not (before.isalnum() or before == '_') and not (after.isalnum() or after == '_'):
                last_top_level_return = i
        i += 1
    if main_end == -1:
        return code + f"\n{assertions}"
    insert_at = last_top_level_return if last_top_level_return != -1 else main_end
    return code[:insert_at] + f"\n// Run assertions\n{assertions}\n" + code[insert_at:]


def run_test_csharp(prefix, completion, suffix, assertions, timeout=60):
    combined = f"{prefix}{completion}{suffix}"
    if assertions.strip():
        combined = _inject_assertions_csharp(combined, assertions)
    temp_dir = tempfile.mkdtemp(prefix="csharp_eval_")
    try:
        csproj = '''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>'''
        with open(os.path.join(temp_dir, "Test.csproj"), 'w') as f:
            f.write(csproj)
        with open(os.path.join(temp_dir, "Program.cs"), 'w', encoding='utf-8') as f:
            f.write(combined)
        r = subprocess.run(
            ["dotnet", "run", "--project", temp_dir],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode != 0:
            return False, (r.stderr or r.stdout)[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- Dispatcher ---

def run_test(lang, prefix, completion, suffix, assertions, timeout=30):
    completion = _extract_code(completion)
    if lang == "python":
        return run_test_python(prefix, completion, suffix, assertions, timeout=timeout)
    elif lang == "javascript":
        return run_test_js(prefix, completion, suffix, assertions, timeout=timeout)
    elif lang == "typescript":
        return run_test_ts(prefix, completion, suffix, assertions, timeout=timeout)
    elif lang == "java":
        return run_test_java(prefix, completion, suffix, assertions, timeout=timeout)
    elif lang == "cpp":
        return run_test_cpp(prefix, completion, suffix, assertions, timeout=60)
    elif lang in ("c_sharp", "csharp"):
        return run_test_csharp(prefix, completion, suffix, assertions, timeout=60)
    else:
        return False, f"Unknown language: {lang}"


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def main():
    base = os.path.dirname(os.path.abspath(__file__))

    all_results = {
        "models": {},
        "summary": {}
    }

    for model in MODELS:
        print(f"\n{'='*70}", flush=True)
        print(f"Model: {model}", flush=True)
        print(f"{'='*70}", flush=True)

        model_data = {
            "successful_cases": 0,
            "failed_cases": 0,
            "timeout_cases": 0,
            "total_completions": 0,
            "correct_completions": 0,
            "pass_at_k_cases": [],
            "failures": [],
            "categories": {},
            "languages": {},
            "test_cases": []
        }

        for lang in LANGUAGES:
            if lang not in model_data["languages"]:
                model_data["languages"][lang] = {
                    "successful_cases": 0, "failed_cases": 0, "timeout_cases": 0,
                    "total_completions": 0, "correct_completions": 0, "pass_at_k_cases": []
                }

            for cat in CATEGORIES:
                comp_path = os.path.join(base, '..', 'completions', lang, cat, f'{cat}-{model}.jsonl')
                bench_path = os.path.join(base, '..', 'benchmark', lang, cat, f'{cat}.jsonl')

                if not os.path.exists(comp_path):
                    continue

                if cat not in model_data["categories"]:
                    model_data["categories"][cat] = {
                        "successful_cases": 0, "failed_cases": 0, "timeout_cases": 0,
                        "total_completions": 0, "correct_completions": 0, "pass_at_k_cases": []
                    }

                with open(bench_path) as f:
                    bench = {}
                    for line in f:
                        t = json.loads(line)
                        bench[t['id']] = t

                with open(comp_path) as f:
                    comps = [json.loads(l) for l in f]

                for rec in comps:
                    tid = rec['id']
                    task = bench[tid]
                    correct = 0
                    completion_results = []

                    for comp_idx, c in enumerate(rec.get(f'{model}_completions', [])):
                        try:
                            ok, err = run_test(
                                lang, task['prefix'], c, task['suffix'],
                                task.get('assertions', '')
                            )
                        except Exception as e:
                            ok = False
                            err = str(e)

                        is_timeout = "timeout" in err.lower() if err else False

                        completion_results.append({
                            "completion_index": comp_idx,
                            "success": ok,
                            "error": err if not ok else None,
                            "is_timeout": is_timeout
                        })

                        if ok:
                            correct += 1

                    total = len(rec.get(f'{model}_completions', []))
                    p1 = pass_at_k(total, correct, 1)
                    overall_success = correct > 0
                    has_timeout = any(cr["is_timeout"] for cr in completion_results if not cr["success"])

                    test_case_result = {
                        "test_id": tid,
                        "language": lang,
                        "category": cat,
                        "success": overall_success,
                        "total_completions": total,
                        "correct_completions": correct,
                        "pass_at_k_score": p1,
                        "completion_results": completion_results
                    }
                    model_data["test_cases"].append(test_case_result)

                    model_data["pass_at_k_cases"].append(p1)
                    model_data["total_completions"] += total
                    model_data["correct_completions"] += correct
                    model_data["categories"][cat]["pass_at_k_cases"].append(p1)
                    model_data["categories"][cat]["total_completions"] += total
                    model_data["categories"][cat]["correct_completions"] += correct
                    model_data["languages"][lang]["pass_at_k_cases"].append(p1)
                    model_data["languages"][lang]["total_completions"] += total
                    model_data["languages"][lang]["correct_completions"] += correct

                    if overall_success:
                        model_data["successful_cases"] += 1
                        model_data["categories"][cat]["successful_cases"] += 1
                        model_data["languages"][lang]["successful_cases"] += 1
                    else:
                        model_data["failed_cases"] += 1
                        model_data["categories"][cat]["failed_cases"] += 1
                        model_data["languages"][lang]["failed_cases"] += 1
                        if has_timeout:
                            model_data["timeout_cases"] += 1
                            model_data["categories"][cat]["timeout_cases"] += 1
                            model_data["languages"][lang]["timeout_cases"] += 1
                        first_error = next((cr["error"] for cr in completion_results if cr["error"]), "Unknown")
                        model_data["failures"].append({
                            "language": lang,
                            "category": cat,
                            "test_id": tid,
                            "error": first_error[:200],
                            "is_timeout": has_timeout,
                            "correct_completions": correct,
                            "total_completions": total
                        })

                cat_scores = model_data["categories"][cat]["pass_at_k_cases"]
                cat_p1 = sum(cat_scores) / len(cat_scores) * 100 if cat_scores else 0
                print(f"  {lang}/{cat}: {cat_p1:.1f}%", flush=True)

        overall_p1 = sum(model_data["pass_at_k_cases"]) / len(model_data["pass_at_k_cases"]) * 100 if model_data["pass_at_k_cases"] else 0

        cat_summary = {}
        for cat in CATEGORIES:
            if cat in model_data["categories"]:
                scores = model_data["categories"][cat]["pass_at_k_cases"]
                cat_summary[cat] = round(sum(scores) / len(scores) * 100, 1) if scores else 0

        lang_summary = {}
        for lang in LANGUAGES:
            if lang in model_data["languages"]:
                scores = model_data["languages"][lang]["pass_at_k_cases"]
                lang_summary[lang] = round(sum(scores) / len(scores) * 100, 1) if scores else 0

        model_data["overall_pass_at_1"] = round(overall_p1, 1)
        model_data["category_pass_at_1"] = cat_summary
        model_data["language_pass_at_1"] = lang_summary
        model_data["task_count"] = len(model_data["pass_at_k_cases"])

        all_results["models"][model] = model_data
        print(f"\n  OVERALL: {overall_p1:.1f}% ({len(model_data['pass_at_k_cases'])} tasks)", flush=True)

    # Build summary tables
    table5 = {}
    for model in MODELS:
        if model not in all_results["models"]:
            continue
        r = all_results["models"][model]
        table5[model] = {"overall": r["overall_pass_at_1"]}
        table5[model].update(r["category_pass_at_1"])

    table9 = {}
    for model in MODELS:
        if model not in all_results["models"]:
            continue
        r = all_results["models"][model]
        table9[model] = {"overall": r["overall_pass_at_1"]}
        table9[model].update(r["language_pass_at_1"])

    all_results["summary"]["table5_pass_at_1_by_category"] = table5
    all_results["summary"]["table9_pass_at_1_by_language"] = table9

    output_path = os.path.join(base, 'pass_at_1_results.json')
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nDetailed results saved to {output_path}")

    # Print Table 5
    print(f"\n{'='*100}")
    print(f"TABLE 5: Pass@1 by category")
    print(f"{'='*100}")
    print(f"{'Model':<20} {'Overall':>8}", end='')
    for cat in CATEGORIES:
        print(f" {cat[:12]:>12}", end='')
    print()
    print('-' * 100)
    for model in MODELS:
        if model not in table5:
            continue
        r = table5[model]
        print(f"{model:<20} {r['overall']:>7.1f}%", end='')
        for cat in CATEGORIES:
            val = r.get(cat, '-')
            if isinstance(val, (int, float)):
                print(f" {val:>11.1f}%", end='')
            else:
                print(f" {val:>12}", end='')
        print()

    # Print Table 9
    print(f"\n{'='*100}")
    print(f"TABLE 9: Pass@1 by language")
    print(f"{'='*100}")
    print(f"{'Model':<20} {'Overall':>8}", end='')
    for lang in LANGUAGES:
        print(f" {lang:>12}", end='')
    print()
    print('-' * 100)
    for model in MODELS:
        if model not in table9:
            continue
        r = table9[model]
        print(f"{model:<20} {r['overall']:>7.1f}%", end='')
        for lang in LANGUAGES:
            val = r.get(lang, '-')
            if isinstance(val, (int, float)):
                print(f" {val:>11.1f}%", end='')
            else:
                print(f" {val:>12}", end='')
        print()


if __name__ == "__main__":
    main()
