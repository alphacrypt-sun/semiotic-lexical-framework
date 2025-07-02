import json
from pathlib import Path
from collections import defaultdict

class SLFNltk:
    def __init__(self, base_path):
        self.phonetic = self._load_json(base_path / "phonetic_transforms_seed.json")
        self.metadata = self._load_json(base_path / "character_metadata.json")
        self._build_lookups()

    def _load_json(self, path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _build_lookups(self):
        self.phonetic_lookup = {}
        for entry in self.phonetic:
            cid = entry["character_id"].lower()
            self.phonetic_lookup.setdefault(cid, []).append(entry)
        self.metadata_lookup = {
            entry["character_id"].lower(): entry
            for entry in self.metadata
        }
        self.seed_tree = {}

    def explain_character(self, char):
        cid = char.lower()
        return {
            "character": cid,
            "metadata": self.metadata_lookup.get(cid, {}),
            "phonetic": self.phonetic_lookup.get(cid, [])
        }

    def find_transforms(self, phrase):
        phrase = phrase.lower()
        results = {}
        for char in phrase:
            if char in self.metadata_lookup:
                results[char] = self.metadata_lookup[char].get("character_transforms", [])
        return results

    def load_seed_tree(self, jsonl_path):
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line.strip())
                key = obj.get("input", "").lower()
                if key:
                    self.seed_tree.setdefault(key, []).append(obj)

    def query_seed_tree(self, term):
        return self.seed_tree.get(term.lower(), [])

    def generate_symbolic_narrative(self, term):
        weight_map = defaultdict(float)
        transforms = self.find_transforms(term)
        for char, entries in transforms.items():
            for entry in entries:
                label = entry.get("logographic_ref", entry.get("target"))
                weight = entry.get("weight", 1.0)
                weight_map[label] += weight

        for seed in self.query_seed_tree(term):
            if "chain" in seed:
                for step in seed["chain"]:
                    if "target" in step:
                        label = step.get("logographic_ref", step["target"])
                        weight_map[label] += 1.0  # fixed flat weight

        if not weight_map:
            return f"No symbolic meaning could be generated for '{term}'."

        sorted_items = sorted(weight_map.items(), key=lambda x: x[1], reverse=True)
        core = sorted_items[:3]
        summary = [f"The term '{term}' unfolds symbolically across cultural layers."]
        symbols = ", ".join(sym for sym, _ in core)
        summary.append(f"It most consistently links to the concepts of {symbols}.")
        summary.append("This suggests a symbolic profile shaped by linguistic, cultural, and mythological resonance.")
        return "\n".join(summary)

    def explain_symbolic_weights(self, term):
        weight_map = defaultdict(float)
        transforms = self.find_transforms(term)
        for char, entries in transforms.items():
            for entry in entries:
                label = entry.get("logographic_ref", entry.get("target"))
                weight = entry.get("weight", 1.0)
                weight_map[label] += weight

        for seed in self.query_seed_tree(term):
            if "chain" in seed:
                for step in seed["chain"]:
                    if "target" in step:
                        label = step.get("logographic_ref", step["target"])
                        weight_map[label] += 1.0  # fixed weight for seed items

        if not weight_map:
            return f"No data available for symbolic breakdown of '{term}'."

        sorted_items = sorted(weight_map.items(), key=lambda x: x[1], reverse=True)
        narrative = [f"Symbolic weight breakdown for '{term}':"]
        for symbol, weight in sorted_items:
            narrative.append(f"- '{symbol}' (aggregated weight: {weight:.2f})")

        narrative.append("\nWeights reflect certainty derived from symbolic and seed associations.")
        return "\n".join(narrative)

if __name__ == "__main__":
    slf = SLFNltk(Path("./data"))  # Adjust path as needed
    slf.load_seed_tree(Path("./data/seed_tree.jsonl"))

    term = input("Enter a word or phrase to generate symbolic narrative: ").strip()
    print("\nSYMBOLIC NARRATIVE:")
    print(slf.generate_symbolic_narrative(term))

    debug = input("\nShow how narrative was built? (y/n): ").strip().lower()
    if debug == "y":
        print("\nSYMBOLIC BREAKDOWN:")
        print(slf.explain_symbolic_weights(term))
