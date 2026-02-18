from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class SandboxPolicy:
    allowed_commands: tuple[str, ...] = ("echo", "python3")
    max_runtime_seconds: int = 5


@dataclass(frozen=True)
class SandboxResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class SandboxedExecutor:
    def __init__(self, root: Path, policy: SandboxPolicy | None = None) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.policy = policy or SandboxPolicy()

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if not str(candidate).startswith(str(self.root)):
            raise PermissionError("path escapes sandbox root")
        return candidate

    def write_text(self, relative_path: str, content: str) -> Path:
        destination = self._resolve(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination

    def read_text(self, relative_path: str) -> str:
        source = self._resolve(relative_path)
        return source.read_text(encoding="utf-8")

    def run(self, command: Sequence[str], timeout: int | None = None) -> SandboxResult:
        if not command:
            raise ValueError("command cannot be empty")
        executable = Path(command[0]).name
        if executable not in self.policy.allowed_commands:
            raise PermissionError(f"command not allowed in sandbox: {executable}")
        process = subprocess.run(
            command,
            cwd=str(self.root),
            capture_output=True,
            text=True,
            timeout=timeout or self.policy.max_runtime_seconds,
            check=False,
        )
        return SandboxResult(
            command=tuple(command),
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )

