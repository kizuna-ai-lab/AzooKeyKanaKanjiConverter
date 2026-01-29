#!/usr/bin/env python3
"""
Generate Pinyin Dictionary for XiaoLiIME Hybrid Input Mode

This script creates a pinyin-to-kanji dictionary by:
1. Extracting kanji words from the existing Japanese dictionary (.loudstxt3 files)
2. Looking up Chinese pinyin using phrase-pinyin-data (words and characters)
3. Generating pinyin entries with correct multi-character word pronunciations

Data source: https://github.com/mozillazg/phrase-pinyin-data
- Provides word-level pinyin (handles multi-pronunciation characters correctly)
- Falls back to single-character pinyin for words not in the phrase dictionary

Usage:
    python generate_pinyin_dict.py [--output OUTPUT_DIR]
"""

import argparse
import re
import struct
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Optional


# Hiragana to romaji mapping
HIRAGANA_TO_ROMAJI = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    # Voiced (dakuten)
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    # Small kana
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo',
    'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
    'っ': 'tt',  # Double consonant marker
}


def download_phrase_pinyin_data(output_dir: Path) -> tuple[Path, Path]:
    """
    Download pinyin data files from GitHub.

    Returns (phrase_file, char_file) paths.

    Data sources:
    - phrase-pinyin-data: word/phrase level pinyin (handles multi-pronunciation correctly)
    - pinyin-data: single character pinyin (fallback for characters not in phrase dict)
    """
    # Word/phrase pinyin (large_pinyin.txt ~9MB, contains phrases from multiple sources)
    phrase_file = output_dir / "large_pinyin.txt"
    phrase_url = "https://raw.githubusercontent.com/mozillazg/phrase-pinyin-data/master/large_pinyin.txt"

    # Single character pinyin from pinyin-data repository
    # pinyin.txt contains character -> pinyin mappings with most common pronunciation
    char_file = output_dir / "char_pinyin.txt"
    char_url = "https://raw.githubusercontent.com/mozillazg/pinyin-data/master/pinyin.txt"

    downloads = [
        ("large_pinyin.txt", phrase_file, phrase_url),
        ("char_pinyin.txt", char_file, char_url),
    ]

    for filename, filepath, url in downloads:
        if filepath.exists():
            print(f"{filename} already exists at {filepath}")
            continue

        print(f"Downloading {filename} from {url}...")

        try:
            result = subprocess.run(
                ['curl', '-L', '-A', 'Mozilla/5.0', '-o', str(filepath), url],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(f"curl failed: {result.stderr}")
            print(f"Downloaded {filename}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            print(f"Please manually download from {url}")
            sys.exit(1)

    return phrase_file, char_file


def remove_tone_marks(pinyin: str) -> str:
    """Remove pinyin tone marks and convert to base letters."""
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ü': 'v',
        'ń': 'n', 'ň': 'n', 'ǹ': 'n',
        'ḿ': 'm',
    }
    result = pinyin.lower()
    for tone, base in tone_map.items():
        result = result.replace(tone, base)
    # Also remove numeric tone markers (1-5)
    result = re.sub(r'[1-5]', '', result)
    return result


def load_phrase_pinyin(phrase_file: Path) -> dict[str, str]:
    """
    Load word/phrase to pinyin mapping from phrase-pinyin-data.

    Format: 词语: pīn yīn
    Returns dict mapping word -> pinyin (without tones, spaces removed)
    """
    phrase_to_pinyin = {}

    print(f"Loading phrase pinyin from {phrase_file}...")

    with open(phrase_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ': ' not in line:
                continue

            # Format: "词语: pīn yīn"
            parts = line.split(': ', 1)
            if len(parts) != 2:
                continue

            phrase, pinyin_with_tones = parts
            # Remove tone marks and spaces
            pinyin_clean = remove_tone_marks(pinyin_with_tones.replace(' ', ''))
            phrase_to_pinyin[phrase] = pinyin_clean

    print(f"Loaded {len(phrase_to_pinyin)} phrase-to-pinyin mappings")
    return phrase_to_pinyin


def load_char_pinyin(char_file: Path) -> dict[str, str]:
    """
    Load single character to pinyin mapping from mozillazg/pinyin-data.

    This file contains the most commonly used pronunciation for each character,
    which is better than Unihan's arbitrary first pronunciation.

    Format: U+XXXX: pīn1,pīn2,...  # 字
    Returns dict mapping char -> pinyin (without tones)
    """
    char_to_pinyin = {}

    print(f"Loading character pinyin from {char_file}...")

    with open(char_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Format: U+XXXX: pīn1,pīn2,...  # 字
            if not line.startswith('U+'):
                continue

            # Split by colon to get codepoint and pinyin part
            if ': ' not in line:
                continue

            codepoint_part, rest = line.split(': ', 1)

            # Remove comment if present
            if '#' in rest:
                pinyin_part = rest.split('#')[0].strip()
            else:
                pinyin_part = rest.strip()

            # Convert codepoint to character
            try:
                codepoint = int(codepoint_part[2:], 16)
                char = chr(codepoint)
            except (ValueError, OverflowError):
                continue

            # Take first pronunciation if multiple (comma-separated)
            first_pinyin = pinyin_part.split(',')[0].strip()
            pinyin_clean = remove_tone_marks(first_pinyin)

            if pinyin_clean:
                char_to_pinyin[char] = pinyin_clean

    print(f"Loaded {len(char_to_pinyin)} character-to-pinyin mappings")
    return char_to_pinyin


def is_kanji(char: str) -> bool:
    """Check if a character is a CJK ideograph (kanji)."""
    try:
        name = unicodedata.name(char, '')
        return 'CJK' in name or 'IDEOGRAPH' in name
    except:
        # Fallback: check Unicode ranges for CJK
        cp = ord(char)
        return (
            (0x4E00 <= cp <= 0x9FFF) or   # CJK Unified Ideographs
            (0x3400 <= cp <= 0x4DBF) or   # CJK Extension A
            (0x20000 <= cp <= 0x2A6DF) or # CJK Extension B
            (0x2A700 <= cp <= 0x2B73F) or # CJK Extension C
            (0x2B740 <= cp <= 0x2B81F) or # CJK Extension D
            (0xF900 <= cp <= 0xFAFF) or   # CJK Compatibility Ideographs
            (0x2F800 <= cp <= 0x2FA1F)    # CJK Compatibility Supplement
        )


def is_hiragana(char: str) -> bool:
    """Check if character is hiragana."""
    return 0x3040 <= ord(char) <= 0x309F


def parse_loudstxt3(filepath: Path) -> list[tuple[str, str, int, int, int, float]]:
    """
    Parse a .loudstxt3 file and extract dictionary entries.

    Returns list of (ruby, word, lcid, rcid, mid, score) tuples.
    """
    entries = []

    try:
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 2:
            return entries

        # Header: UInt16 count
        count = struct.unpack('<H', data[0:2])[0]

        if count == 0:
            return entries

        # Offsets: count * UInt32
        header_size = 2 + count * 4
        if len(data) < header_size:
            return entries

        offsets = []
        for i in range(count):
            offset = struct.unpack('<I', data[2 + i*4 : 2 + i*4 + 4])[0]
            offsets.append(offset)

        # Parse each entry
        for i in range(count):
            start = offsets[i]
            end = offsets[i+1] if i+1 < count else len(data)

            if start >= len(data) or end > len(data) or start >= end:
                continue

            entry_data = data[start:end]
            if len(entry_data) < 2:
                continue

            # Entry format: UInt16 row_count, then rows, then text
            row_count = struct.unpack('<H', entry_data[0:2])[0]

            if row_count == 0:
                continue

            # Each row: lcid(2) + rcid(2) + mid(2) + score(4) = 10 bytes
            rows_size = row_count * 10
            if len(entry_data) < 2 + rows_size:
                continue

            rows = []
            for j in range(row_count):
                row_start = 2 + j * 10
                lcid = struct.unpack('<H', entry_data[row_start:row_start+2])[0]
                rcid = struct.unpack('<H', entry_data[row_start+2:row_start+4])[0]
                mid = struct.unpack('<H', entry_data[row_start+4:row_start+6])[0]
                score = struct.unpack('<f', entry_data[row_start+6:row_start+10])[0]
                rows.append((lcid, rcid, mid, score))

            # Text area: ruby\tword1\tword2\t...
            text_start = 2 + rows_size
            text_data = entry_data[text_start:]

            try:
                text = text_data.decode('utf-8')
                parts = text.split('\t')
                if len(parts) >= 1:
                    ruby = parts[0]
                    words = parts[1:] if len(parts) > 1 else [ruby]

                    for idx, word in enumerate(words):
                        if idx < len(rows):
                            lcid, rcid, mid, score = rows[idx]
                            # Empty word means same as ruby
                            actual_word = word if word else ruby
                            entries.append((ruby, actual_word, lcid, rcid, mid, score))
            except:
                pass

    except Exception as e:
        pass

    return entries


def extract_japanese_dictionary(dict_dir: Path) -> list[tuple[str, str, int, int, int, float]]:
    """
    Extract all entries from the Japanese dictionary .loudstxt3 files.

    Returns list of (ruby, word, lcid, rcid, mid, score) tuples.
    """
    entries = []

    loudstxt3_files = list(dict_dir.glob("*.loudstxt3"))
    # Exclude pinyin files
    loudstxt3_files = [f for f in loudstxt3_files if not f.name.startswith("pinyin")]

    print(f"Found {len(loudstxt3_files)} Japanese dictionary files")

    for i, filepath in enumerate(loudstxt3_files):
        if i % 50 == 0:
            print(f"  Processing file {i+1}/{len(loudstxt3_files)}...")

        file_entries = parse_loudstxt3(filepath)
        entries.extend(file_entries)

    print(f"Extracted {len(entries)} entries from Japanese dictionary")
    return entries


def generate_pinyin_for_word(
    word: str,
    phrase_to_pinyin: dict[str, str],
    char_to_pinyin: dict[str, str]
) -> Optional[str]:
    """
    Generate pinyin for a word containing kanji and/or hiragana.

    Priority:
    1. Direct phrase lookup (handles multi-pronunciation characters correctly)
    2. Character-by-character lookup as fallback

    - Kanji: converted to pinyin
    - Hiragana: converted to romaji
    - Other characters: skip word

    Returns None if word cannot be converted.
    """
    # Must contain at least one kanji to be useful
    if not any(is_kanji(c) for c in word):
        return None

    # Priority 1: Direct phrase lookup
    # This handles multi-pronunciation characters correctly (e.g., 地 -> di in 築地)
    if word in phrase_to_pinyin:
        return phrase_to_pinyin[word]

    # Priority 2: Character-by-character lookup
    pinyin_parts = []

    for char in word:
        if char in char_to_pinyin:
            # Kanji with pinyin mapping
            pinyin_parts.append(char_to_pinyin[char])
        elif is_hiragana(char) and char in HIRAGANA_TO_ROMAJI:
            # Hiragana converted to romaji
            pinyin_parts.append(HIRAGANA_TO_ROMAJI[char])
        elif is_kanji(char):
            # Kanji without pinyin mapping - skip entire word
            return None
        else:
            # Other characters (katakana, punctuation) - skip entire word
            return None

    if not pinyin_parts:
        return None

    return ''.join(pinyin_parts)


def generate_pinyin_entries(
    japanese_entries: list[tuple[str, str, int, int, int, float]],
    phrase_to_pinyin: dict[str, str],
    char_to_pinyin: dict[str, str]
) -> list[tuple[str, str, int, int, int, float]]:
    """
    Generate pinyin dictionary entries from Japanese dictionary entries.

    For each Japanese entry with kanji word:
    1. Look up pinyin (phrase-level first, then character-by-character)
    2. Create new entry with pinyin as key, kanji as value
    3. Keep the entry with the best (highest) score for each (pinyin, word) pair
    """
    # Track best entry for each (pinyin, word) pair
    best_entries: dict[tuple[str, str], tuple[str, str, int, int, int, float]] = {}

    print("Generating pinyin entries from Japanese dictionary...")
    phrase_hits = 0
    char_hits = 0

    # Process Japanese dictionary entries
    for ruby, word, lcid, rcid, mid, score in japanese_entries:
        # Only process words that contain kanji
        if not any(is_kanji(c) for c in word):
            continue

        # Check if word exists in phrase dictionary (for stats)
        is_phrase_hit = word in phrase_to_pinyin

        # Generate pinyin for the word
        pinyin = generate_pinyin_for_word(word, phrase_to_pinyin, char_to_pinyin)

        if pinyin and pinyin.isascii() and pinyin.islower():
            key = (pinyin, word)
            # Adjust score (cap at -5.0)
            adjusted_score = min(score, -5.0)

            # Keep entry with best (highest/least negative) score
            if key not in best_entries or adjusted_score > best_entries[key][5]:
                best_entries[key] = (pinyin, word, lcid, rcid, mid, adjusted_score)

            # Track stats
            if is_phrase_hit:
                phrase_hits += 1
            else:
                char_hits += 1

    pinyin_entries = list(best_entries.values())
    print(f"Generated {len(pinyin_entries)} pinyin entries from Japanese dictionary")
    print(f"  - Phrase-level pinyin: {phrase_hits} hits")
    print(f"  - Character-level pinyin: {char_hits} hits")
    print(f"Total pinyin entries: {len(pinyin_entries)}")

    return pinyin_entries


def write_tsv(entries: list[tuple], output_file: Path):
    """Write entries to TSV format."""
    print(f"Writing {len(entries)} entries to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# pinyin\tword\tlcid\trcid\tmid\tvalue\n")
        for pinyin, word, lcid, rcid, mid, value in sorted(entries, key=lambda x: (x[0], x[1])):
            f.write(f"{pinyin}\t{word}\t{lcid}\t{rcid}\t{mid}\t{value}\n")

    print(f"Written TSV to {output_file}")


def build_louds_dictionary(
    tsv_file: Path,
    output_dir: Path,
    char_id_file: Path
):
    """Build LOUDS dictionary files from TSV."""

    print(f"Building LOUDS dictionary...")
    print(f"  TSV file: {tsv_file}")
    print(f"  Output dir: {output_dir}")
    print(f"  CharID file: {char_id_file}")

    output_dir.mkdir(parents=True, exist_ok=True)

    swift_script = f'''
import Foundation

// Load charID mapping
let charIDPath = "{char_id_file}"
let charIDString = try! String(contentsOfFile: charIDPath, encoding: .utf8)
var char2UInt8: [Character: UInt8] = [:]
for (index, char) in charIDString.enumerated() {{
    char2UInt8[char] = UInt8(index)
}}

// Ensure lowercase letters are mapped
let letters = "abcdefghijklmnopqrstuvwxyz"
for (i, c) in letters.enumerated() {{
    if char2UInt8[c] == nil {{
        char2UInt8[c] = UInt8(164 + i)
    }}
}}

// Parse TSV file
struct Entry {{
    var pinyin: String
    var word: String
    var lcid: Int
    var rcid: Int
    var mid: Int
    var value: Float
}}

var entries: [Entry] = []
let tsvPath = "{tsv_file}"
let tsvContent = try! String(contentsOfFile: tsvPath, encoding: .utf8)
for line in tsvContent.split(separator: "\\n") {{
    if line.hasPrefix("#") {{ continue }}
    let parts = line.split(separator: "\\t", omittingEmptySubsequences: false)
    if parts.count >= 6 {{
        let entry = Entry(
            pinyin: String(parts[0]),
            word: String(parts[1]),
            lcid: Int(parts[2])!,
            rcid: Int(parts[3])!,
            mid: Int(parts[4])!,
            value: Float(parts[5])!
        )
        entries.append(entry)
    }}
}}

print("Loaded \\(entries.count) entries from TSV")

// Build trie structure
class TrieNode {{
    var children: [UInt8: TrieNode] = [:]
    var entries: [Entry] = []
}}

let root = TrieNode()

for entry in entries {{
    var node = root
    for char in entry.pinyin {{
        guard let id = char2UInt8[char] else {{
            continue
        }}
        if node.children[id] == nil {{
            node.children[id] = TrieNode()
        }}
        node = node.children[id]!
    }}
    node.entries.append(entry)
}}

// BFS to build LOUDS structure
var bits: [Bool] = [true, false]
var nodeChars: [UInt8] = [0, 0]

struct QueueItem {{
    var node: TrieNode
    var char: UInt8
}}

var queue: [QueueItem] = root.children.sorted {{ $0.key < $1.key }}.map {{ QueueItem(node: $0.value, char: $0.key) }}
bits.append(contentsOf: [Bool](repeating: true, count: queue.count))
bits.append(false)

var nodeIndex = 2
var nodeToIndex: [ObjectIdentifier: Int] = [:]
var indexToEntries: [Int: [Entry]] = [:]

while !queue.isEmpty {{
    var nextQueue: [QueueItem] = []
    for item in queue {{
        nodeToIndex[ObjectIdentifier(item.node)] = nodeIndex
        nodeChars.append(item.char)
        if !item.node.entries.isEmpty {{
            indexToEntries[nodeIndex] = item.node.entries
        }}

        let children = item.node.children.sorted {{ $0.key < $1.key }}
        bits.append(contentsOf: [Bool](repeating: true, count: children.count))
        bits.append(false)

        for (childChar, childNode) in children {{
            nextQueue.append(QueueItem(node: childNode, char: childChar))
        }}
        nodeIndex += 1
    }}
    queue = nextQueue
}}

print("Built LOUDS trie with \\(nodeIndex) nodes")

// Write LOUDS file
func makeLOUDSData(bits: [Bool]) -> Data {{
    let unit = 64
    let paddedCount = ((bits.count + unit - 1) / unit) * unit
    var data = Data()
    var value: UInt64 = 0
    var idxInUnit = 0
    for b in bits {{
        if b {{
            value |= (1 << (unit - idxInUnit - 1))
        }}
        idxInUnit += 1
        if idxInUnit == unit {{
            var v = value
            data.append(Data(bytes: &v, count: 8))
            value = 0
            idxInUnit = 0
        }}
    }}
    if idxInUnit != 0 {{
        while idxInUnit < unit {{
            value |= (1 << (unit - idxInUnit - 1))
            idxInUnit += 1
        }}
        var v = value
        data.append(Data(bytes: &v, count: 8))
    }}
    return data
}}

let outputDir = "{output_dir}"
let loudsData = makeLOUDSData(bits: bits)
try! loudsData.write(to: URL(fileURLWithPath: outputDir + "/pinyin.louds"))
print("Written pinyin.louds")

let charsData = Data(nodeChars)
try! charsData.write(to: URL(fileURLWithPath: outputDir + "/pinyin.loudschars2"))
print("Written pinyin.loudschars2")

// Write loudstxt3 files (sharded)
let shardShift = 11
let entriesPerShard = 1 << shardShift
let localMask = entriesPerShard - 1

var shards: [Int: [(local: Int, ruby: String, rows: [(word: String, lcid: Int, rcid: Int, mid: Int, score: Float)])]] = [:]

for (nodeIdx, nodeEntries) in indexToEntries {{
    let shard = nodeIdx >> shardShift
    let local = nodeIdx & localMask
    let ruby = nodeEntries.first!.pinyin
    let rows = nodeEntries.map {{ ($0.word, $0.lcid, $0.rcid, $0.mid, $0.value) }}
    shards[shard, default: []].append((local: local, ruby: ruby, rows: rows))
}}

for (shard, items) in shards.sorted(by: {{ $0.key < $1.key }}) {{
    var payloads: [Data] = Array(repeating: {{
        var z: UInt16 = 0
        return Data(bytes: &z, count: 2)
    }}(), count: entriesPerShard)

    for item in items {{
        var d = Data()
        var count = UInt16(item.rows.count)
        d.append(Data(bytes: &count, count: 2))
        for row in item.rows {{
            var lcid = UInt16(row.lcid)
            var rcid = UInt16(row.rcid)
            var mid = UInt16(row.mid)
            var score = Float32(row.score)
            d.append(Data(bytes: &lcid, count: 2))
            d.append(Data(bytes: &rcid, count: 2))
            d.append(Data(bytes: &mid, count: 2))
            d.append(Data(bytes: &score, count: 4))
        }}
        let text = ([item.ruby] + item.rows.map {{ $0.word == item.ruby ? "" : $0.word }}).joined(separator: "\\t")
        d.append(text.data(using: .utf8)!)
        payloads[item.local] = d
    }}

    var result = Data()
    var count16 = UInt16(entriesPerShard)
    result.append(Data(bytes: &count16, count: 2))

    var offset: UInt32 = 2 + UInt32(entriesPerShard) * 4
    for i in 0..<entriesPerShard {{
        result.append(Data(bytes: &offset, count: 4))
        offset += UInt32(payloads[i].count)
    }}

    for p in payloads {{
        result.append(p)
    }}

    try! result.write(to: URL(fileURLWithPath: outputDir + "/pinyin\\(shard).loudstxt3"))
}}

print("Written \\(shards.count) loudstxt3 shard files")
print("Dictionary build complete!")
'''

    script_file = output_dir / "build_pinyin_dict.swift"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(swift_script)

    print(f"Running Swift script to build dictionary...")
    result = subprocess.run(
        ['swift', str(script_file)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error building dictionary:")
        print(result.stderr)
        sys.exit(1)

    print(result.stdout)
    script_file.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Pinyin Dictionary from Japanese Dictionary"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "Sources" / "KanaKanjiConverterModuleWithDefaultDictionary" / "PinyinDictionary" / "louds",
        help="Output directory for pinyin dictionary files"
    )
    parser.add_argument(
        "--dict-dir", "-d",
        type=Path,
        default=Path(__file__).parent.parent / "Sources" / "KanaKanjiConverterModuleWithDefaultDictionary" / "azooKey_dictionary_storage" / "Dictionary" / "louds",
        help="Source directory containing Japanese dictionary files (.loudstxt3)"
    )
    parser.add_argument(
        "--tsv-only",
        action="store_true",
        help="Only generate TSV file, skip LOUDS building"
    )

    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Step 1: Download phrase-pinyin-data (replaces Unihan for better multi-pronunciation handling)
    phrase_file, char_file = download_phrase_pinyin_data(args.output.parent)

    # Step 2: Load pinyin data
    phrase_to_pinyin = load_phrase_pinyin(phrase_file)
    char_to_pinyin = load_char_pinyin(char_file)

    # Step 3: Extract entries from Japanese dictionary
    japanese_entries = extract_japanese_dictionary(args.dict_dir)

    # Step 4: Generate pinyin entries
    pinyin_entries = generate_pinyin_entries(japanese_entries, phrase_to_pinyin, char_to_pinyin)

    # Step 5: Write TSV
    tsv_file = args.output / "pinyin_dictionary.tsv"
    write_tsv(pinyin_entries, tsv_file)

    # Step 6: Build LOUDS dictionary
    if not args.tsv_only:
        char_id_file = args.dict_dir / "charID.chid"
        build_louds_dictionary(tsv_file, args.output, char_id_file=char_id_file)

    print("\nDone! Dictionary files created:")
    print(f"  - {args.output}/pinyin.louds")
    print(f"  - {args.output}/pinyin.loudschars2")
    print(f"  - {args.output}/pinyin*.loudstxt3")


if __name__ == "__main__":
    main()
