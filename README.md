# AC Semiotic Lexical Framework (SLF) — v1.1.0

## What the **AC Semiotic Lexical Framework (SLF)** *is* — in depth

1. **Symbol-centric correlation engine**
   - At its core SLF treats every glyph, digraph, or word as a *symbolic node* rather than a mere string of letters. It explores meaning by walking outward through curated rule-sets, creating a branching semantic graph.

2. **Multi-layer transform system**
   - **Symbolic transforms** – mythic, cultural, or archetypal. Shifts to be added for charater mined semantics. (e.g., *A → ox → strength*).
   - **Logographic transforms** –roman charaters mapped to pinyin/romaji dictionary gloss (*A → 人 → “ren” or man in Chinese).
   - **Phonetic transforms** – IPA-guided sound-symbolic swaps (*/p/ ↔ /ʀ/*, Grimm shifts, etc.).
   - **Acronym swaps** – parses capitals or syllable initials into new compressed forms (*NASA → space, flight, etc.*).
   - **Ups / downs (letter additions & deletions)** – expand or contract a word to surface hidden subwords (*man → m-a-n, + i, main,).
   - **Embedded-word insertions** – splice dictionary words inside others to expose layered phrases (*plowMANmound*).

3. **Recursive story-tree builder**
   - Every transform spawns a child node; each child can itself sprout new branches. The result is a *semantic tree* that captures multiple, co-existing interpretation paths for any starting term.

4. **History-preserving workflow**
   - SLF logs each hop (rule id, method, weight, parent id) so entire chains can be replayed, scored, or visualised later. Think Git commit history for meaning.

5. **Hybrid data foundations**
   - Combines hand-curated mythological tables, IPA rule packs, and large dictionaries to balance expert knowledge with breadth.

6. **Real-time exploratory REPL**
   - A text-mode interface lets researchers seed a word, pick preferred branches, apply filters (method, weight), and watch the tree grow live.

7. **Pluggable scoring & AI assist**
   - Each rule carries a *weight* and the engine can learn preference profiles, allowing stochastic “creativity” when multiple paths tie. Future hooks support LLM-based relevance ranking.

8. **Designed for historical linguistics & cryptosemiotics**
   - Out-of-the-box support for runic, hieroglyphic, cuneiform, and other paleo-scripts, making SLF suitable for decipherment experiments and hidden-layer lyric analyses.

9. **Extensible by data, not code**
   - New symbol sets, rule families, or entire transformation methods can be added simply by dropping another metadata file—no core modification required.

10. **Goal: surface latent narratives in language**
    - By revealing how letters, sounds, myths, and abbreviations intertwine, SLF aims to turn “flat” text into rich, multi-threaded storylines that can be mined for metaphor, cultural insight, or creative inspiration.

---

## Included in this package:

- `slf_core_v1.1.0.py` — fully annotated source code.
- `character_transforms.parquet` — main symbolic/logographic/phonetic rules.
- `acronym_transforms.parquet` — acronym expansions.
- `wordlist.txt` — starter symbolic wordlist.
- `large_wordlist.txt` — large basic dictionary (~50,000 words).
- `requirements.txt` — Python dependencies.
- `README.md` — this documentation.

## How to Run:

```bash
pip install -r requirements.txt
python3 slf_core_v1.1.0.py
```

If you do not specify `-m`, the script will auto-load both `.parquet` files and the wordlist if present in the same folder.

## Tree Log:

Transform chains are logged in `seed_tree.jsonl` so you can trace, replay, and analyze every hop.

## Expand it:

Just add new `.parquet` files (symbolic, phonetic, logographic, acronym, etc.) to grow the framework—no core changes needed.

## Enjoy building your own symbolic language maps! 🚀✨
