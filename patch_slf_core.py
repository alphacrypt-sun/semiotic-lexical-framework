import shutil

TARGET = "slf_core_v1.7.5.py"
BACKUP = TARGET + ".bak6"

# Backup
shutil.copyfile(TARGET, BACKUP)

with open(TARGET, "r", encoding="utf-8") as f:
    lines = f.readlines()

def patch_goto(lines):
    """Ensure self.branch is set in goto function when moving to a node."""
    out = []
    in_goto = False
    for idx, line in enumerate(lines):
        out.append(line)
        if line.strip().startswith("def goto("):
            in_goto = True
        if in_goto and "n = nodes[goto_id]" in line:
            indent = line[:len(line) - len(line.lstrip())]
            # Insert after: n = nodes[goto_id]
            out.append(f"{indent}self.branch = n.get('branch', 'main')\n")
        # End function
        if in_goto and line.strip().startswith("def ") and not line.strip().startswith("def goto("):
            in_goto = False
    return out

def patch_jump_1e(lines):
    """Ensure self.branch is set in jump_1e function after jump."""
    out = []
    in_jump = False
    for idx, line in enumerate(lines):
        # Find jump_1e function
        if line.strip().startswith("def jump_1e("):
            in_jump = True
        # Patch inside jump_1e
        if in_jump and "print(f\"Jump: {root} \u2192 {chosen_target} [{chosen_branch}]\")" in line:
            indent = line[:len(line) - len(line.lstrip())]
            # Remove old branch/seed set lines if present
            skip = 0
            for nextline in lines[idx+1:idx+5]:
                if ("self.working_seed" in nextline or "self.branch" in nextline or "print(f\"Working seed set to" in nextline):
                    skip += 1
                else:
                    break
            # Insert new logic
            out.append(line)
            out.append(f"{indent}self.working_seed = chosen_target\n")
            out.append(f"{indent}self.branch = chosen_branch\n")
            out.append(f"{indent}print(f\"Working seed set to {{chosen_target}}, branch {{chosen_branch}}\")\n")
            in_jump = False  # Only patch once per function
            # Skip lines that were replaced
            continue
        out.append(line)
    return out

def patch_manual_enter_seed(lines):
    """Ensure self.branch is set in manual_enter_seed if seed menu changes branch."""
    # For now, just ensure it's set to current branch at the function's start, if needed
    out = []
    in_func = False
    for line in lines:
        out.append(line)
        if line.strip().startswith("def manual_enter_seed("):
            in_func = True
            indent = line[:len(line) - len(line.lstrip())] + "    "
            out.append(f"{indent}if hasattr(self, 'branch'):\n{indent}    self.branch = getattr(self, 'branch', 'main')\n")
        if in_func and line.strip().startswith("def ") and not line.strip().startswith("def manual_enter_seed("):
            in_func = False
    return out

def patch_startup(lines):
    """Ensure self.branch is set at program start."""
    out = []
    for line in lines:
        out.append(line)
        if "self.working_seed = self._normalize(initial_seed)" in line:
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f"{indent}self.branch = getattr(self, 'branch', 'main')\n")
    return out

# Apply patches
lines = patch_goto(lines)
lines = patch_jump_1e(lines)
lines = patch_manual_enter_seed(lines)
lines = patch_startup(lines)

with open(TARGET, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Patch applied! Backup is in", BACKUP)