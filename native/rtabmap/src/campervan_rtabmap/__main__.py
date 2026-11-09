"""Inspect the native build and its macOS dynamic dependency closure."""

import argparse
import json
import subprocess
from pathlib import Path

from . import _native, build_info


def _load_commands(path: Path) -> tuple[list[str], list[str]]:
    libraries = subprocess.check_output(["otool", "-L", str(path)], text=True).splitlines()[1:]
    dependencies = [line.strip().split(" (", 1)[0] for line in libraries]
    commands = subprocess.check_output(["otool", "-l", str(path)], text=True).splitlines()
    rpaths = []
    for i, line in enumerate(commands):
        if line.strip() == "cmd LC_RPATH":
            for candidate in commands[i + 1 : i + 4]:
                if candidate.strip().startswith("path "):
                    rpaths.append(candidate.strip().split(" ", 2)[1])
    return dependencies, rpaths


def _audit() -> list[str]:
    package = Path(__file__).resolve().parent
    extension = Path(_native.__file__).resolve()
    seen: set[Path] = set()
    errors: list[str] = []

    def inspect(path: Path, inherited_rpaths: tuple[Path, ...] = ()) -> None:
        if path in seen:
            return
        seen.add(path)
        dependencies, local_rpaths = _load_commands(path)
        rpaths = tuple(Path(p.replace("@loader_path", str(path.parent))) for p in local_rpaths) + inherited_rpaths
        for dependency in dependencies:
            if dependency.startswith(("/usr/lib/", "/System/Library/")):
                continue
            if dependency.startswith("@loader_path/"):
                candidates = [path.parent / dependency.removeprefix("@loader_path/")]
            elif dependency.startswith("@rpath/"):
                candidates = [r / dependency.removeprefix("@rpath/") for r in rpaths]
            else:
                candidates = [Path(dependency)]
            resolved = next((p.resolve() for p in candidates if p.exists()), None)
            if resolved is None or not resolved.is_relative_to(package):
                errors.append(f"{path}: external or unresolved dependency {dependency}")
            else:
                inspect(resolved, rpaths)

    inspect(extension)
    print(f"extension: {extension}")
    print(f"package bytes: {sum(p.stat().st_size for p in package.rglob('*') if p.is_file())}")
    print(f"inspected binaries: {len(seen)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--info", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if not (args.info or args.audit):
        parser.error("select --info or --audit")
    print(json.dumps(build_info(), indent=2, sort_keys=True))
    print((Path(__file__).parent / "build-info.json").read_text())
    if args.audit:
        errors = _audit()
        for error in errors:
            print(error)
        if errors:
            raise SystemExit(1)
        print("dependency audit: Apple system and package libraries only")


if __name__ == "__main__":
    main()
