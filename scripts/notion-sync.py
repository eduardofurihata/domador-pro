#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "notion-client>=2.2.1",
#   "click>=8.1.0",
# ]
# ///
"""
notion-sync — bidirectional manual sync between local markdown files and Notion pages.

Usage:
    notion-sync init <page_url_or_id>      bootstrap: define a página raiz no Notion
    notion-sync push [path]                local → Notion
    notion-sync pull [path]                Notion → local
    notion-sync status [path]              mostra o que mudaria sem aplicar

Flags:
    --force        sobrescreve mesmo com mudança remota desde o último sync
    --dry-run      mostra plano sem aplicar
    --verbose      logs detalhados

Token: ~/.config/notion-sync/.env (NOTION_TOKEN=...)
State: ./.notion-sync.json (commitado no repo)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
from notion_client import APIResponseError, Client

# =============================================================================
# CONFIG
# =============================================================================

TOKEN_PATH = Path.home() / ".config" / "notion-sync" / ".env"
STATE_FILENAME = ".notion-sync.json"
DEFAULT_LOCAL_ROOT = "."
STATE_VERSION = 1

# Pastas/padrões sempre ignorados (além de hidden e dirs sem .md)
ALWAYS_IGNORE = {
    "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    "target", ".pytest_cache", ".ruff_cache", ".mypy_cache",
}

# Notion API limits
MAX_BLOCKS_PER_REQUEST = 100
MAX_RICH_TEXT_LENGTH = 2000


# =============================================================================
# TOKEN & STATE
# =============================================================================

def load_token() -> str:
    """Load NOTION_TOKEN from ~/.config/notion-sync/.env or env var."""
    env_token = os.environ.get("NOTION_TOKEN")
    if env_token:
        return env_token

    if not TOKEN_PATH.exists():
        click.echo(
            click.style(
                f"❌ Token não encontrado. Crie {TOKEN_PATH} com NOTION_TOKEN=...",
                fg="red",
            ),
            err=True,
        )
        sys.exit(1)

    for line in TOKEN_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith("NOTION_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")

    click.echo(
        click.style(f"❌ NOTION_TOKEN não encontrado em {TOKEN_PATH}", fg="red"),
        err=True,
    )
    sys.exit(1)


def find_repo_root() -> Path:
    """Walk up from cwd until we find a .git or the existing state file."""
    cur = Path.cwd().resolve()
    while cur != cur.parent:
        if (cur / ".git").exists() or (cur / STATE_FILENAME).exists():
            return cur
        cur = cur.parent
    return Path.cwd().resolve()


def state_path(repo_root: Path) -> Path:
    return repo_root / STATE_FILENAME


def load_state(repo_root: Path) -> dict[str, Any]:
    p = state_path(repo_root)
    if not p.exists():
        return {
            "version": STATE_VERSION,
            "local_root": DEFAULT_LOCAL_ROOT,
            "root_page_id": None,
            "mapping": {},
        }
    state = json.loads(p.read_text())
    state.setdefault("mapping", {})
    return state


def save_state(repo_root: Path, state: dict[str, Any]) -> None:
    p = state_path(repo_root)
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


# =============================================================================
# UTIL
# =============================================================================

def normalize_page_id(page_id_or_url: str) -> str:
    """Aceita URL Notion ou page_id puro, retorna UUID com hífens.

    URLs do Notion: o id (32 hex) fica sempre no fim do último path segment,
    ex: https://www.notion.so/Sync-34fbccbb29bb8035be59ce2cf45a8bc2?pvs=4
    """
    s = page_id_or_url.strip()
    if "://" in s or s.startswith("/"):
        last = s.rstrip("/").split("/")[-1]
        last = last.split("?")[0].split("#")[0]
        s = last

    s_clean = s.replace("-", "").lower()
    # 32 hex chars no FIM da string (após possível "Title-" prefix)
    m = re.search(r"([0-9a-f]{32})$", s_clean)
    if m:
        h = m.group(1)
        return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    # Fallback: UUID já formatado
    m2 = re.search(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        s.lower(),
    )
    if m2:
        return m2.group(1)
    raise click.ClickException(f"page_id inválido: {page_id_or_url}")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def title_from_filename(p: Path) -> str:
    """README.md de uma pasta usa o nome da pasta. Outros, o nome do arquivo sem extensão."""
    stem = p.stem
    if stem.upper() == "README":
        return p.parent.name
    return stem


# =============================================================================
# MARKDOWN → NOTION BLOCKS
# =============================================================================

INLINE_PATTERNS = [
    # (regex, builder)
    (re.compile(r"\*\*(.+?)\*\*"), lambda m: ("bold", m.group(1))),
    (re.compile(r"(?<!\*)\*([^*\n]+?)\*(?!\*)"), lambda m: ("italic", m.group(1))),
    (re.compile(r"_([^_\n]+?)_"), lambda m: ("italic", m.group(1))),
    (re.compile(r"~~(.+?)~~"), lambda m: ("strikethrough", m.group(1))),
    (re.compile(r"`([^`\n]+?)`"), lambda m: ("code", m.group(1))),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), lambda m: ("link", (m.group(1), m.group(2)))),
]


def parse_inline(text: str) -> list[dict]:
    """Converte markdown inline em rich_text[] do Notion."""
    if not text:
        return []

    result: list[dict] = []

    def emit_plain(s: str):
        if not s:
            return
        # Quebra por MAX_RICH_TEXT_LENGTH
        for i in range(0, len(s), MAX_RICH_TEXT_LENGTH):
            chunk = s[i : i + MAX_RICH_TEXT_LENGTH]
            result.append(
                {
                    "type": "text",
                    "text": {"content": chunk, "link": None},
                    "annotations": {
                        "bold": False, "italic": False, "strikethrough": False,
                        "underline": False, "code": False, "color": "default",
                    },
                    "plain_text": chunk,
                }
            )

    # Encontrar todos os matches de todos os patterns, ordenar por posição
    matches: list[tuple[int, int, str, Any]] = []
    for pattern, builder in INLINE_PATTERNS:
        for m in pattern.finditer(text):
            kind, payload = builder(m)
            matches.append((m.start(), m.end(), kind, payload))

    # Resolver sobreposições: pegar o de menor start, depois reiniciar a busca após o fim
    matches.sort(key=lambda x: (x[0], -x[1]))
    chosen: list[tuple[int, int, str, Any]] = []
    last_end = -1
    for start, end, kind, payload in matches:
        if start >= last_end:
            chosen.append((start, end, kind, payload))
            last_end = end

    cursor = 0
    for start, end, kind, payload in chosen:
        emit_plain(text[cursor:start])
        if kind == "link":
            link_text, url = payload
            # Notion só aceita http(s)/mailto/tel — relativos viram texto plano
            url_clean = url.strip()
            is_valid = url_clean.startswith(("http://", "https://", "mailto:", "tel:"))
            if is_valid:
                result.append(
                    {
                        "type": "text",
                        "text": {"content": link_text, "link": {"url": url_clean}},
                        "annotations": {
                            "bold": False, "italic": False, "strikethrough": False,
                            "underline": False, "code": False, "color": "default",
                        },
                        "plain_text": link_text,
                        "href": url_clean,
                    }
                )
            else:
                # link relativo/inválido → mantém só o texto, sem hyperlink
                emit_plain(link_text)
        else:
            ann = {
                "bold": False, "italic": False, "strikethrough": False,
                "underline": False, "code": False, "color": "default",
            }
            ann[kind] = True
            content = payload
            for i in range(0, len(content), MAX_RICH_TEXT_LENGTH):
                chunk = content[i : i + MAX_RICH_TEXT_LENGTH]
                result.append(
                    {
                        "type": "text",
                        "text": {"content": chunk, "link": None},
                        "annotations": ann.copy(),
                        "plain_text": chunk,
                    }
                )
        cursor = end
    emit_plain(text[cursor:])
    return result


def md_to_blocks(md_text: str) -> list[dict]:
    """Parser line-by-line cobrindo headings, listas, código, quote, hr, tabelas, parágrafos."""
    # Strip frontmatter YAML
    lines = md_text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1 :]
                break

    blocks: list[dict] = []
    i = 0
    n = len(lines)

    def append_block(b: dict):
        blocks.append(b)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Linha em branco — pula
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", stripped):
            append_block({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # Code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plain text"
            i += 1
            code_lines: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # consume closing ```
            code_content = "\n".join(code_lines)
            # Notion code block: language deve estar em uma allowlist; senão usa "plain text"
            allowed_langs = {
                "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript",
                "c++", "c#", "css", "dart", "diff", "docker", "elixir", "elm",
                "erlang", "flow", "fortran", "f#", "gherkin", "glsl", "go",
                "graphql", "groovy", "haskell", "html", "java", "javascript",
                "json", "julia", "kotlin", "latex", "less", "lisp", "livescript",
                "lua", "makefile", "markdown", "markup", "matlab", "mermaid",
                "nix", "objective-c", "ocaml", "pascal", "perl", "php", "plain text",
                "powershell", "prolog", "protobuf", "python", "r", "reason", "ruby",
                "rust", "sass", "scala", "scheme", "scss", "shell", "sql", "swift",
                "typescript", "vb.net", "verilog", "vhdl", "visual basic",
                "webassembly", "xml", "yaml",
            }
            lang_norm = lang.lower()
            if lang_norm not in allowed_langs:
                lang_norm = "plain text"
            append_block(
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": code_content[:MAX_RICH_TEXT_LENGTH * 50]},
                            }
                        ],
                        "language": lang_norm,
                    },
                }
            )
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m:
            level = min(len(m.group(1)), 3)
            text = m.group(2).strip()
            ttype = f"heading_{level}"
            append_block(
                {
                    "object": "block",
                    "type": ttype,
                    ttype: {"rich_text": parse_inline(text)},
                }
            )
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            append_block(
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": parse_inline("\n".join(quote_lines))},
                }
            )
            continue

        # Tables: linha começa com | e a próxima é separador |---|---|
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            header_cells = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2  # pula header e separador
            rows: list[list[str]] = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1

            width = max(len(header_cells), max((len(r) for r in rows), default=0))
            def pad(cells: list[str]) -> list[str]:
                return cells + [""] * (width - len(cells))

            children = [
                {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": [parse_inline(c) for c in pad(header_cells)]
                    },
                }
            ] + [
                {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {"cells": [parse_inline(c) for c in pad(r)]},
                }
                for r in rows
            ]
            append_block(
                {
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": width,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": children,
                    },
                }
            )
            continue

        # To-do
        m = re.match(r"^[-*+]\s+\[([ xX])\]\s+(.+)$", stripped)
        if m:
            checked = m.group(1).lower() == "x"
            text = m.group(2).strip()
            append_block(
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": parse_inline(text),
                        "checked": checked,
                    },
                }
            )
            i += 1
            continue

        # Bulleted list
        m = re.match(r"^[-*+]\s+(.+)$", stripped)
        if m:
            text = m.group(1).strip()
            append_block(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": parse_inline(text)},
                }
            )
            i += 1
            continue

        # Numbered list
        m = re.match(r"^\d+\.\s+(.+)$", stripped)
        if m:
            text = m.group(1).strip()
            append_block(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": parse_inline(text)},
                }
            )
            i += 1
            continue

        # Paragraph (acumula linhas até linha em branco ou outro bloco)
        para_lines = [stripped]
        i += 1
        while i < n:
            next_line = lines[i]
            next_stripped = next_line.strip()
            if not next_stripped:
                break
            # se for início de outro bloco, para
            if (
                re.match(r"^#{1,6}\s+", next_stripped)
                or next_stripped.startswith("```")
                or next_stripped.startswith(">")
                or next_stripped.startswith("|")
                or re.match(r"^[-*+]\s+", next_stripped)
                or re.match(r"^\d+\.\s+", next_stripped)
                or re.match(r"^(\*{3,}|-{3,}|_{3,})$", next_stripped)
            ):
                break
            para_lines.append(next_stripped)
            i += 1
        append_block(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": parse_inline(" ".join(para_lines))},
            }
        )

    return blocks


# =============================================================================
# NOTION BLOCKS → MARKDOWN
# =============================================================================

def render_rich_text(rich_text: list[dict]) -> str:
    parts = []
    for rt in rich_text:
        text = rt.get("plain_text") or rt.get("text", {}).get("content", "")
        ann = rt.get("annotations", {})
        href = rt.get("href") or rt.get("text", {}).get("link", {}).get("url") if rt.get("text", {}).get("link") else None
        if ann.get("code"):
            text = f"`{text}`"
        if ann.get("bold"):
            text = f"**{text}**"
        if ann.get("italic"):
            text = f"*{text}*"
        if ann.get("strikethrough"):
            text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)


def blocks_to_md(blocks: list[dict], client: Client | None = None, depth: int = 0) -> str:
    out: list[str] = []
    for b in blocks:
        t = b.get("type")
        data = b.get(t, {})
        if t == "paragraph":
            out.append(render_rich_text(data.get("rich_text", [])))
            out.append("")
        elif t in ("heading_1", "heading_2", "heading_3"):
            level = int(t.split("_")[1])
            out.append("#" * level + " " + render_rich_text(data.get("rich_text", [])))
            out.append("")
        elif t == "bulleted_list_item":
            out.append("- " + render_rich_text(data.get("rich_text", [])))
        elif t == "numbered_list_item":
            out.append("1. " + render_rich_text(data.get("rich_text", [])))
        elif t == "to_do":
            check = "x" if data.get("checked") else " "
            out.append(f"- [{check}] " + render_rich_text(data.get("rich_text", [])))
        elif t == "code":
            lang = data.get("language", "")
            code_text = render_rich_text(data.get("rich_text", []))
            out.append(f"```{lang}")
            out.append(code_text)
            out.append("```")
            out.append("")
        elif t == "quote":
            text = render_rich_text(data.get("rich_text", []))
            for ln in text.split("\n"):
                out.append(f"> {ln}")
            out.append("")
        elif t == "divider":
            out.append("---")
            out.append("")
        elif t == "table" and client is not None:
            children = client.blocks.children.list(block_id=b["id"]).get("results", [])
            if children:
                rows: list[list[str]] = []
                for row in children:
                    if row.get("type") == "table_row":
                        cells = row["table_row"]["cells"]
                        rows.append([render_rich_text(c) for c in cells])
                if rows:
                    width = len(rows[0])
                    out.append("| " + " | ".join(rows[0]) + " |")
                    out.append("|" + "|".join(["---"] * width) + "|")
                    for r in rows[1:]:
                        out.append("| " + " | ".join(r) + " |")
                    out.append("")
        elif t == "callout":
            text = render_rich_text(data.get("rich_text", []))
            out.append(f"> {text}")
            out.append("")
        elif t == "toggle":
            out.append(render_rich_text(data.get("rich_text", [])))
            out.append("")
        elif t in ("image", "video", "file", "embed", "bookmark"):
            url = data.get("url") or data.get("external", {}).get("url") or data.get("file", {}).get("url", "")
            caption = render_rich_text(data.get("caption", []))
            if t == "image":
                out.append(f"![{caption}]({url})")
            else:
                out.append(f"[{caption or url}]({url})")
            out.append("")
        # outros tipos: ignora silenciosamente
    return "\n".join(out).rstrip() + "\n"


# =============================================================================
# NOTION OPS
# =============================================================================

def get_page(client: Client, page_id: str) -> dict:
    return client.pages.retrieve(page_id=page_id)


def get_page_title(page: dict) -> str:
    props = page.get("properties", {})
    title_prop = props.get("title") or next(
        (v for v in props.values() if v.get("type") == "title"), None
    )
    if not title_prop:
        return ""
    rt = title_prop.get("title", [])
    return "".join(t.get("plain_text", "") for t in rt)


def get_page_blocks(client: Client, page_id: str) -> list[dict]:
    blocks: list[dict] = []
    cursor: str | None = None
    while True:
        kwargs = {"block_id": page_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.blocks.children.list(**kwargs)
        blocks.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return blocks


def archive_block(client: Client, block_id: str) -> None:
    client.blocks.delete(block_id=block_id)


def replace_page_blocks(
    client: Client,
    page_id: str,
    new_blocks: list[dict],
    *,
    preserve_child_pages: bool = True,
) -> None:
    """Substitui o CONTEÚDO da página por new_blocks.

    Por padrão preserva blocks do tipo `child_page` — eles representam as
    páginas-filhas (subpastas/arquivos no nosso modelo). Sem isso, todo push
    de README arquivaria as subpáginas e quebraria a hierarquia.

    Resultado: ordem fica [child_pages preservados][novo conteúdo appendado].
    A ordem visual no Notion não é igual à do markdown, mas os dados estão
    íntegros.
    """
    existing = get_page_blocks(client, page_id)
    for b in existing:
        if preserve_child_pages and b.get("type") == "child_page":
            continue
        try:
            archive_block(client, b["id"])
        except APIResponseError as e:
            click.echo(f"  warn: falhou ao arquivar block {b['id']}: {e}", err=True)
    for i in range(0, len(new_blocks), MAX_BLOCKS_PER_REQUEST):
        batch = new_blocks[i : i + MAX_BLOCKS_PER_REQUEST]
        client.blocks.children.append(block_id=page_id, children=batch)


def create_child_page(client: Client, parent_page_id: str, title: str) -> str:
    resp = client.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
    )
    return resp["id"]


def list_child_pages(client: Client, page_id: str) -> list[dict]:
    """Retorna apenas blocos do tipo child_page (não outros blocos)."""
    out = []
    for b in get_page_blocks(client, page_id):
        if b.get("type") == "child_page":
            out.append(b)
    return out


def update_page_title(client: Client, page_id: str, title: str) -> None:
    client.pages.update(
        page_id=page_id,
        properties={
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
    )


# =============================================================================
# SYNC LOGIC
# =============================================================================

def is_md_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() == ".md"


def dir_has_md(path: Path) -> bool:
    """True se a pasta ou qualquer descendente tem .md (ignorando hidden e ALWAYS_IGNORE)."""
    if not path.is_dir():
        return False
    for root, dirs, files in os.walk(path):
        # poda hidden e always-ignore
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in ALWAYS_IGNORE
        ]
        if any(f.lower().endswith(".md") for f in files):
            return True
    return False


def should_skip_dir(p: Path) -> bool:
    if p.name.startswith("."):
        return True
    if p.name in ALWAYS_IGNORE:
        return True
    if not dir_has_md(p):
        return True
    return False


def list_dir_for_sync(local_dir: Path) -> tuple[list[Path], Path | None]:
    """Retorna (subpastas+arquivos, README.md). Pastas sem .md e ignored são puladas."""
    subdirs = []
    md_files = []
    readme: Path | None = None
    for child in sorted(local_dir.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            if should_skip_dir(child):
                continue
            subdirs.append(child)
        elif is_md_file(child):
            if child.stem.upper() == "README":
                readme = child
            else:
                md_files.append(child)
    return subdirs + md_files, readme


def push_path(
    client: Client,
    state: dict,
    repo_root: Path,
    local_root: Path,
    target: Path,
    parent_page_id: str,
    *,
    force: bool,
    dry_run: bool,
    verbose: bool,
    counter: dict,
) -> None:
    rel = str(target.relative_to(local_root)) if target != local_root else "."
    mapping = state["mapping"]

    if target.is_dir():
        # Garante que a pasta tem uma página correspondente (exceto se for o próprio root)
        folder_page_id = parent_page_id
        if rel != ".":
            entry = mapping.get(rel)
            if entry and entry.get("page_id"):
                folder_page_id = entry["page_id"]
            else:
                title = target.name
                if dry_run:
                    click.echo(f"  [dry] criaria página '{title}' sob {parent_page_id[:8]}…")
                    folder_page_id = "DRY-RUN-NEW-PAGE"
                else:
                    folder_page_id = create_child_page(client, parent_page_id, title)
                    mapping[rel] = {
                        "page_id": folder_page_id,
                        "type": "folder",
                        "local_hash": None,
                        "notion_last_edited_time": None,
                        "last_synced": now_iso(),
                    }
                    if verbose:
                        click.echo(f"  + criou página folder '{title}' ({folder_page_id})")

        # README.md: vira o conteúdo da página da pasta
        children, readme = list_dir_for_sync(target)
        if readme is not None and folder_page_id != "DRY-RUN-NEW-PAGE":
            push_file_to_page(
                client, state, repo_root, local_root, readme,
                folder_page_id, force=force, dry_run=dry_run,
                verbose=verbose, counter=counter, is_readme=True,
            )

        # Recursão nos filhos (excluindo README, que já foi tratado)
        for child in children:
            push_path(
                client, state, repo_root, local_root, child,
                folder_page_id, force=force, dry_run=dry_run,
                verbose=verbose, counter=counter,
            )

    elif is_md_file(target):
        push_file_to_page(
            client, state, repo_root, local_root, target,
            parent_page_id, force=force, dry_run=dry_run,
            verbose=verbose, counter=counter, is_readme=False,
        )


def push_file_to_page(
    client: Client,
    state: dict,
    repo_root: Path,
    local_root: Path,
    file_path: Path,
    parent_page_id: str,
    *,
    force: bool,
    dry_run: bool,
    verbose: bool,
    counter: dict,
    is_readme: bool,
) -> None:
    """
    Empurra conteúdo de um .md pra uma página Notion.

    Para is_readme=True: o conteúdo do README.md vai DIRETAMENTE pra
    parent_page_id (a página da pasta), não cria página filha.

    Para is_readme=False: cria/usa página filha de parent_page_id com
    título derivado do nome do arquivo.
    """
    rel = str(file_path.relative_to(local_root))
    mapping = state["mapping"]
    entry = mapping.get(rel)

    cur_hash = file_hash(file_path)
    md_text = file_path.read_text()
    new_blocks = md_to_blocks(md_text)

    if is_readme:
        # README: conteúdo vai pra própria página da pasta (parent_page_id).
        page_id = parent_page_id
    else:
        page_id = entry.get("page_id") if entry else None

    title = title_from_filename(file_path) if not is_readme else None

    # Detectar mudanças
    local_changed = (entry is None) or (entry.get("local_hash") != cur_hash)
    remote_changed = False
    if page_id and entry is not None:
        try:
            page = get_page(client, page_id)
            remote_edited = page.get("last_edited_time")
            stored_edited = entry.get("notion_last_edited_time")
            if remote_edited and stored_edited and remote_edited > stored_edited:
                remote_changed = True
        except APIResponseError:
            if not is_readme:
                page_id = None  # foi deletada no Notion?

    if not local_changed and entry is not None:
        if verbose:
            click.echo(f"  ✓ {rel} (sem mudanças)")
        return

    if remote_changed and not force:
        click.echo(
            click.style(
                f"  ⚠ {rel}: remoto mudou desde último sync — pulando (use --force pra sobrescrever)",
                fg="yellow",
            )
        )
        return

    counter["pushed"] = counter.get("pushed", 0) + 1
    if dry_run:
        click.echo(f"  [dry] push {rel} → page {page_id or '(novo)'}")
        return

    if not is_readme and not page_id:
        page_id = create_child_page(client, parent_page_id, title)
        if verbose:
            click.echo(f"  + criou página '{title}' ({page_id[:8]}…)")
    elif not is_readme:
        # arquivo já mapeado: atualiza title se necessário
        try:
            cur_page = get_page(client, page_id)
            cur_title = get_page_title(cur_page)
            if cur_title != title:
                update_page_title(client, page_id, title)
        except APIResponseError:
            pass

    # substitui conteúdo da página alvo
    replace_page_blocks(client, page_id, new_blocks)

    # captura novo last_edited_time depois da nossa escrita
    page_after = get_page(client, page_id)

    mapping[rel] = {
        "page_id": page_id,
        "type": "readme" if is_readme else "file",
        "local_hash": cur_hash,
        "notion_last_edited_time": page_after.get("last_edited_time"),
        "last_synced": now_iso(),
    }
    save_state(repo_root, state)
    click.echo(click.style(f"  ↑ {rel}", fg="green"))


def pull_path(
    client: Client,
    state: dict,
    repo_root: Path,
    local_root: Path,
    target: Path,
    page_id: str,
    *,
    force: bool,
    dry_run: bool,
    verbose: bool,
    counter: dict,
) -> None:
    """Puxa Notion → local. target é o caminho local correspondente à page_id."""
    target.mkdir(parents=True, exist_ok=True)
    rel_dir = str(target.relative_to(local_root)) if target != local_root else "."
    mapping = state["mapping"]

    # Lista filhos da página: pages (subpastas/arquivos) + outros blocos (conteúdo da página)
    all_blocks = get_page_blocks(client, page_id)
    child_pages = [b for b in all_blocks if b.get("type") == "child_page"]
    content_blocks = [b for b in all_blocks if b.get("type") != "child_page"]

    # Se a pasta tem README.md ou é a raiz, conteúdo da página atual vai pro README
    if rel_dir != ".":
        readme_rel = f"{rel_dir}/README.md" if rel_dir != "." else "README.md"
        readme_path = local_root / readme_rel
        if content_blocks:
            pull_blocks_to_file(
                client, state, repo_root, local_root, readme_path,
                page_id, content_blocks,
                force=force, dry_run=dry_run, verbose=verbose, counter=counter,
                is_readme=True,
            )

    # Cada child_page: se nome bate com pasta, recursão; senão, .md
    for cp in child_pages:
        cp_id = cp["id"]
        cp_title = cp.get("child_page", {}).get("title", "untitled")
        # Decide se é pasta ou arquivo: olhamos se a página tem outras child_pages dentro
        sub_blocks = get_page_blocks(client, cp_id)
        sub_child_pages = [x for x in sub_blocks if x.get("type") == "child_page"]
        is_folder_like = len(sub_child_pages) > 0

        # Sanitiza nome pra filesystem
        safe_name = re.sub(r"[^\w\-. ]", "-", cp_title).strip().strip("-") or "untitled"

        if is_folder_like:
            sub_target = target / safe_name
            pull_path(
                client, state, repo_root, local_root, sub_target, cp_id,
                force=force, dry_run=dry_run, verbose=verbose, counter=counter,
            )
        else:
            file_path = target / f"{safe_name}.md"
            sub_content = [x for x in sub_blocks if x.get("type") != "child_page"]
            pull_blocks_to_file(
                client, state, repo_root, local_root, file_path,
                cp_id, sub_content,
                force=force, dry_run=dry_run, verbose=verbose, counter=counter,
                is_readme=False,
            )


def pull_blocks_to_file(
    client: Client,
    state: dict,
    repo_root: Path,
    local_root: Path,
    file_path: Path,
    page_id: str,
    blocks: list[dict],
    *,
    force: bool,
    dry_run: bool,
    verbose: bool,
    counter: dict,
    is_readme: bool,
) -> None:
    rel = str(file_path.relative_to(local_root))
    mapping = state["mapping"]
    entry = mapping.get(rel)

    md_text = blocks_to_md(blocks, client=client)

    # Round-trip skip: se o local md → blocks → md já bate com o que veio
    # do Notion, a única diferença é nossa conversão lossy (ex: links relativos
    # que viram texto plano). Não sobrescreve o local nesse caso — preserva
    # sintaxe markdown rica que o usuário escreveu.
    if file_path.exists():
        try:
            local_md = file_path.read_text()
            local_roundtripped = blocks_to_md(md_to_blocks(local_md))
            if local_roundtripped.strip() == md_text.strip():
                if verbose:
                    click.echo(f"  ✓ {rel} (round-trip equivalente, mantém local)")
                # Realinha state pra evitar detectar como mudança em runs futuros
                page = get_page(client, page_id)
                if entry:
                    entry["local_hash"] = file_hash(file_path)
                    entry["notion_last_edited_time"] = page.get("last_edited_time")
                    entry["last_synced"] = now_iso()
                    save_state(repo_root, state)
                return
        except Exception:
            pass  # falha no round-trip → segue lógica normal

    page = get_page(client, page_id)
    remote_edited = page.get("last_edited_time")
    stored_edited = entry.get("notion_last_edited_time") if entry else None
    remote_changed = (entry is None) or (
        stored_edited and remote_edited and remote_edited > stored_edited
    )

    local_changed = False
    if file_path.exists() and entry is not None:
        cur_hash = file_hash(file_path)
        if entry.get("local_hash") and cur_hash != entry.get("local_hash"):
            local_changed = True

    if not remote_changed and entry is not None:
        if verbose:
            click.echo(f"  ✓ {rel} (sem mudanças remotas)")
        return

    if local_changed and not force:
        click.echo(
            click.style(
                f"  ⚠ {rel}: local mudou desde último sync — pulando (use --force pra sobrescrever)",
                fg="yellow",
            )
        )
        return

    counter["pulled"] = counter.get("pulled", 0) + 1
    if dry_run:
        click.echo(f"  [dry] pull page {page_id[:8]}… → {rel}")
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(md_text)

    mapping[rel] = {
        "page_id": page_id,
        "type": "readme" if is_readme else "file",
        "local_hash": file_hash(file_path),
        "notion_last_edited_time": remote_edited,
        "last_synced": now_iso(),
    }
    save_state(repo_root, state)
    click.echo(click.style(f"  ↓ {rel}", fg="cyan"))


# =============================================================================
# CLI
# =============================================================================

@click.group(help="Sync bidirecional manual entre markdown local e Notion.")
def cli():
    pass


@cli.command(help="Bootstrap: define a página raiz do Notion (passe ID ou URL).")
@click.argument("page")
@click.option(
    "--local-root", default=DEFAULT_LOCAL_ROOT,
    help="Pasta local raiz, relativa ao repo (default: '.', toda raiz do repo)",
)
@click.option(
    "--as", "create_as", default=None,
    help="Cria subpágina(s) dentro do `page` e usa como raiz. Aceita path (ex: 'sync/agencia-domapro').",
)
def init(page: str, local_root: str, create_as: str | None):
    repo_root = find_repo_root()
    state = load_state(repo_root)

    parent_id = normalize_page_id(page)
    token = load_token()
    client = Client(auth=token)

    # Valida acesso ao parent
    try:
        p = get_page(client, parent_id)
    except APIResponseError as e:
        raise click.ClickException(
            f"Falha ao acessar página {parent_id}. A integration foi compartilhada com ela?\n{e}"
        )
    parent_title = get_page_title(p) or "(sem título)"

    if create_as:
        # Cria cadeia: cada segmento vira subpágina filha do anterior, reusando se já existir
        cur_parent = parent_id
        for segment in [s for s in create_as.split("/") if s]:
            existing = list_child_pages(client, cur_parent)
            match = next(
                (c for c in existing if c.get("child_page", {}).get("title") == segment),
                None,
            )
            if match:
                cur_parent = match["id"]
                click.echo(f"  ↺ reaproveitando '{segment}' ({cur_parent[:8]}…)")
            else:
                cur_parent = create_child_page(client, cur_parent, segment)
                click.echo(f"  + criou '{segment}' ({cur_parent[:8]}…)")
        page_id = cur_parent
        title = create_as.split("/")[-1]
    else:
        page_id = parent_id
        title = parent_title

    state["root_page_id"] = page_id
    state["local_root"] = local_root
    save_state(repo_root, state)

    click.echo(click.style(f"✓ Raiz definida:", fg="green"))
    click.echo(f"  Notion page: '{title}' ({page_id})")
    click.echo(f"  Local root:  {(repo_root / local_root).resolve()}")
    click.echo(f"  State:       {state_path(repo_root)}")


def _resolve_target(repo_root: Path, local_root_dir: Path, path_arg: str | None) -> Path:
    if path_arg is None:
        return local_root_dir
    p = Path(path_arg).resolve() if Path(path_arg).is_absolute() else (Path.cwd() / path_arg).resolve()
    # validar que tá dentro do local_root
    try:
        p.relative_to(local_root_dir.resolve())
    except ValueError:
        raise click.ClickException(f"path '{path_arg}' está fora do local_root '{local_root_dir}'")
    return p


@cli.command(help="local → Notion. Path opcional limita escopo.")
@click.argument("path", required=False)
@click.option("--force", is_flag=True, help="sobrescreve mesmo se remoto mudou")
@click.option("--dry-run", is_flag=True, help="mostra plano sem aplicar")
@click.option("--verbose", "-v", is_flag=True)
def push(path: str | None, force: bool, dry_run: bool, verbose: bool):
    repo_root = find_repo_root()
    state = load_state(repo_root)
    if not state.get("root_page_id"):
        raise click.ClickException("Não inicializado. Rode `notion-sync init <page>` primeiro.")

    local_root = (repo_root / state["local_root"]).resolve()
    if not local_root.exists():
        raise click.ClickException(f"local_root não existe: {local_root}")

    target = _resolve_target(repo_root, local_root, path)

    token = load_token()
    client = Client(auth=token)

    # Determinar parent_page_id pro target inicial:
    # Se target == local_root → parent é root_page_id
    # Senão → precisamos ter a pasta pai mapeada
    counter: dict = {}

    if target == local_root:
        parent = state["root_page_id"]
    else:
        # Sobe a árvore até achar pasta mapeada (ou local_root)
        cur = target if target.is_dir() else target.parent
        while cur != local_root:
            rel_cur = str(cur.relative_to(local_root))
            entry = state["mapping"].get(rel_cur)
            if entry and entry.get("page_id"):
                # OK, mas precisamos do parent dessa pasta também — vamos só começar do root pra simplificar
                break
            cur = cur.parent
        # Pra simplicidade e correção, sempre começamos do root e descemos até o target.
        # Isso garante que pastas intermediárias existam no Notion.
        # Implementação: caminhar do root pra baixo, criando pastas ausentes.
        parent = state["root_page_id"]
        if target != local_root:
            parts = list(target.relative_to(local_root).parts)
            cur_parent = parent
            cur_path = local_root
            # cria/usa todas as pastas até o target.parent
            walk_parts = parts[:-1] if target.is_file() else parts
            for part in walk_parts:
                cur_path = cur_path / part
                rel = str(cur_path.relative_to(local_root))
                e = state["mapping"].get(rel)
                if e and e.get("page_id"):
                    cur_parent = e["page_id"]
                else:
                    if dry_run:
                        click.echo(f"  [dry] criaria página intermediária '{part}'")
                        cur_parent = "DRY-RUN-NEW-PAGE"
                    else:
                        cur_parent = create_child_page(client, cur_parent, part)
                        state["mapping"][rel] = {
                            "page_id": cur_parent,
                            "type": "folder",
                            "local_hash": None,
                            "notion_last_edited_time": None,
                            "last_synced": now_iso(),
                        }
                        save_state(repo_root, state)
            parent = cur_parent

    click.echo(f"push {target.relative_to(repo_root)} → page {parent[:8] if parent else '?'}…")
    push_path(
        client, state, repo_root, local_root, target, parent,
        force=force, dry_run=dry_run, verbose=verbose, counter=counter,
    )

    n = counter.get("pushed", 0)
    click.echo(click.style(f"✓ {n} arquivo(s) enviados.", fg="green"))


@cli.command(help="Notion → local. Path opcional limita escopo.")
@click.argument("path", required=False)
@click.option("--force", is_flag=True, help="sobrescreve local mesmo se mudou")
@click.option("--dry-run", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
def pull(path: str | None, force: bool, dry_run: bool, verbose: bool):
    repo_root = find_repo_root()
    state = load_state(repo_root)
    if not state.get("root_page_id"):
        raise click.ClickException("Não inicializado. Rode `notion-sync init <page>` primeiro.")

    local_root = (repo_root / state["local_root"]).resolve()
    target = _resolve_target(repo_root, local_root, path) if path else local_root

    token = load_token()
    client = Client(auth=token)

    # Resolver page_id do target
    if target == local_root:
        page_id = state["root_page_id"]
    else:
        rel = str(target.relative_to(local_root))
        entry = state["mapping"].get(rel)
        if not entry or not entry.get("page_id"):
            raise click.ClickException(
                f"'{rel}' ainda não tem mapeamento no Notion. Faça push antes ou rode pull sem path."
            )
        page_id = entry["page_id"]

    counter: dict = {}
    click.echo(f"pull page {page_id[:8]}… → {target.relative_to(repo_root)}")
    pull_path(
        client, state, repo_root, local_root, target, page_id,
        force=force, dry_run=dry_run, verbose=verbose, counter=counter,
    )

    n = counter.get("pulled", 0)
    click.echo(click.style(f"✓ {n} arquivo(s) recebidos.", fg="green"))


@cli.command(help="Mostra o que mudaria sem aplicar (push + pull dry).")
@click.argument("path", required=False)
def status(path: str | None):
    click.echo(click.style("→ push (dry):", fg="green"))
    ctx = click.get_current_context()
    ctx.invoke(push, path=path, force=False, dry_run=True, verbose=True)
    click.echo(click.style("\n← pull (dry):", fg="cyan"))
    ctx.invoke(pull, path=path, force=False, dry_run=True, verbose=True)


if __name__ == "__main__":
    cli()
