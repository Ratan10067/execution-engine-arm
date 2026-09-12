"""
Judge0 Comprehensive Languages Catalog.
Maps official Judge0 language IDs to compiler and runner configurations.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class LanguageConfig:
    id: int
    name: str
    is_compiled: bool
    source_file: str
    compile_cmd: Optional[str] = None
    run_cmd: str = ""
    is_archived: bool = False
    env: Optional[Dict[str, str]] = None


LANGUAGES_CATALOG: Dict[int, LanguageConfig] = {
    # Bash
    46: LanguageConfig(
        id=46,
        name="Bash (5.0.0)",
        is_compiled=False,
        source_file="script.sh",
        run_cmd="bash script.sh",
    ),
    # C (GCC 7.4.0)
    48: LanguageConfig(
        id=48,
        name="C (GCC 7.4.0)",
        is_compiled=True,
        source_file="main.c",
        compile_cmd="gcc -O2 -std=c11 main.c -o a.out -lm",
        run_cmd="./a.out",
    ),
    # C (GCC 8.3.0)
    49: LanguageConfig(
        id=49,
        name="C (GCC 8.3.0)",
        is_compiled=True,
        source_file="main.c",
        compile_cmd="gcc -O2 -std=c11 main.c -o a.out -lm",
        run_cmd="./a.out",
    ),
    # C (GCC 9.2.0)
    50: LanguageConfig(
        id=50,
        name="C (GCC 9.2.0)",
        is_compiled=True,
        source_file="main.c",
        compile_cmd="gcc -O2 -std=c17 main.c -o a.out -lm",
        run_cmd="./a.out",
    ),
    # C# (Mono 6.6.0.161)
    51: LanguageConfig(
        id=51,
        name="C# (Mono 6.6.0.161)",
        is_compiled=True,
        source_file="Main.cs",
        compile_cmd="mcs -out:Main.exe Main.cs",
        run_cmd="mono Main.exe",
    ),
    # C++ (GCC 7.4.0)
    52: LanguageConfig(
        id=52,
        name="C++ (GCC 7.4.0)",
        is_compiled=True,
        source_file="main.cpp",
        compile_cmd="g++ -O2 -std=c++17 main.cpp -o a.out -lm",
        run_cmd="./a.out",
    ),
    # C++ (GCC 8.3.0)
    53: LanguageConfig(
        id=53,
        name="C++ (GCC 8.3.0)",
        is_compiled=True,
        source_file="main.cpp",
        compile_cmd="g++ -O2 -std=c++17 main.cpp -o a.out -lm",
        run_cmd="./a.out",
    ),
    # C++ (GCC 9.2.0)
    54: LanguageConfig(
        id=54,
        name="C++ (GCC 9.2.0)",
        is_compiled=True,
        source_file="main.cpp",
        compile_cmd="g++ -O2 -std=c++20 main.cpp -o a.out -lm",
        run_cmd="./a.out",
    ),
    # Go (1.13.5)
    60: LanguageConfig(
        id=60,
        name="Go (1.13.5)",
        is_compiled=True,
        source_file="main.go",
        compile_cmd="go build -o a.out main.go",
        run_cmd="./a.out",
    ),
    # Java (OpenJDK 13.0.1 / 17)
    62: LanguageConfig(
        id=62,
        name="Java (OpenJDK 13.0.1)",
        is_compiled=True,
        source_file="Main.java",
        compile_cmd="javac Main.java",
        run_cmd="java -XX:+UseSerialGC -Xss1m -Xms16m Main",
    ),
    # JavaScript (Node.js 12.14.0)
    63: LanguageConfig(
        id=63,
        name="JavaScript (Node.js 12.14.0)",
        is_compiled=False,
        source_file="main.js",
        run_cmd="node --max-old-space-size=512 main.js",
    ),
    # Lua (5.3.5)
    64: LanguageConfig(
        id=64,
        name="Lua (5.3.5)",
        is_compiled=False,
        source_file="main.lua",
        run_cmd="lua main.lua",
    ),
    # PHP (7.4.1)
    68: LanguageConfig(
        id=68,
        name="PHP (7.4.1)",
        is_compiled=False,
        source_file="main.php",
        run_cmd="php main.php",
    ),
    # Python (2.7.17)
    70: LanguageConfig(
        id=70,
        name="Python (2.7.17)",
        is_compiled=False,
        source_file="script.py",
        run_cmd="python2 script.py",
    ),
    # Python (3.8.1)
    71: LanguageConfig(
        id=71,
        name="Python (3.8.1)",
        is_compiled=False,
        source_file="script.py",
        run_cmd="python3 script.py",
    ),
    # Ruby (2.7.0)
    72: LanguageConfig(
        id=72,
        name="Ruby (2.7.0)",
        is_compiled=False,
        source_file="main.rb",
        run_cmd="ruby main.rb",
    ),
    # Rust (1.40.0)
    73: LanguageConfig(
        id=73,
        name="Rust (1.40.0)",
        is_compiled=True,
        source_file="main.rs",
        compile_cmd="rustc -O main.rs -o a.out",
        run_cmd="./a.out",
    ),
    # TypeScript (3.7.4)
    74: LanguageConfig(
        id=74,
        name="TypeScript (3.7.4)",
        is_compiled=True,
        source_file="main.ts",
        compile_cmd="tsc main.ts",
        run_cmd="node --max-old-space-size=512 main.js",
    ),
    # C (Clang 7.0.1)
    75: LanguageConfig(
        id=75,
        name="C (Clang 7.0.1)",
        is_compiled=True,
        source_file="main.c",
        compile_cmd="clang -O2 -std=c17 main.c -o a.out -lm",
        run_cmd="./a.out",
    ),
    # C++ (Clang 7.0.1)
    76: LanguageConfig(
        id=76,
        name="C++ (Clang 7.0.1)",
        is_compiled=True,
        source_file="main.cpp",
        compile_cmd="clang++ -O2 -std=c++20 main.cpp -o a.out -lm",
        run_cmd="./a.out",
    ),
    # Kotlin (1.3.70)
    78: LanguageConfig(
        id=78,
        name="Kotlin (1.3.70)",
        is_compiled=True,
        source_file="Main.kt",
        compile_cmd="kotlinc Main.kt -include-runtime -d Main.jar",
        run_cmd="java -XX:+UseSerialGC -Xss1m -jar Main.jar",
    ),
    # SQLite 3
    82: LanguageConfig(
        id=82,
        name="SQL (SQLite 3.27.2)",
        is_compiled=False,
        source_file="query.sql",
        run_cmd="sqlite3 < query.sql",
    ),
    # Swift (5.2.3)
    83: LanguageConfig(
        id=83,
        name="Swift (5.2.3)",
        is_compiled=True,
        source_file="main.swift",
        compile_cmd="swiftc main.swift -o a.out",
        run_cmd="./a.out",
    ),
    # Perl (5.28.1)
    85: LanguageConfig(
        id=85,
        name="Perl (5.28.1)",
        is_compiled=False,
        source_file="main.pl",
        run_cmd="perl main.pl",
    ),
    # Multi-file Program
    89: LanguageConfig(
        id=89,
        name="Multi-file program",
        is_compiled=True,
        source_file="compile",
        compile_cmd="./compile",
        run_cmd="./run",
    ),
}


def get_language(language_id: int) -> Optional[LanguageConfig]:
    """Retrieve language configuration by ID."""
    return LANGUAGES_CATALOG.get(language_id)


def get_all_languages() -> List[Dict[str, Any]]:
    """Return all supported languages formatted for Judge0 API."""
    result = []
    for lang_id, lang in sorted(LANGUAGES_CATALOG.items()):
        result.append({
            "id": lang.id,
            "name": lang.name,
            "is_archived": lang.is_archived,
            "source_file": lang.source_file,
            "compile_cmd": lang.compile_cmd,
            "run_cmd": lang.run_cmd,
        })
    return result
