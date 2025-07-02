#!/usr/bin/env python3
"""
AC Semiotic Lexical Framework (SLF) — v1.7.4

- All transformation methods from v1.7.1.
- All new features from v1.7.3: SQLite logging, jump_1e, etc.
- 'fullreset' command is NOT included (as in v1.7.3).
"""

from __future__ import annotations
import argparse
import json
import logging
import pathlib
import sys
import unicodedata
import uuid
from datetime import datetime
import time
import sqlite3
from collections import Counter, defaultdict
import pandas as pd

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from time import sleep

console = Console()
previous_outputs = set()

def show_menu():
    menu_table = Table(show_header=False, box=box.ROUNDED, width=60)
    menu_table.add_row("[bold cyan]1a[/bold cyan]", "Symbolic Transform")
    menu_table.add_row("[bold cyan]1b[/bold cyan]", "Phonetic Transform")
    menu_table.add_row("[bold cyan]1c[/bold cyan]", "Acronym Transform")
    menu_table.add_row("[bold cyan]1d[/bold cyan]", "Dictionary Scan")
    menu_table.add_row("[bold cyan]1e[/bold cyan]", "Jump Menu")
    menu_table.add_row("[bold cyan]2[/bold cyan]", "Reverse Transform")
    menu_table.add_row("[bold cyan]3[/bold cyan]", "Manual Enter Seed")
    menu_table.add_row("[bold cyan]4[/bold cyan]", "Up Add")
    menu_table.add_row("[bold cyan]5[/bold cyan]", "Down Remove")
    menu_table.add_row("[bold cyan]7[/bold cyan]", "Select")
    menu_table.add_row("[bold cyan]8[/bold cyan]", "List")
    menu_table.add_row("[bold cyan]9[/bold cyan]", "Tree")
    menu_table.add_row("[bold cyan]10[/bold cyan]", "Branch")
    menu_table.add_row("[bold cyan]11[/bold cyan]", "Description")
    menu_table.add_row("[bold cyan]reset[/bold cyan]", "Reset Working")
    menu_table.add_row("[bold cyan]goto[/bold cyan]", "Goto Node")
    menu_table.add_row("[bold cyan]help[/bold cyan]", "Help")
    menu_table.add_row("[bold cyan]q/quit[/bold cyan]", "Quit")
    console.print(Panel(menu_table, title="[bold green]Main Menu[/bold green]", border_style="green"))

def show_status(engine):
    status = (
        f"[bold magenta]Work:[/bold magenta] [white]{engine.working_seed}[/white]\n"
        f"[bold yellow]Up:[/bold yellow] [white]{engine.up_seed}[/white]\n"
        f"[bold blue]Down:[/bold blue] [white]{engine.down_seed}[/white]\n"
        f"[bold cyan]Node:[/bold cyan] [white]{getattr(engine, 'current_node_id', '?')}[/white]\n"
        f"[bold green]Step:[/bold green] [white]{engine.step}[/white]\n"
        f"[bold red]Branch:[/bold red] [white]{engine.branch}[/white]"
    )
    console.print(Panel(status, title="[bold white]Status[/bold white]", border_style="cyan"))

def print_if_unique(output):
    if output not in previous_outputs:
        console.print(Panel(output, border_style="blue"))
        previous_outputs.add(output)
    else:
        console.print("[yellow]Duplicate output skipped.[/yellow]")

from prompt_toolkit import prompt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SLF-Core")

def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def calc_diff(src, tgt):
    src_c = Counter(src)
    tgt_c = Counter(tgt)
    add = ''.join((tgt_c - src_c).elements())
    rem = ''.join((src_c - tgt_c).elements())
    s = []
    if add: s.append(f"+{add}")
    if rem: s.append(f"-{rem}")
    return " ".join(s)

