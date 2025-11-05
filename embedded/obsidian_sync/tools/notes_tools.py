"""Notes tools and system prompt.

Domain: Notes — Interact with Obsidian-style project pages and dated Notes.md files.

This extension provides:
- Project hierarchy discovery from Markdown frontmatter (`project_id`, `project_parent`).
- Retrieval of project page and linked note page text by `project_id` or display name.
- Query of dated note entries within a date range across `*Notes.md` files.
- Update/append content into today's dated entry for a project note, optionally under a section.

Environment:
- Base directory resolves to the synced vault at extensions/obsidian_sync/vault/
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import re
from datetime import datetime

# Local import
try:
    from . import project_hierarchy as gen
except ImportError:
    import project_hierarchy as gen


SYSTEM_PROMPT = """
You are an expert at managing notes and organizing information in an Obsidian-style vault.
When users ask about their notes, projects, or want to create entries,
use these tools to help them stay organized.

Prefer precise operations: when asked to update notes, find or create today's entry,
optionally place content under a specified markdown section.
"""


# ---------- Helper ----------

def _base_dir() -> Path:
    """Get the synced vault directory."""
    vault_path = Path(__file__).parent / "vault"
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault directory not found: {vault_path}. Ensure sync service is running.")
    return vault_path


# ---------- Tools ----------

def NOTES_GET_project_hierarchy() -> tuple[bool, str]:
    """
    Return a simplified hierarchy: root project names and immediate child names only.

    Example Prompt: "Show me my project structure" or "What projects do I have?"

    Example Response:
    {
      "status": "success",
      "hierarchy": "Eco AI\\n- Roadmap\\n- Research\\n\\nOpen Ethos\\n- Article"
    }

    Example Args:
    {}
    """
    try:
        base = _base_dir()
        projects = gen.build_projects(base)
        gen.link_notes(base, projects)
        lines: List[str] = []
        for root_id in gen.roots_of(projects):
            root = projects[root_id]
            lines.append(f"{root.display_name}")
            for child_id in root.children:
                child = projects[child_id]
                lines.append(f"- {child.display_name}")
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()
        
        result = {
            "status": "success",
            "hierarchy": "\\n".join(lines)
        }
        return (True, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        return (False, json.dumps(error, ensure_ascii=False))


def NOTES_GET_project_text(project_id: str) -> tuple[bool, str]:
    """
    Return the root project page text and note page text for a given project_id or display name.

    Example Prompt: "Show me the text for project Eco AI" or "What's in my Luna project notes?"

    Example Response:
    {
      "status": "success",
      "project_id": "Eco AI",
      "root_page_path": "Projects/Eco AI/Eco AI.md",
      "root_page_text": "# Eco AI\\n\\nAI-powered ecology project...",
      "note_page_path": "Projects/Eco AI/Notes.md",
      "note_page_text": "6/1/24\\n\\nStarted research phase..."
    }

    Example Args:
    {
      "project_id": "Eco AI"
    }
    """
    try:
        if not project_id:
            error = {"status": "error", "message": "project_id is required"}
            return (False, json.dumps(error, ensure_ascii=False))
        
        base = _base_dir()
        projects = gen.build_projects(base)
        gen.link_notes(base, projects)

        lookup = {pid.lower(): pid for pid in projects.keys()}
        canonical = lookup.get(project_id.lower())
        if canonical is None:
            dn_lookup = {p.display_name.lower(): p.project_id for p in projects.values()}
            canonical = dn_lookup.get(project_id.lower())
        if canonical is None:
            error = {"status": "error", "message": f"Project not found: {project_id}"}
            return (False, json.dumps(error, ensure_ascii=False))

        proj = projects[canonical]
        root_page_path = str(proj.file_path.relative_to(base))
        try:
            root_page_text = proj.file_path.read_text(encoding="utf-8")
        except Exception:
            root_page_text = None

        note_page_path = str(Path(proj.note_file).relative_to(base)) if proj.note_file else None
        if proj.note_file and Path(proj.note_file).exists():
            try:
                note_page_text = Path(proj.note_file).read_text(encoding="utf-8")
            except Exception:
                note_page_text = None
        else:
            note_page_text = None

        result = {
            "status": "success",
            "project_id": canonical,
            "root_page_path": root_page_path,
            "root_page_text": root_page_text,
            "note_page_path": note_page_path,
            "note_page_text": note_page_text
        }
        return (True, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        return (False, json.dumps(error, ensure_ascii=False))


_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2})(?::)?\s*$")


def _parse_frontmatter(lines: List[str]):
    if not lines or lines[0].strip() != "---":
        return [], 0
    fm_lines: List[str] = [lines[0]]
    idx = 1
    while idx < len(lines):
        fm_lines.append(lines[idx])
        if lines[idx].strip() == "---":
            return fm_lines, idx + 1
        idx += 1
    return [], 0


def _iter_note_entries(lines: List[str]):
    current_date: Optional[datetime] = None
    current_header: Optional[str] = None
    current_body: List[str] = []

    def flush():
        nonlocal current_date, current_header, current_body
        if current_date is not None and current_header is not None:
            yield current_date, current_header, current_body[:]
        current_date = None
        current_header = None
        current_body = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        m = _DATE_RE.match(line.strip())
        if m:
            if current_date is not None:
                yield from flush()
            month, day, yy = m.groups()
            year = 2000 + int(yy)
            try:
                current_date = datetime(year, int(month), int(day))
                current_header = line if line.endswith("\\n") else (line + "\\n")
            except ValueError:
                if current_date is not None:
                    current_body.append(line)
        else:
            if current_date is not None:
                current_body.append(line if line.endswith("\\n") else (line + "\\n"))
        idx += 1

    if current_date is not None and current_header is not None:
        yield current_date, current_header, current_body[:]


def _find_notes_files(base_dir: Path) -> List[Path]:
    paths: List[Path] = []
    for pat in ("*Notes.md", "*notes.md"):
        paths.extend(base_dir.rglob(pat))
    seen = set()
    result: List[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def NOTES_GET_notes_by_date_range(start_date: str, end_date: str) -> tuple[bool, str]:
    """
    Return dated note entries within [start_date, end_date] (MM/DD/YY), newest-first.

    Example Prompt: "Find my notes between 06/01/24 and 06/15/24"

    Example Response:
    {
      "status": "success",
      "start_date": "06/01/24",
      "end_date": "06/15/24",
      "entries": [
        {
          "file": "Projects/Eco AI/Notes.md",
          "date": "2024-06-15",
          "date_str": "6/15/24",
          "content": "Completed research phase..."
        }
      ]
    }

    Example Args:
    {
      "start_date": "06/01/24",
      "end_date": "06/15/24"
    }
    """
    def parse_mdyy(s: str) -> datetime:
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2})$", s.strip())
        if not m:
            raise ValueError("Dates must be in MM/DD/YY format")
        month, day, yy = m.groups()
        return datetime(2000 + int(yy), int(month), int(day))

    try:
        start_dt = parse_mdyy(start_date)
        end_dt = parse_mdyy(end_date)
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        return (False, json.dumps(error, ensure_ascii=False))
    
    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt

    try:
        base = _base_dir()
        results: List[Dict[str, Any]] = []
        
        for md_path in _find_notes_files(base):
            try:
                text = md_path.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = [l if l.endswith("\\n") else l + "\\n" for l in text.splitlines(True)]
            _, body_idx = _parse_frontmatter(lines)
            body = lines[body_idx:]

            for dt, header, content_lines in _iter_note_entries(body):
                if start_dt <= dt <= end_dt:
                    content = "".join(content_lines).rstrip("\\n")
                    results.append({
                        "file": str(md_path.relative_to(base)),
                        "date": dt.date().isoformat(),
                        "date_str": header.strip().rstrip(':'),
                        "content": content,
                    })

        results.sort(key=lambda r: r["date"], reverse=True)
        
        result = {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "entries": results
        }
        return (True, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        return (False, json.dumps(error, ensure_ascii=False))


def NOTES_UPDATE_project_note(project_id: str, content: str, section_id: Optional[str] = None) -> tuple[bool, str]:
    """
    Append content to today's dated note entry for a project. Creates file/entry if needed.

    Example Prompt: "Add 'ship MVP' under 'Milestones' for project Eco AI"

    Example Response:
    {
      "status": "success",
      "project_id": "Eco AI",
      "note_file": "Projects/Eco AI/Notes.md",
      "created_file": false,
      "created_entry": true,
      "appended": true,
      "date_str": "11/4/25"
    }

    Example Args:
    {
      "project_id": "Eco AI",
      "content": "Ship MVP by end of month",
      "section_id": "Milestones"
    }
    """
    try:
        if not project_id:
            error = {"status": "error", "message": "project_id is required"}
            return (False, json.dumps(error, ensure_ascii=False))
        if not content:
            error = {"status": "error", "message": "content is required"}
            return (False, json.dumps(error, ensure_ascii=False))

        base = _base_dir()
        projects = gen.build_projects(base)
        gen.link_notes(base, projects)

        lookup = {pid.lower(): pid for pid in projects.keys()}
        canonical_id = lookup.get(project_id.lower())
        if canonical_id is None:
            dn_lookup = {p.display_name.lower(): p.project_id for p in projects.values()}
            canonical_id = dn_lookup.get(project_id.lower())
        if canonical_id is None:
            error = {"status": "error", "message": f"Project not found: {project_id}"}
            return (False, json.dumps(error, ensure_ascii=False))

        proj = projects[canonical_id]

        created_file = False
        if proj.note_file and Path(proj.note_file).exists():
            note_path = Path(proj.note_file)
        else:
            note_path = proj.file_path.parent / "Notes.md"
            if not note_path.exists():
                created_file = True
                note_path.write_text("---\\n" f"note_project_id: {proj.project_id}\\n" "---\\n\\n", encoding="utf-8")

        text = note_path.read_text(encoding="utf-8")
        lines = [l if l.endswith("\\n") else l + "\\n" for l in text.splitlines(True)]

        fm_lines, body_idx = _parse_frontmatter(lines)
        body = lines[body_idx:]

        today = datetime.now()
        m = today.month
        d = today.day
        yy = today.year % 100
        today_str = f"{m}/{d}/{yy:02d}"

        date_indices = [i for i, ln in enumerate(body) if _DATE_RE.match(ln.strip().rstrip(':'))]

        def match_date_line(ln: str) -> bool:
            s = ln.strip()
            if s.endswith(":"):
                s = s[:-1]
            return s == today_str

        first_date_idx = date_indices[0] if date_indices else None
        today_start = None
        for i in date_indices:
            if match_date_line(body[i]):
                today_start = i
                break

        def find_entry_end(start_idx: int) -> int:
            for j in date_indices:
                if j > start_idx:
                    return j
            return len(body)

        created_entry = False
        appended = False

        if today_start is None:
            entry_lines: List[str] = []
            entry_lines.append(today_str + "\\n")
            entry_lines.append("\\n")
            if section_id:
                entry_lines.append(f"## {section_id}\\n\\n")
            content_block = content if content.endswith("\\n") else content + "\\n"
            entry_lines.append(content_block)

            insert_pos = first_date_idx if first_date_idx is not None else len(body)
            new_body = body[:insert_pos] + entry_lines + (body[insert_pos:] if insert_pos is not None else [])
            lines = fm_lines + new_body
            note_path.write_text("".join(lines), encoding="utf-8")
            created_entry = True
        else:
            entry_end = find_entry_end(today_start)

            if section_id:
                sec_pat = re.compile(rf"^\\s*#{{1,6}}\\s+{re.escape(section_id)}\\s*$", re.IGNORECASE)
                sec_start = None
                for idx in range(today_start + 1, entry_end):
                    if sec_pat.match(body[idx].rstrip("\\n")):
                        sec_start = idx
                        break

                if sec_start is None:
                    insert_at = entry_end
                    if insert_at > today_start + 1 and body[insert_at - 1].strip() != "":
                        body.insert(insert_at, "\\n")
                        insert_at += 1
                    body.insert(insert_at, f"## {section_id}\\n")
                    insert_at += 1
                    body.insert(insert_at, "\\n")
                    insert_at += 1
                    content_block = content if content.endswith("\\n") else content + "\\n"
                    body.insert(insert_at, content_block)
                    appended = True
                else:
                    sec_end = entry_end
                    for idx in range(sec_start + 1, entry_end):
                        if re.match(r"^\\s*#{{1,6}}\\s+", body[idx]):
                            sec_end = idx
                            break
                    insert_at = sec_end
                    if insert_at > sec_start + 1 and body[insert_at - 1].strip() != "":
                        body.insert(insert_at, "\\n")
                        insert_at += 1
                    content_block = content if content.endswith("\\n") else content + "\\n"
                    body.insert(insert_at, content_block)
                    appended = True
            else:
                insert_at = entry_end
                if body[insert_at - 1].strip() != "":
                    body.insert(insert_at, "\\n")
                    insert_at += 1
                content_block = content if content.endswith("\\n") else content + "\\n"
                body.insert(insert_at, content_block)
                appended = True

            lines = fm_lines + body
            note_path.write_text("".join(lines), encoding="utf-8")

        result = {
            "status": "success",
            "project_id": canonical_id,
            "note_file": str(note_path.relative_to(base)),
            "created_file": created_file,
            "created_entry": created_entry,
            "appended": appended,
            "date_str": today_str
        }
        return (True, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        return (False, json.dumps(error, ensure_ascii=False))


TOOLS = [
    NOTES_GET_project_hierarchy,
    NOTES_GET_project_text,
    NOTES_GET_notes_by_date_range,
    NOTES_UPDATE_project_note,
]
