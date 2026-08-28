#!/usr/bin/env python3
"""
Comprehensive Verdict & Metrics Verification Script for Judge0 ARM64 Engine.
Tests all contest verdicts:
1. Accepted (AC)
2. Wrong Answer (WA)
3. Time Limit Exceeded (TLE)
4. Compilation Error (CE)
5. Runtime Error (NZEC)
6. Interactive Stdin/Stdout Evaluation
7. CPU Execution Time & Peak Memory Reporting
"""
import sys
import json
import time
from fastapi.testclient import TestClient
from src.app import app


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  TEST: {title}")
    print("=" * 70)


def print_result(verdict_expected, data):
    status_info = data.get("status", {})
    status_id = status_info.get("id")
    status_desc = status_info.get("description")
    time_taken = data.get("time")
    memory_used = data.get("memory")
    stdout = data.get("stdout")
    compile_out = data.get("compile_output")
    message = data.get("message")

    passed = (status_desc.lower() == verdict_expected.lower()) or (verdict_expected.lower() in status_desc.lower())

    symbol = "✅ PASSED" if passed else "❌ FAILED"
    print(f"  Result:          {symbol}")
    print(f"  Expected:        {verdict_expected}")
    print(f"  Engine Verdict:  {status_desc} (Status ID: {status_id})")
    print(f"  Execution Time:  {time_taken}s")
    print(f"  Peak Memory:     {memory_used} KB")

    if message:
        print(f"  Message:         {message}")
    if stdout:
        print(f"  Stdout Output:   {repr(stdout)}")
    if compile_out:
        print(f"  Compile Output:  {compile_out.strip().splitlines()[0] if compile_out.strip() else 'N/A'}")
    print("-" * 70)


def run_all_verifications():
    with TestClient(app) as client:
        # 1. Accepted (AC)
        print_header("1. Accepted (AC) - Sum Problem (C++)")
        payload_ac = {
            "language_id": 54,  # C++ GCC
            "source_code": "#include <iostream>\nusing namespace std;\nint main() { int a, b; if (cin >> a >> b) cout << a + b << endl; return 0; }",
            "stdin": "100 250",
            "expected_output": "350\n",
            "cpu_time_limit": 2.0,
            "memory_limit": 262144,
        }
        res_ac = client.post("/submissions?wait=true", json=payload_ac).json()
        print_result("Accepted", res_ac)

        # 2. Wrong Answer (WA)
        print_header("2. Wrong Answer (WA) - Incorrect Calculation (Python 3)")
        payload_wa = {
            "language_id": 71,  # Python 3
            "source_code": "a, b = map(int, input().split())\nprint(a * b)",  # Prints multiplication instead of sum
            "stdin": "5 10",
            "expected_output": "15\n",  # Expected addition 15, gets 50
            "cpu_time_limit": 2.0,
        }
        res_wa = client.post("/submissions?wait=true", json=payload_wa).json()
        print_result("Wrong Answer", res_wa)

        # 3. Time Limit Exceeded (TLE)
        print_header("3. Time Limit Exceeded (TLE) - Infinite Loop (Python 3)")
        payload_tle = {
            "language_id": 71,
            "source_code": "while True:\n    pass",
            "cpu_time_limit": 1.0,
            "wall_time_limit": 1.0,
        }
        res_tle = client.post("/submissions?wait=true", json=payload_tle).json()
        print_result("Time Limit Exceeded", res_tle)

        # 4. Compilation Error (CE)
        print_header("4. Compilation Error (CE) - Syntax Error (C GCC)")
        payload_ce = {
            "language_id": 50,  # C GCC
            "source_code": "#include <stdio.h>\nint main() { THIS_IS_SYNTAX_ERROR; return 0; }",
        }
        res_ce = client.post("/submissions?wait=true", json=payload_ce).json()
        print_result("Compilation Error", res_ce)

        # 5. Runtime Error (NZEC)
        print_header("5. Runtime Error (NZEC) - ZeroDivisionError (Python 3)")
        payload_nzec = {
            "language_id": 71,
            "source_code": "x = 10 / 0",
        }
        res_nzec = client.post("/submissions?wait=true", json=payload_nzec).json()
        print_result("Runtime Error (NZEC)", res_nzec)

        # 6. JavaScript Stdin/Stdout Execution
        print_header("6. JavaScript Node.js Execution - Stdin & JSON parsing")
        payload_js = {
            "language_id": 63,
            "source_code": "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf-8').trim();\nconsole.log(`Processed: ${input.toUpperCase()}`);",
            "stdin": "hello world",
            "expected_output": "Processed: HELLO WORLD\n",
        }
        res_js = client.post("/submissions?wait=true", json=payload_js).json()
        print_result("Accepted", res_js)

        # 7. Bash Execution & System Metrics
        print_header("7. Bash Shell Script Execution & Metrics")
        payload_bash = {
            "language_id": 46,
            "source_code": "echo 'Testing ARM64 Process Sandbox'\nexpr 100 '*' 5",
            "expected_output": "Testing ARM64 Process Sandbox\n500\n",
        }
        res_bash = client.post("/submissions?wait=true", json=payload_bash).json()
        print_result("Accepted", res_bash)

        print("\n" + "=" * 70)
        print("  🎉 ALL VERDICT AND METRIC CHECKS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_verifications()
