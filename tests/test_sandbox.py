from pathlib import Path

import pytest

from ree_openclaw.sandbox.harness import SandboxPolicy, SandboxedExecutor


def test_sandbox_allows_whitelisted_command(tmp_path: Path) -> None:
    executor = SandboxedExecutor(
        tmp_path / "sandbox",
        policy=SandboxPolicy(allowed_commands=("echo",)),
    )
    result = executor.run(("echo", "hello"))
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_sandbox_blocks_non_whitelisted_command(tmp_path: Path) -> None:
    executor = SandboxedExecutor(
        tmp_path / "sandbox",
        policy=SandboxPolicy(allowed_commands=("echo",)),
    )
    with pytest.raises(PermissionError):
        executor.run(("ls",))


def test_sandbox_blocks_path_escape(tmp_path: Path) -> None:
    executor = SandboxedExecutor(tmp_path / "sandbox")
    with pytest.raises(PermissionError):
        executor.write_text("../escape.txt", "blocked")

