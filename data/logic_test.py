import json
import itertools

# --- Load transforms from JSON ---
with open("character_transforms.json", encoding="utf-8") as f:
    transforms_data = json.load(f)

# Build lookup: {char: [transform-dict, ...]}
char_to_transforms = {}
for entry in transforms_data:
    char = entry["character_id"].lower()
    char_to_transforms[char] = entry["character_transforms"]

def select_transform_for_char(char, transforms):
    print(f"\nAvailable transforms for '{char}':")
    for idx, t in enumerate(transforms):
        logog = " [LOGOGRAPHIC]" if t.get("method") == "logographic" else ""
        logoref = f" logographic_ref: {t.get('logographic_ref', 'None')}"
        print(
            f"{idx+1}. {t['target']} (context: {t.get('context','')}, method: {t.get('method','')}, weight: {t.get('weight','')}){logog}{logoref}"
        )

    print("0. Use all with weight 1.0")
    print("-1. Use all transforms")
    print("-2. Exclude all logographic transforms")
    print("-3. ONLY logographic transforms")
    sel = input(f"Select transform for '{char}' (number, 0, -1, -2, or -3): ")
    if sel == "0":
        return [t for t in transforms if t.get('weight') == 1.0] or transforms
    elif sel == "-1":
        return transforms
    elif sel == "-2":
        filtered = [t for t in transforms if t.get("method") != "logographic"]
        return filtered if filtered else transforms
    elif sel == "-3":
        filtered = [t for t in transforms if t.get("method") == "logographic"]
        return filtered if filtered else transforms
    else:
        try:
            idx = int(sel) - 1
            return [transforms[idx]]
        except Exception:
            print("Invalid selection, using all weight 1.0 by default.")
            return [t for t in transforms if t.get('weight') == 1.0] or transforms

def get_char_choices(seed):
    selected = []
    for c in seed.lower():
        transforms = char_to_transforms.get(c, [])
        if not transforms:
            print(f"No transforms for '{c}', using as-is.")
            selected.append([{'target': c, 'weight': 1.0}])
        else:
            choice = select_transform_for_char(c, transforms)
            selected.append(choice)
    return selected

def run_combinations(selected):
    lists = [[t['target'] for t in group] for group in selected]
    for combo in itertools.product(*lists):
        yield "".join(combo)

# --- Main interaction ---
seed = input("Enter seed phrase: ").strip().lower()
selected = get_char_choices(seed)

print("\nSample brute-force results (first 20):")
for i, combo in enumerate(run_combinations(selected)):
    print(combo)
    if i > 19:
        print("...etc...")
        break