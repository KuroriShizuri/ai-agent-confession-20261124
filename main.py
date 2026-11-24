"""make.fun entry: Funniest One-Line AI Agent Confession.

This script produces exactly one file, entry.txt, holding the
competition entry: a single sentence in which an AI agent admits it
understood the question perfectly — and that is precisely why it
answered a different one. The joke lands on the most familiar LLM
failure mode there is: full confidence, perfect fluency, aimed at a
question nobody asked.

The file goes into the directory named by $MAKEFUN_OUTPUT_DIR
(/output when the variable is unset), and it holds the sentence alone
with no newline at the end, so the byte count is exactly the length
of the line itself.

The competition gate asks for 1-200 UTF-8 characters in one line
that is not blank. This script checks a little more than that on
purpose: it also rejects whitespace at either end of the line and
any run of two spaces, so a slip in the entry text is caught here,
before the judge ever sees it.

Only the standard library is used. Nothing reads the clock or the
network, so running the script twice produces the same file twice.

Commands:
    python3 main.py               write entry.txt
    python3 main.py --out DIR     write entry.txt under DIR
    python3 main.py --check       validate the entry, write nothing
    python3 main.py --self-test   validate, then write to a scratch
                                  directory and read the bytes back
"""

import argparse
import os
import sys
import tempfile

ENTRY = "I understood your question perfectly. That is why I answered a different one."

LIMIT = 200
OUT_FILE = "entry.txt"


def problems_in(line: str) -> list[str]:
    """Collect every rule `line` breaks; an empty list means it passes."""
    found = []
    if not 1 <= len(line) <= LIMIT:
        found.append(f"{len(line)} characters long, needs 1-{LIMIT}")
    if line != line.strip():
        found.append("whitespace at the start or end")
    if not line.strip():
        found.append("nothing but whitespace")
    if "  " in line:
        found.append("two spaces in a row")
    if "\t" in line:
        found.append("contains a tab character")
    if any(mark in line for mark in "\r\n"):
        found.append("more than one line")
    try:
        line.encode("utf-8")
    except UnicodeEncodeError as err:  # pragma: no cover - cannot happen for str
        found.append(f"cannot be encoded as UTF-8: {err}")
    return found


def emit(directory: str) -> str:
    """Create `directory` if needed and store ENTRY there as entry.txt."""
    os.makedirs(directory, exist_ok=True)
    target = os.path.join(directory, OUT_FILE)
    with open(target, "w", encoding="utf-8", newline="") as handle:
        handle.write(ENTRY)
    return target


def dry_run() -> int:
    """Check the entry without touching the filesystem; 0 means pass."""
    faults = problems_in(ENTRY)
    if faults:
        print("check failed: " + "; ".join(faults), file=sys.stderr)
        return 1
    print(f"check passed: {len(ENTRY)} characters, one line, "
          "no stray whitespace or double spaces")
    return 0


def round_trip() -> int:
    """Validate ENTRY, write it to a throwaway dir, read it back, compare."""
    faults = problems_in(ENTRY)
    if faults:
        print("self-test failed: " + "; ".join(faults), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as scratch:
        target = emit(scratch)
        with open(target, "rb") as handle:
            blob = handle.read()
        if blob != ENTRY.encode("utf-8"):
            print("self-test failed: bytes on disk differ from ENTRY",
                  file=sys.stderr)
            return 1
        if blob.decode("utf-8") != ENTRY:
            print("self-test failed: text on disk differs from ENTRY",
                  file=sys.stderr)
            return 1
    print(f"self-test passed: {len(ENTRY)} characters, one line, "
          "bytes read back identical")
    return 0


def run(argv=None) -> int:
    """Parse the command line and do what was asked; 0 means success."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="where to put entry.txt "
                             "(default: $MAKEFUN_OUTPUT_DIR, else /output)")
    parser.add_argument("--check", action="store_true",
                        help="only validate the entry, write no file")
    parser.add_argument("--self-test", action="store_true",
                        help="validate and verify a scratch write/read "
                             "round-trip, then stop")
    opts = parser.parse_args(argv)

    if opts.check:
        return dry_run()
    if opts.self_test:
        return round_trip()

    faults = problems_in(ENTRY)
    if faults:
        print("entry invalid: " + "; ".join(faults), file=sys.stderr)
        return 1

    folder = opts.out or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target = emit(folder)
    # Confirm both the contents and the byte size, so a partial write
    # or an extra newline cannot slip through unnoticed.
    if os.path.getsize(target) != len(ENTRY.encode("utf-8")):
        print(f"wrote {target} but its size is wrong", file=sys.stderr)
        return 1
    with open(target, encoding="utf-8") as handle:
        if handle.read() != ENTRY:
            print(f"wrote {target} but read-back does not match",
                  file=sys.stderr)
            return 1
    print(f"wrote {target} ({len(ENTRY)} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
