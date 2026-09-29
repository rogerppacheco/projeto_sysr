"""Utilitários para scripts que alteram o código-fonte dos sites.

Toda alteração é feita em memória, validada e só então gravada de forma atômica,
preservando encoding, BOM e o estilo de quebra de linha (LF/CRLF) do arquivo.
"""
from __future__ import annotations

import difflib
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_BOM = "\ufeff"


class PatchError(Exception):
    pass


@dataclass
class SourceFile:
    path: Path
    text: str
    eol: str = "\n"
    bom: bool = False
    original: str = field(init=False)

    def __post_init__(self) -> None:
        self.original = self.text

    @classmethod
    def load(cls, path: str | os.PathLike) -> "SourceFile":
        path = Path(path)
        raw = path.read_bytes().decode("utf-8")
        bom = raw.startswith(_BOM)
        if bom:
            raw = raw[1:]
        eol = "\r\n" if "\r\n" in raw else "\n"
        return cls(path=path, text=raw.replace("\r\n", "\n"), eol=eol, bom=bom)

    @property
    def changed(self) -> bool:
        return self.text != self.original

    def replace_once(self, target: str, replacement: str) -> str:
        """Substitui `target` exatamente uma vez.

        Retorna "aplicado", "ja_aplicado" ou "nao_encontrado".
        """
        count = self.text.count(target)
        if count > 1:
            raise PatchError(f"{self.path}: trecho alvo aparece {count} vezes; substituição ambígua")
        if count == 1:
            self.text = self.text.replace(target, replacement)
            return "aplicado"
        if replacement in self.text:
            return "ja_aplicado"
        return "nao_encontrado"

    def append_block(self, block: str) -> None:
        """Acrescenta um bloco ao fim do arquivo, separado por uma linha em branco."""
        self.text = self.text.rstrip("\n") + "\n\n" + block.strip("\n") + "\n"

    def validate(self) -> None:
        for lineno, line in enumerate(self.text.split("\n"), start=1):
            if line.strip() in ("\\n", "\\r\\n"):
                raise PatchError(f"{self.path}:{lineno}: linha contém '\\n' literal em vez de quebra de linha")
        if self.path.suffix == ".py":
            try:
                compile(self.text, str(self.path), "exec")
            except SyntaxError as exc:
                raise PatchError(f"{self.path}:{exc.lineno}: SyntaxError após o patch: {exc.msg}") from exc

    def diff(self) -> str:
        return "".join(
            difflib.unified_diff(
                self.original.splitlines(keepends=True),
                self.text.splitlines(keepends=True),
                fromfile=f"a/{self.path.name}",
                tofile=f"b/{self.path.name}",
            )
        )

    def save(self) -> bool:
        if not self.changed:
            return False
        self.validate()
        data = ((_BOM if self.bom else "") + self.text.replace("\n", self.eol)).encode("utf-8")
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        self.original = self.text
        return True


def git(repo: str | os.PathLike, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise PatchError(f"git {' '.join(args)} falhou em {repo}:\n{result.stderr.strip()}")
    return result.stdout


def ensure_clean_worktree(repo: str | os.PathLike) -> None:
    pending = git(repo, "status", "--porcelain").strip()
    if pending:
        raise PatchError(f"{repo} tem alterações não commitadas; resolva antes de rodar o patch:\n{pending}")


def commit_files(repo: str | os.PathLike, files: list[Path], message: str, push: bool) -> None:
    rel = [str(Path(f).resolve().relative_to(Path(repo).resolve())) for f in files]
    git(repo, "add", "--", *rel)
    git(repo, "commit", "-m", message)
    if push:
        git(repo, "push")
