#!/usr/bin/env python3
"""
Simple CLI test client for Judge0 ARM64 Execution Engine.
Prints clear, human-readable execution results with colors and clean formatting.
"""
import sys
import json
import urllib.request
import urllib.error

LANGUAGES = {
    "python": (71, "Python 3", "print('Hello from Python 3!')\nprint(f'Sum: {sum(range(1, 11))}')"),
    "c": (50, "C (GCC)", '#include <stdio.h>\nint main() {\n    printf("Hello from C GCC!\\n");\n    return 0;\n}'),
    "cpp": (54, "C++ (GCC)", '#include <iostream>\nint main() {\n    std::cout << "Hello from C++ GCC!" << std::endl;\n    return 0;\n}'),
    "js": (63, "JavaScript (Node.js)", 'const arr = [1, 2, 3, 4, 5];\nconsole.log("Hello from JavaScript! Sum =", arr.reduce((a, b) => a + b, 0));'),
    "java": (62, "Java (OpenJDK)", 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello from Java OpenJDK on ARM64!");\n    }\n}'),
    "bash": (46, "Bash", 'echo "Hello from Bash!"\necho "Kernel: $(uname -s) $(uname -m)"'),
}


__test__ = False

def run_language_test(server_url: str, lang_key: str):
    if lang_key not in LANGUAGES:
        print(f"Unknown language '{lang_key}'. Choose from: {', '.join(LANGUAGES.keys())}")
        return

    lang_id, lang_name, sample_code = LANGUAGES[lang_key]

    print("\n" + "=" * 60)
    print(f"  Testing Language: {lang_name} (ID: {lang_id})")
    print("=" * 60)

    url = f"{server_url.rstrip('/')}/submissions?wait=true"
    payload = {
        "language_id": lang_id,
        "source_code": sample_code,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode("utf-8"))

            status_desc = res_json.get("status", {}).get("description", "Unknown")
            status_id = res_json.get("status_id") or res_json.get("status", {}).get("id")
            stdout = res_json.get("stdout")
            stderr = res_json.get("stderr")
            compile_output = res_json.get("compile_output")
            time_sec = res_json.get("time")
            memory_kb = res_json.get("memory")

            # Formatted Output
            status_symbol = "✅" if status_id == 3 else "❌"
            print(f"  Status:         {status_symbol} {status_desc} (ID: {status_id})")
            print(f"  Execution Time: {time_sec}s")
            print(f"  Peak Memory:    {memory_kb} KB")
            print("-" * 60)

            if stdout:
                print("  [STDOUT]:")
                for line in stdout.strip().split("\n"):
                    print(f"    {line}")

            if stderr:
                print("  [STDERR]:")
                for line in stderr.strip().split("\n"):
                    print(f"    {line}")

            if compile_output:
                print("  [COMPILER OUTPUT]:")
                for line in compile_output.strip().split("\n"):
                    print(f"    {line}")

            print("=" * 60)

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")


def main():
    server_url = "http://localhost:2358"
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        server_url = sys.argv[1]
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]

    if not args or "all" in args:
        print(f"Running full language matrix test against {server_url} ...")
        for key in ["python", "c", "cpp", "js", "java", "bash"]:
            run_language_test(server_url, key)
    else:
        for key in args:
            run_language_test(server_url, key.lower())


if __name__ == "__main__":
    main()
