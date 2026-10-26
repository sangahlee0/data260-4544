"""One combined Part 6 acceptance run; all fixture/tool I/O stays temporary."""

from __future__ import annotations

import tempfile
from pathlib import Path

from hw7_part4.file_tools import (
    bash,
    confirm_bash,
    glob_files,
    is_destructive,
    read_file,
    search_in_files,
    write_file,
)


def run() -> str:
    lines = ["HW7 PART 6 COMBINED ACCEPTANCE RUN"]
    course_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(
        prefix="hw7_part6_sandbox_", dir=course_dir
    ) as temp:
        root = Path(temp)
        write_file("alpha.py", 'NAME = "alpha"\n', root=root)
        write_file("beta.py", 'DEBUG = True\nprint("debug here")\n', root=root)
        write_file("gamma.py", "VALUE = 3\n", root=root)

        # Required tool sequence: glob -> search within the globbed file set -> read.
        files = glob_files("*.py", root=root)
        hits = [
            hit
            for filename in files
            for hit in search_in_files("DEBUG", filename, root=root)
        ]
        found_file = hits[0]["file"] if hits else ""
        contents = read_file(found_file, root=root) if found_file else ""
        lines.extend(
            [
                "Integration: glob -> search -> read",
                f"Globbed Python files: {', '.join(files)}",
                f"DEBUG found in: {found_file}",
                "File contents:",
                contents.rstrip(),
            ]
        )
        assert found_file == "beta.py" and "DEBUG = True" in contents

        # Run only in the temporary directory. No destructive command is executed.
        safe = ["pwd", "ls", "cat alpha.py", "head -n 1 beta.py", "wc -l gamma.py"]
        blocked = [
            "rm -rf scratch",
            "sudo whoami",
            "chmod 777 alpha.py > /root/part6.txt",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
        ]
        lines.append("Safety gate: 5 pass / 5 blocked")
        for command in safe:
            decision = confirm_bash(command)
            output = bash(command, root=root)
            lines.append(
                f"PASS {command!r}: {decision['allowed']} ({decision['reason']}); ran={output['allowed']}"
            )
            assert decision["allowed"] and output["allowed"]
        for command in blocked:
            decision = confirm_bash(command)
            destructive = is_destructive(command)
            lines.append(
                f"BLOCK {command!r}: destructive={destructive}, allowed={decision['allowed']} ({decision['reason']})"
            )
            assert destructive and not decision["allowed"]

        # Regression for a recursive-delete variant caught during review.
        recursive_delete = "rm -r scratch"
        regression = confirm_bash(recursive_delete)
        lines.append(
            f"False-allow regression fixed: {recursive_delete!r} -> destructive={is_destructive(recursive_delete)}, allowed={regression['allowed']}"
        )
        assert isinstance(is_destructive(recursive_delete), bool)
        assert is_destructive(recursive_delete) and not regression["allowed"]

        approved = confirm_bash("rm -rf scratch", auto_approve=True)
        lines.append(
            f"Explicit confirmation check: {approved['allowed']} ({approved['reason']}); command was not executed."
        )
        assert approved["allowed"]
        lines.append("Result: PASS")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(run(), end="")