class TransformEngine:
    def __init__(self, metadata_paths: list[str], seed: str, author: str = None):
        self._startup(metadata_paths, seed, author)

    def _init_db(self):
        self.db_path = "transform_history.db"
        self.conn = sqlite3.connect(self.db_path)
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS transform_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                source TEXT,
                target TEXT,
                reversal BOOLEAN,
                identical BOOLEAN,
                branch TEXT,
                received_up BOOLEAN DEFAULT 0,
                received_down BOOLEAN DEFAULT 0
            )
        ''')
        # Try to add columns if missing
        try:
            c.execute('ALTER TABLE transform_log ADD COLUMN received_up BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE transform_log ADD COLUMN received_down BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        c.execute('CREATE INDEX IF NOT EXISTS idx_branch ON transform_log(branch)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reversal ON transform_log(reversal)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_identical ON transform_log(identical)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_up ON transform_log(received_up)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_down ON transform_log(received_down)')
        self.conn.commit()

    def _log_sqlite(self, source, target, branch, method=""):
        reversal = (target == source[::-1])
        identical = (target == source)
        # Consider all methods that should mark as up/down
        received_up = method.startswith("manual_up") or method == "dictionary" or method == "symbolic_all"
        received_down = method.startswith("manual_down") or method == "dictionary"
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO transform_log (timestamp, source, target, reversal, identical, branch, received_up, received_down)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (now_iso(), source, target, reversal, identical, branch, int(received_up), int(received_down)))
        self.conn.commit()

    def _startup(self, metadata_paths: list[str], seed: str, author: str = None):
        self._init_db()
        if author:
            self.author = author
        else:
            while True:
                try:
                    self.author = prompt("Enter author name: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nAborted.")
                    sys.exit(0)
                if self.author:
                    break
                print("Author name cannot be empty.")

        if seed:
            initial_seed = seed
        else:
            while True:
                try:
                    initial_seed = prompt("Enter initial seed: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nAborted.")
                    sys.exit(0)
                if initial_seed:
                    break
                print("Seed cannot be empty.")

        self.session_id = f"{now_iso()}_{self.author.replace(' ','_')}"
        self.branch = "main"
        self.description = ""
        self.metadata = self._load_metadata(metadata_paths)
        self.wordlist = self._load_wordlist()
        self.tree_log = pathlib.Path("seed_tree.jsonl")  # Changed to relative path
        self.id_base = str(uuid.uuid4())
        self.id_count = 10
        self.working_seed = self._normalize(initial_seed)
        self.branch = getattr(self, 'branch', 'main')
        self.prev_working_seed = self.working_seed
        self.up_seed = ""
        self.down_seed = ""
        self.step = 1
        self.last_action_method = "root"
        self.last_timestamp = time.time()
        self.current_node_id = f"{self.id_base}-{self.id_count}"
        self.parent_id = None

        if not self.tree_log.exists() or self.tree_log.stat().st_size == 0:
            self._log_node(
                source="root",
                target=self.working_seed,
                parent_id=None,
                method="root",
                up="",
                down="",
                description="Initial root node"
            )

    def _normalize(self, text: str) -> str:
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()

    def _load_metadata(self, paths: list[str]) -> pd.DataFrame:
        self.metadata_paths = paths
        dfs: list[pd.DataFrame] = []
        for p in paths:
            fp = pathlib.Path(p)
            if not fp.exists():
                logger.warning(f"Metadata file not found: {fp}")
                continue
            try:
                df = pd.read_parquet(fp)
            except Exception as e:
                logger.warning(f"Failed to load {p}: {e}")
                continue
            if "source" in df.columns:
                dfs.append(df)
            elif "character_id" in df.columns:
                rows = []
                for _, row in df.iterrows():
                    for t in row["character_transforms"]:
                        rows.append({
                            "source": self._normalize(t["source"]),
                            "target": self._normalize(t["target"]),
                            "context": t.get("context", ""),
                            "method": t.get("method", ""),
                            "weight": t.get("weight", 0),
                            "logographic_ref": t.get("logographic_ref")
                        })
                dfs.append(pd.DataFrame(rows))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=["source","target","context","method","weight","logographic_ref"])

    def _load_wordlist(self) -> list[str]:
        for name in ("large_wordlist.txt", "wordlist.txt"):
            fp = pathlib.Path(name)
            if fp.exists():
                try:
                    lines = fp.read_text(encoding="utf-8").splitlines()
                except Exception as e:
                    logger.warning(f"Unable to read wordlist {name}: {e}")
                    continue
                words = sorted({w.strip().lower() for w in lines if w.strip()})
                if not words:
                    logger.warning(f"{name} is empty.")
                return words
        logger.warning("No wordlist found; dictionary disabled.")
        return []

    def _is_subsequence(self, small: str, big: str) -> bool:
        it = iter(big)
        return all(c in it for c in small)

    def load_tree(self) -> dict[str, dict]:
        nodes: dict[str, dict] = {}
        if self.tree_log.exists():
            for line in self.tree_log.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    n = json.loads(line)
                    nodes[n["id"]] = n
                except Exception as e:
                    logger.warning(f"Skipping invalid log line: {e}")
        return nodes

    def _next_id(self):
        self.id_count += 1
        return f"{self.id_base}-{self.id_count}"

    def _log_node(self, source, target, parent_id, method, up="", down="", description=None):
        timestamp = now_iso()
        duration = round(time.time() - self.last_timestamp, 3)
        self.last_timestamp = time.time()
        diff = calc_diff(source, target)
        node = {
            "id": self.current_node_id,
            "parent_id": parent_id,
            "session_id": self.session_id,
            "branch": self.branch,
            "author": self.author,
            "timestamp": timestamp,
            "duration": f"{duration}s",
            "step": self.step,
            "source": source,
            "target": target,
            "up_seed": up,
            "down_seed": down,
            "method": method,
            "diff": diff,
            "description": description if description is not None else self.description
        }
        with self.tree_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")

    def _commit_node(self):
        prev_id = self.current_node_id
        new_id = self._next_id()
        self._log_node(
            source=self.prev_working_seed,
            target=self.working_seed,
            parent_id=prev_id,
            method=self.last_action_method or "",
            up=self.up_seed,
            down=self.down_seed
        )
        # Log to sqlite, pass method for up/down mark
        self._log_sqlite(self.prev_working_seed, self.working_seed, self.branch, self.last_action_method or "")
        self.current_node_id = new_id
        self.parent_id = prev_id
        self.step += 1
        self.last_action_method = None
        self.description = ""
        self.prev_working_seed = self.working_seed
        logger.info(f"Committed node {new_id}")

    # --- Begin: Transform methods from 1.7.1 ---
    def get_options(self, char: str, method: str) -> pd.DataFrame:
        return self.metadata[
            (self.metadata["source"] == char) &
            (self.metadata["method"] == method)
        ].sort_values("weight", ascending=False)

    def symbolic_transform(self):
        c = prompt("Letter to transform > ").strip().lower()
        if len(c) != 1:
            print("Enter a single letter.")
            return
        opts = self.get_options(c, "symbolic")
        if opts.empty:
            print("No symbolic transforms.")
            return
        for i, row in enumerate(opts.itertuples(), 1):
            print(f"{i}. {row.source}\u2192{row.target} [{row.context}, w={row.weight}]")
        pick = prompt("Pick (number) > ").strip()
        if not (pick.isdigit() and 1 <= int(pick) <= len(opts)):
            return
        t = opts.iloc[int(pick) - 1]
        positions = [i for i, ch in enumerate(self.working_seed) if ch == c]
        if not positions:
            print(f"No '{c}' found in working seed.")
            return
        if len(positions) == 1:
            pos = positions[0]
            self.prev_working_seed = self.working_seed
            s = self.working_seed
            self.working_seed = s[:pos] + t.target + s[pos+1:]
            self.last_action_method = "symbolic"
            print(f"Updated Working Seed: {self.working_seed}")
            return
        print("Multiple occurrences found:")
        for idx, pos in enumerate(positions, 1):
            preview = self.working_seed[:pos] + t.target + self.working_seed[pos+1:]
            print(f"{idx}. Replace at position {pos}: {preview}")
        print("a. Apply to all")
        pos_pick = prompt(f"Pick position (1-{len(positions)}) or 'a' for all > ").strip().lower()
        self.prev_working_seed = self.working_seed
        s = self.working_seed
        if pos_pick == 'a':
            s_list = list(s)
            for pos in positions:
                s_list[pos] = t.target
            self.working_seed = "".join(s_list)
            self.last_action_method = "symbolic_all"
            print(f"Updated Working Seed (all): {self.working_seed}")
        elif pos_pick.isdigit() and 1 <= int(pos_pick) <= len(positions):
            pos = positions[int(pos_pick)-1]
            self.working_seed = s[:pos] + t.target + s[pos+1:]
            self.last_action_method = "symbolic"
            print(f"Updated Working Seed: {self.working_seed}")
        else:
            print("Invalid selection.")
        self._commit_node()  # PATCH: always commit on transform

    def phonetic_transform(self):
        c = prompt("Letter for phonetic > ").strip().lower()
        if len(c) != 1:
            print("Enter a single letter.")
            return
        opts = self.get_options(c, "phonetic")
        if opts.empty:
            print("No phonetic transforms.")
            return
        for i, row in enumerate(opts.itertuples(), 1):
            print(f"{i}. {row.source}\u2192{row.target} [{row.context}, w={row.weight}]")
        pick = prompt("Pick (number) > ").strip()
        if not (pick.isdigit() and 1 <= int(pick) <= len(opts)):
            return
        t = opts.iloc[int(pick) - 1]
        positions = [i for i, ch in enumerate(self.working_seed) if ch == c]
        if not positions:
            print(f"No '{c}' found in working seed.")
            return
        for idx, pos in enumerate(positions, 1):
            preview = self.working_seed[:pos] + t.target + self.working_seed[pos+1:]
            print(f"{idx}. Replace at position {pos}: {preview}")
        pos_pick = prompt("Pick position (number) > ").strip()
        if not (pos_pick.isdigit() and 1 <= int(pos_pick) <= len(positions)):
            return
        pos = positions[int(pos_pick) - 1]
        self.prev_working_seed = self.working_seed
        s = self.working_seed
        self.working_seed = s[:pos] + t.target + s[pos+1:]
        self.last_action_method = "phonetic"
        print(f"Updated Working Seed: {self.working_seed}")
        self._commit_node()  # PATCH: always commit on transform

    def acronym_transform(self):
        s = self.working_seed
        blocks: list = []
        for i in range(len(s)):
            for j in range(i + 2, len(s) + 1):
                blk = s[i:j]
                rows = self.metadata[
                    (self.metadata["source"] == blk) &
                    (self.metadata["method"] == "acronym")
                ]
                if not rows.empty:
                    blocks.append((blk, i, rows))
        if not blocks:
            print("No acronym matches.")
            return
        for idx, (blk, pos, rows) in enumerate(blocks, 1):
            print(f"[{idx}] '{blk}' at pos {pos}:")
            for j, row in enumerate(rows.itertuples(), 1):
                print(f"  {j}. {row.source}\u2192{row.target} [{row.context}, w={row.weight}]")
        sel = prompt("Pick [blk] [xfrm] > ").split()
        if len(sel) == 2 and sel[0].isdigit() and sel[1].isdigit():
            b, x = int(sel[0]) - 1, int(sel[1]) - 1
            blk, pos, rows = blocks[b]
            t = rows.iloc[x]
            self.prev_working_seed = self.working_seed
            self.working_seed = s[:pos] + t.target + s[pos + len(blk):]
            self.last_action_method = "acronym"
            print(f"Updated Working Seed: {self.working_seed}")
        self._commit_node()  # PATCH: always commit on transform

    def smart_dict_scan(self):
        s = self.working_seed
        if not self.wordlist:
            print("Wordlist empty.")
            return
        candidates: list = []
        MAX_FRAG_LEN = 6
        MAX_CANDIDATES = 50
        self._commit_node()  # PATCH: always commit on transform

        fragments = set()
        for i in range(len(s)):
            for j in range(i + 2, min(len(s), i + MAX_FRAG_LEN) + 1):
                fragments.add(s[i:j])
        fragments.add(s)

        for w in self.wordlist:
            if abs(len(w) - len(s)) > 10:
                continue
            for frag in fragments:
                if len(frag) < 2:
                    continue
                if self._is_subsequence(frag, w) or self._is_subsequence(w, frag):
                    up = ''.join((Counter(w) - Counter(frag)).elements())
                    down = ''.join((Counter(frag) - Counter(w)).elements())
                    if len(up) <= 4 and len(down) <= 3:
                        pos = s.find(frag) if frag in s else 0
                        candidates.append((frag, w, pos, up, down))
                        if len(candidates) >= MAX_CANDIDATES:
                            break
            if len(candidates) >= MAX_CANDIDATES:
                break

        if not candidates:
            print("No fuzzy matches found.")
            return
        for idx, (frag, full_word, pos, up, down) in enumerate(candidates, 1):
            print(f"{idx}. Replace '{frag}' at pos {pos} with '{full_word}' (up:'{up}', down:'{down}')")
        pick = prompt("Pick (num) > ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(candidates):
            f, full, pos, up, down = candidates[int(pick) - 1]
            self.prev_working_seed = self.working_seed
            self.up_seed += up
            self.down_seed += down
            self.working_seed = s[:pos] + full + s[pos + len(f):]
            self.last_action_method = "dictionary"
            print(f"Updated Working Seed: {self.working_seed}")
            self._commit_node()  # PATCH: Always log after dictionary transform

    def select(self):
        try:
            ch = prompt("Select [1=up,2=wrk,3=down]>").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        branch_id = self._next_id()
        prev_id = self.current_node_id
        prev_seed = self.working_seed
        desc = None
        if ch == '1' and self.up_seed:
            self.prev_working_seed = self.working_seed
            self.working_seed = self.up_seed
            self.last_action_method = "select_up"
            desc = "Branch to up seed"
            self.up_seed = ""
            self.down_seed = ""
        elif ch == '3' and self.down_seed:
            self.prev_working_seed = self.working_seed
            self.working_seed = self.down_seed
            self.last_action_method = "select_down"
            desc = "Branch to down seed"
            self.up_seed = ""
            self.down_seed = ""
        elif ch == '2':
            self.last_action_method = "select_working"
            print("Working seed unchanged.")
            return
        else:
            print("Invalid selection.")
            return
        self.current_node_id = branch_id
        self.parent_id = prev_id
        self._log_node(
            source=prev_seed,
            target=self.working_seed,
            parent_id=prev_id,
            method=self.last_action_method,
            up=self.up_seed,
            down=self.down_seed,
            description=desc
        )
        print(f"Now: {self.working_seed}")

    def add_description(self):
        try:
            desc = prompt("Enter description for next commit > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        if desc:
            self.description = desc
            print(f"Description set for next commit: {desc}")
        self._commit_node()  # PATCH: always commit on description change

    def set_branch(self):
        try:
            branch = prompt("Enter branch name/tag > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        if branch:
            self.branch = branch
            print(f"Branch/tag set: {branch}")

    def print_list(self):
        if not self.tree_log.exists():
            print("No nodes.")
            return
        for line in self.tree_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            node = json.loads(line)
            print(json.dumps(node, ensure_ascii=False))

    def print_tree(self):
        nodes = self.load_tree()
        children = {}
        for nid, n in nodes.items():
            p = n.get("parent_id")
            if p not in children: children[p] = []
            children[p].append(nid)
        def walk(nid, depth=0):
            if nid not in nodes: return
            n = nodes[nid]
            print("  " * depth + f"{nid[-2:]}: {n['source']} \u2192 {n['target']} [{n.get('branch','')}] ({n.get('description','')})")
            for child in children.get(nid, []):
                walk(child, depth+1)
        roots = [nid for nid, n in nodes.items() if n["parent_id"] is None]
        for r in roots: walk(r)

    def reset_working(self):
        nodes = self.load_tree()
        if self.current_node_id in nodes:
            n = nodes[self.current_node_id]
            self.working_seed = n['target']
            self.prev_working_seed = self.working_seed
            self.up_seed = n.get('up_seed', '')
            self.down_seed = n.get('down_seed', '')
            self.step = n.get('step', 1)
            print(f"Reset to: {self.working_seed}")

    def help(self):
        print("""
Help — SLF Menu Commands:
[1a sym]         : Symbolic transform (Parquet-driven letter/meaning transform)
[1b phon]        : Phonetic transform (Parquet-driven)
[1c acr]         : Acronym transform (Parquet-driven)
[1d dict]        : Smart dictionary scan and fix (add/remove letters for match)
[1e jump]        : Fast hash-powered jump excluding reversals/identicals/up/down
[2 rev]          : Reverse the working seed
[3 enter]        : Enter a new seed (resets state)
[4 up/add]       : Manually append letters to working seed (Up Seed)
[5 down/remove]  : Remove letters from working seed (Down Seed)
[/commit]  : Commit current node (increments step/ID and logs all details)
[7 select]       : Switch working seed to Up, Down, or remain (branches log if Up/Down)
[8 list]         : Print all nodes in the JSONL log
[9 tree]         : Print log as a tree (parent/child indented)
[10 branch]      : Set or tag the current branch
[11 desc]        : Add/edit description for next commit
[reset]          : Reset working, up, down to current node in log
[goto]           : Jump to any previous node by ID
[q quit]         : Quit
[help]           : This help menu
""")

    def reverse_transform(self):
        self.prev_working_seed = self.working_seed
        self.working_seed = self.working_seed[::-1]
        self.last_action_method = "reverse"
        print(f"Reversed: {self.working_seed}")
        self._commit_node()  # PATCH: always commit on transform

    def manual_enter_seed(self):
        if hasattr(self, 'branch'):
            self.branch = getattr(self, 'branch', 'main')
        try:
            s = prompt("New seed >").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        if s:
            self.prev_working_seed = self.working_seed
            self.working_seed = self._normalize(s)
            self.last_action_method = "manual"
            print(f"New Working Seed: {self.working_seed}")
        self._commit_node()  # PATCH: always commit on transform

    def manual_up_add(self):
        try:
            up = prompt("Add letters (up) >").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        if up:
            s = self.working_seed
            print(f"Current working seed: {s}")
            positions = list(range(len(s)+1))
            for idx, pos in enumerate(positions):
                preview = s[:pos] + up + s[pos:]
                print(f"{idx+1}. Insert at pos {pos}: {preview}")
            pos_input = prompt(f"Pick position to insert (1-{len(positions)}) > ").strip()
            if not (pos_input.isdigit() and 1 <= int(pos_input) <= len(positions)):
                print("Invalid position.")
                return
            pos = positions[int(pos_input)-1]
            self.prev_working_seed = s
            self.up_seed += up
            self.working_seed = s[:pos] + up + s[pos:]
            self.last_action_method = "manual_up"
            print(f"Added (up): {up} at {pos} => {self.working_seed}")
        self._commit_node()  # PATCH: always commit on transform

    def manual_down_remove(self):
        try:
            down = prompt("Remove letter (down, single char) >").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        if down:
            s = self.working_seed
            positions = [i for i, c in enumerate(s) if c == down]
            if not positions:
                print(f"No '{down}' found in working seed.")
                return
            for idx, pos in enumerate(positions):
                preview = s[:pos] + s[pos+1:]
                print(f"{idx+1}. Remove at pos {pos}: {preview}")
            pos_input = prompt(f"Pick position to remove (1-{len(positions)}) > ").strip()
            if not (pos_input.isdigit() and 1 <= int(pos_input) <= len(positions)):
                print("Invalid position.")
                return
            pos = positions[int(pos_input)-1]
            self.prev_working_seed = s
            self.down_seed += down
            self.working_seed = s[:pos] + s[pos+1:]
            self.last_action_method = "manual_down"
            print(f"Removed (down): {down} at {pos} => {self.working_seed}")
        self._commit_node()  # PATCH: always commit on transform

    def goto(self):
        nodes = self.load_tree()
        if not nodes:
            print("No nodes.")
            return
        node_list = list(nodes.items())
        print("Available nodes:")
        for idx, (nid, n) in enumerate(node_list, 1):
            print(f"{idx}. {nid}|{n['source']}\u2192{n['target']}|step={n['step']}|method={n['method']}")
        try:
            sel = prompt("Pick node by number or enter node id > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
        if sel.isdigit() and 1 <= int(sel) <= len(node_list):
            goto_id = node_list[int(sel) - 1][0]
        else:
            goto_id = sel
        if goto_id not in nodes:
            print("Node id not found.")
            return
        n = nodes[goto_id]
        self.branch = n.get('branch', 'main')
        self.working_seed = n['target']
        self.prev_working_seed = self.working_seed
        self.current_node_id = n['id']
        self.up_seed = n.get('up_seed', '')
        self.down_seed = n.get('down_seed', '')
        self.step = n.get('step', 1)
        print(f"Moved to node {goto_id}. Working: {self.working_seed} | Up: {self.up_seed} | Down: {self.down_seed} | Step: {self.step}")

    # --- End: Transform methods from 1.7.1 ---

    # --- Begin: 1.7.3 unique methods ---
    def jump_1e(self):
        """Provide fast hash-based jump menu for roots and major transforms.
        Exclude reversals, identicals, and any seed that has received up or down."""
        c = self.conn.cursor()
        # Find all seeds that have received an up or down
        c.execute('SELECT DISTINCT source FROM transform_log WHERE received_up=1 OR received_down=1')
        received_mod_sources = {row[0] for row in c.fetchall()}
        c.execute('SELECT DISTINCT target FROM transform_log WHERE received_up=1 OR received_down=1')
        received_mod_targets = {row[0] for row in c.fetchall()}
        received_mod = received_mod_sources | received_mod_targets

        # Only include entries that are not reversals, not identicals, and not in received_mod
        c.execute('SELECT DISTINCT source, target, branch, reversal, identical FROM transform_log')
        root_map = defaultdict(list)
        for source, target, branch, reversal, identical in c.fetchall():
            if reversal or identical:
                continue
            if source in received_mod or target in received_mod:
                continue
            root_map[source].append((target, branch))
        if not root_map:
            print("No jumpable entries.")
            return
        roots = list(root_map.keys())
        print("Jump roots:")
        for i, r in enumerate(roots, 1):
            print(f"{i}. {r} ({len(root_map[r])} transforms)")
        sel = input("Jump to root by number: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(roots):
            root = roots[int(sel)-1]
            print(f"Targets for {root}:")
            targets = root_map[root]
            for j, (tgt, branch) in enumerate(targets, 1):
                print(f"  {j}. {tgt} [{branch}]")
            subsel = input("Jump to target by number: ").strip()
            if subsel.isdigit() and 1 <= int(subsel) <= len(targets):
                chosen_target, chosen_branch = targets[int(subsel)-1]
                print(f"Jump: {root} \u2192 {chosen_target} [{chosen_branch}]")
                self.working_seed = chosen_target
                self.branch = chosen_branch
                print(f"Working seed set to {chosen_target}, branch {chosen_branch}")

    def close(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

def interactive_loop(engine: TransformEngine):
    cmds = (
        "[1a sym 1b phon 1c acr 1d dict 1e jump "
        "2 rev 3 enter 4 up add 5 down remove 7 select 8 list 9 tree 10 branch 11 desc reset goto help q quit]> "
    )
    while True:
        console.rule("[bold blue]SLF CLI[/bold blue]")
        show_status(engine)
        show_menu()
        try:
            cmd = prompt(cmds).strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[red]Session ended.[/red]")
            break
        last_output = None
        if cmd == '1a': last_output = engine.symbolic_transform()
        elif cmd == '1b': last_output = engine.phonetic_transform()
        elif cmd == '1c': last_output = engine.acronym_transform()
        elif cmd == '1d': last_output = engine.smart_dict_scan()
        elif cmd == '1e': last_output = engine.jump_1e()
        elif cmd == '2': last_output = engine.reverse_transform()
        elif cmd == '3': last_output = engine.manual_enter_seed()
        elif cmd in ('4','up','add'): last_output = engine.manual_up_add()
        elif cmd in ('5','down','remove'): last_output = engine.manual_down_remove()
        elif cmd in ('7','select'): last_output = engine.select()
        elif cmd in ('8','list'): last_output = engine.print_list()
        elif cmd in ('9','tree'): last_output = engine.print_tree()
        elif cmd in ('10','branch'): last_output = engine.set_branch()
        elif cmd in ('11','desc','description'): last_output = engine.add_description()
        elif cmd == 'reset': last_output = engine.reset_working()
        elif cmd == 'goto': last_output = engine.goto()
        elif cmd == 'help': last_output = engine.help()
        elif cmd in ('q','quit'): break
        else: console.print("[red]Unknown command.[/red]")
        if last_output: print_if_unique(str(last_output))
    engine.close()
    console.print("[bold green]Bye.[/bold green]")
    print("Bye.")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--metadata', nargs='+', default=['character_transforms.parquet', 'acronym_transforms.parquet', 'phonetic_transforms.parquet'])
    ap.add_argument('-s', '--seed', default='')
    ap.add_argument('--author', default=None, help='Author name for logging')
    args = ap.parse_args()
    engine = TransformEngine(args.metadata, args.seed, args.author)
    interactive_loop(engine)