# Semiotic Lexical Framework (SLF)

## Overview

The **Semiotic Lexical Framework (SLF)** is a Python toolkit for interactively mining **symbolic, phonetic, and conceptual information** from lexical input. Whether analyzing a single letter, phrase, or complex character chain, SLF enables users to trace transformations, uncover hidden semantic layers, and build transformation trees rooted in symbolic logic.

Ideal for linguists, cryptographers, symbolic analysts, and researchers in esoteric linguistics or semiotic systems.

---

## 🔑 Features

- **Symbolic Mining Engine**: Decodes letters and fragments into cultural, mythic, and logographic meanings.
- **Interactive CLI**: Perform symbolic, phonetic, acronym, and dictionary-based transformations via an intuitive command-line interface.
- **Tree-Based Seed Management**: Log and navigate transformations as a dynamic tree structure with branching.
- **Rich Logging**: Persistent state tracking via `SQLite` and `JSONL`.
- **Custom Metadata Integration**: Works with character-level symbolic datasets and acronym mappings.

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the SLF Interactive Engine

```bash
python slf_transform_modual_interactive_v.0.0.3.py
```

### 3. Follow CLI Prompts

You’ll be asked to input a seed and metadata source. From there, you can:
- Select symbolic, phonetic, or acronym transformations
- Apply dictionary scans
- Reverse the seed
- Navigate up/down/branch through transformations

---

## 🔍 Typical Use Cases

- Mine symbolic meanings from individual letters or full words.
- Analyze mythic or logographic shifts (e.g., `"a" → "man" → "ren" → "kami"`).
- Track phonetic transformations or acronym expansions.
- Use SLF as a recursive story-generation or code-cracking engine.
- Export full transformation trees for downstream processing.

---

## 🔁 Transformation Modes (CLI Commands)

- `1a` — Symbolic Transform
- `1b` — Phonetic Transform
- `1c` — Acronym Transform
- `1d` — Dictionary Scan
- `1e` — Jump Menu (non-reversals)
- `2` — Reverse Transform
- `3` — Manual Seed Entry
- `4` — Up Add (insert chars)
- `5` — Down Remove (delete chars)
- `7` — Select Branch (up/down)
- `8` — List All Nodes
- `9` — View Tree
- `10` — Set Branch Tag
- `11` — Add Node Description
- `goto` — Go to Previous Node
- `reset` — Reset Working State

---

## 🧠 About

SLF is designed to mine **deep symbolic structures** in language — whether for **linguistic analysis**, **cultural decryption**, or **semiotic storytelling**. It supports conceptual layering from phonetics to mythic coding.

---

## 📜 License

MIT License — free to use, modify, and share.

---

## 🌱 Example

A single letter `a` might transform symbolically as:

```plaintext
a → man → ren → shen → alpha → origin → apple
```

Each transformation includes cultural context (e.g., "Chinese", "Egyptian") and weight metadata.

---

For advanced usage, see the `character_transforms.json` and `acronym_transforms.json` files for symbolic mappings and abbreviation handling.
