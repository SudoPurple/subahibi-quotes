#!/usr/bin/env python3
"""
SubaHibi (Wonderful Everyday) Quote Extractor
Extracts all dialogue lines, monologues, and philosophical quotes directly
from BGI/Ethornell BURIKO ARC20 archives and compiled scenario bytecode.
"""

import glob
import json
import os
import re
import struct
import sys

CHAPTER_MAP = {
    'data01000': 'Prologue',
    'data01101': 'Down the Rabbit-Hole I',
    'data01102': 'Down the Rabbit-Hole II',
    'data01201': "It's My Own Invention",
    'data01301': 'Looking-glass Insects',
    'data01401': 'Jabberwocky I',
    'data01501': 'Which Dreamed It',
    'data01601': 'Jabberwocky II',
    'data01701': 'Wonderful Everyday',
    'data01900': 'Extra Scenes',
    'data01999': 'Epilogue / System',
}

# POV Narrator for monologues when there is no spoken speaker
POV_MAP = {
    'Prologue': 'Minakami Yuki',
    'Down the Rabbit-Hole I': 'Minakami Yuki',
    'Down the Rabbit-Hole II': 'Minakami Yuki',
    "It's My Own Invention": 'Mamiya Takuji',
    'Looking-glass Insects': 'Takashimadaira Zakuro',
    'Jabberwocky I': 'Yuuki Tomosane',
    'Which Dreamed It': 'Mamiya Takuji',
    'Jabberwocky II': 'Yuuki Tomosane',
    'Wonderful Everyday': 'Minakami Yuki',
    'Extra Scenes': 'Minakami Yuki',
    'Epilogue / System': 'Minakami Yuki',
}

VOICE_MAP = {
    'yuki': 'Minakami Yuki',
    'taku': 'Mamiya Takuji',
    'zaku': 'Takashimadaira Zakuro',
    'has': 'Wakatsuki Hasaki',
    'kimi': 'Tachibana Kimika',
    'kag': 'Wakatsuki Kagami',
    'tsuk': 'Wakatsuki Tsukasa',
    'mizu': 'Mamiya Mizuna',
    'aya': 'Otonashi Ayana',
    'tom': 'Yuuki Tomosane',
    'riri': 'Riruru',
    'mura': 'Murata',
    'ota': 'Ota',
    'sen': 'Senuma',
}

SPEAKER_CLEANUP = {
    'Yuki': 'Minakami Yuki',
    'Takuji': 'Mamiya Takuji',
    'Zakuro': 'Takashimadaira Zakuro',
    'Hasaki': 'Wakatsuki Hasaki',
    'Kimika': 'Tachibana Kimika',
    'Kagami': 'Wakatsuki Kagami',
    'Tsukasa': 'Wakatsuki Tsukasa',
    'Ayana': 'Otonashi Ayana',
    'Tomosane': 'Yuuki Tomosane',
    'Mizuna': 'Mamiya Mizuna',
    'Takashima Zakuro': 'Takashimadaira Zakuro',
}

# List of known valid characters in the game
KNOWN_CHARACTERS = set([
    'Minakami Yuki', 'Mamiya Takuji', 'Takashimadaira Zakuro', 'Yuuki Tomosane',
    'Tachibana Kimika', 'Wakatsuki Hasaki', 'Wakatsuki Kagami', 'Wakatsuki Tsukasa',
    'Otonashi Ayana', 'Mamiya Mizuna', 'Riruru', 'Mamiya', 'Kimura', 'Megu',
    'Satoko', 'Master', 'Asumi', 'Shiroyama', 'Nishimura', 'Usami', 'Iida',
    'Numada', 'Yasuko', 'Miu', 'God', 'Kiyokawa', 'Senagawa', 'Teacher',
    'Hiroo', 'Kiyoshi', 'Ayumi', 'Doll', 'Iinuma', 'Kotomi', 'Edmond Rostand',
    'Ludwig Wittgenstein', 'Cyrano de Bergerac'
])


class DscDecoder:
    """Decompress DSC FORMAT 1.00 streams from BGI archives."""

    def __init__(self, data: bytes):
        self.data = data
        self.magic = struct.unpack('<H', data[0:2])[0] << 16
        self.key = struct.unpack('<I', data[16:20])[0]
        self.output_size = struct.unpack('<i', data[20:24])[0]
        self.dec_count = struct.unpack('<I', data[24:28])[0]
        self.output = bytearray(self.output_size)
        self.pos = 0x20
        self.m_bits = 0
        self.m_cached_bits = 0

    def update_key(self) -> int:
        v0 = 20021 * (self.key & 0xFFFF)
        v1 = self.magic | (self.key >> 16)
        v1 = v1 * 20021 + self.key * 346
        v1 = (v1 + (v0 >> 16)) & 0xFFFF
        self.key = ((v1 << 16) + (v0 & 0xFFFF) + 1) & 0xFFFFFFFF
        return v1 & 0xFF

    def get_bits(self, count: int) -> int:
        while self.m_cached_bits < count:
            if self.pos >= len(self.data):
                return -1
            b = self.data[self.pos]
            self.pos += 1
            self.m_bits = (self.m_bits << 8) | b
            self.m_cached_bits += 8
        mask = (1 << count) - 1
        self.m_cached_bits -= count
        return (self.m_bits >> self.m_cached_bits) & mask

    def get_next_bit(self) -> int:
        return self.get_bits(1)

    def unpack(self) -> bytes:
        hcodes = []
        for i in range(512):
            src = self.data[self.pos]
            self.pos += 1
            depth = (src - self.update_key()) & 0xFF
            if depth != 0:
                hcodes.append((depth, i))

        hcodes.sort()
        node_count = len(hcodes)
        hnodes = [[False, 0, 0, 0] for _ in range(1024)]
        nodes_index = [[0] * 512 for _ in range(2)]
        next_node_index = 1
        depth_nodes = 1
        depth = 0
        child_index = 0
        nodes_index[0][0] = 0

        n = 0
        while n < node_count:
            huffman_nodes_index = child_index
            child_index ^= 1
            depth_existed_nodes = 0
            while n < node_count and hcodes[n][0] == depth:
                node = [False, hcodes[n][1], 0, 0]
                hnodes[nodes_index[huffman_nodes_index][depth_existed_nodes]] = node
                depth_existed_nodes += 1
                n += 1

            depth_nodes_to_create = depth_nodes - depth_existed_nodes
            for i in range(depth_nodes_to_create):
                node = [True, 0, next_node_index, next_node_index + 1]
                next_node_index += 2
                nodes_index[child_index][i * 2] = node[2]
                nodes_index[child_index][i * 2 + 1] = node[3]
                hnodes[nodes_index[huffman_nodes_index][depth_existed_nodes + i]] = node

            depth += 1
            depth_nodes = depth_nodes_to_create * 2

        dst_ptr = 0
        for _ in range(self.dec_count):
            node_idx = 0
            while hnodes[node_idx][0]:
                bit = self.get_next_bit()
                if bit == -1:
                    break
                node_idx = hnodes[node_idx][3] if bit else hnodes[node_idx][2]

            code = hnodes[node_idx][1]
            if code >= 256:
                offset = self.get_bits(12)
                if offset == -1:
                    break
                count = (code & 0xFF) + 2
                offset += 2
                src_ptr = dst_ptr - offset
                for _ in range(count):
                    self.output[dst_ptr] = self.output[src_ptr]
                    dst_ptr += 1
                    src_ptr += 1
            else:
                self.output[dst_ptr] = code
                dst_ptr += 1

        return bytes(self.output)


def is_valid_speaker(name: str) -> bool:
    """Validate that a string is a genuine character name, not dialogue or asset ID."""
    if not name or len(name) > 30 or len(name) < 2:
        return False
    if name.startswith('"') or name.startswith("'") or name.startswith('“'):
        return False
    if name.endswith('.') or name.endswith('!') or name.endswith('?'):
        return False
    if '\n' in name or '<' in name or '>' in name:
        return False
    if re.match(r'^(map|sp|bg|bgm|se|sys|ev|ch|ef)\d+', name):
        return False
    return True


def parse_script_dialogues(bytecode: bytes, chapter: str, scene_name: str):
    """Parse dialogue and quotes from compiled Buriko script bytecode."""
    magic = b'BurikoCompiledScriptVer1.00\x00'
    if bytecode.startswith(magic):
        extra = struct.unpack('<I', bytecode[0x1C:0x20])[0]
        body = bytecode[0x1C + extra:]
    else:
        body = bytecode

    idx7f = body.find(b'\x7f\x00\x00\x00')
    if idx7f == -1 or idx7f > 128:
        return []
    first_text_offset = struct.unpack('<I', body[idx7f + 4 : idx7f + 8])[0]
    if first_text_offset >= len(body):
        return []

    string_cache = {}

    def get_string(offset):
        if offset in string_cache:
            return string_cache[offset]
        if not (first_text_offset <= offset < len(body)):
            return ''
        end = body.find(b'\x00', offset)
        if end == -1:
            return ''
        chunk = body[offset:end]
        try:
            val = chunk.decode('cp932')
        except UnicodeDecodeError:
            try:
                val = chunk.decode('utf-8')
            except UnicodeDecodeError:
                val = chunk.decode('latin1', errors='ignore')
        val = val.strip()
        string_cache[offset] = val
        return val

    raw_entries = []
    last_voice_speaker = ''

    for i in range(0, first_text_offset, 4):
        val = struct.unpack('<I', body[i : i + 4])[0]

        # Voice audio opcode 0x1a5
        if val == 0x1A5:
            if i >= 8:
                prev_op = struct.unpack('<I', body[i - 8 : i - 4])[0]
                if prev_op == 3:
                    v_off = struct.unpack('<I', body[i - 4 : i])[0]
                    v_str = get_string(v_off).lower()
                    for prefix, name in VOICE_MAP.items():
                        if v_str.startswith(prefix + '_'):
                            last_voice_speaker = name
                            break

        # Dialogue / Text rendering opcodes 0x140 - 0x145
        elif 0x140 <= val <= 0x145:
            args = []
            p = i - 8
            while p >= 0 and p >= i - 32:
                op = struct.unpack('<I', body[p : p + 4])[0]
                if op == 3:
                    s_off = struct.unpack('<I', body[p + 4 : p + 8])[0]
                    s = get_string(s_off)
                    if s:
                        args.insert(0, s)
                    p -= 8
                else:
                    p -= 4

            if not args:
                continue

            speaker = ''
            text = ''
            if len(args) == 2:
                speaker = args[0]
                text = args[1]
            elif len(args) == 1:
                speaker = ''
                text = args[0]
            else:
                speaker = args[0]
                text = ' '.join(args[1:])

            text = text.replace('\n', ' ').strip()
            if not text or len(text) < 2:
                continue

            if re.match(r'^(map|sp|bg|bgm|se|sys|ev|ch|ef|day[a-z]*)\d+', text):
                continue
            if re.match(r'^[a-z]+_\d+(_[a-z0-9]+)?$', text):
                continue

            # Check if speaker argument is a valid name
            if not is_valid_speaker(speaker):
                # If speaker looked like text (e.g. quote continuation), combine or discard speaker
                if speaker.startswith('"') or speaker.startswith('“'):
                    text = speaker + ' ' + text
                speaker = ''

            # Standardize speaker name
            if speaker in SPEAKER_CLEANUP:
                speaker = SPEAKER_CLEANUP[speaker]
            elif not speaker and last_voice_speaker and (text.startswith('"') or text.startswith('“')):
                speaker = last_voice_speaker

            last_voice_speaker = ''
            raw_entries.append((speaker, text))

    # Merge multi-line broken quotes
    quotes = []
    idx = 0
    pov_narrator = POV_MAP.get(chapter, 'Minakami Yuki')

    while idx < len(raw_entries):
        speaker, text = raw_entries[idx]
        idx += 1

        while (
            (text.startswith('"') or text.startswith('“'))
            and not (text.endswith('"') or text.endswith('”'))
            and idx < len(raw_entries)
        ):
            next_sp, next_txt = raw_entries[idx]
            if next_sp == speaker or not next_sp:
                text += ' ' + next_txt
                idx += 1
            else:
                break

        stripped = text.strip('"“” \t\r\n.,!?…-―')
        # Filter tiny fragments like "What?", "Ah.", "...", "Yeah"
        if len(stripped) < 4 or stripped.count('.') >= 3 and len(stripped) < 8:
            continue

        is_spoken = bool(speaker or text.startswith('"') or text.startswith('“'))

        # If it's a monologue/narration without an explicit speaker, attribute to chapter POV character
        assigned_speaker = speaker if speaker else pov_narrator

        quotes.append(
            {
                'chapter': chapter,
                'scene': scene_name,
                'speaker': assigned_speaker,
                'text': text,
                'is_dialogue': is_spoken,
            }
        )

    return quotes


def extract_from_arc(arc_path: str):
    """Extract and parse all script files inside a BURIKO ARC20 archive."""
    arc_base = os.path.splitext(os.path.basename(arc_path))[0]
    chapter = CHAPTER_MAP.get(arc_base, arc_base)

    quotes = []
    with open(arc_path, 'rb') as f:
        sig = f.read(12)
        if not sig.startswith(b'BURIKO ARC20'):
            return []
        count = struct.unpack('<I', f.read(4))[0]
        base_offset = 0x10 + 0x80 * count

        entries = []
        for i in range(count):
            f.seek(0x10 + i * 0x80)
            name_bytes = f.read(0x60)
            name = name_bytes.split(b'\x00')[0].decode('shift-jis', errors='replace')
            rel_offset, size = struct.unpack('<II', f.read(8))
            entries.append((name, base_offset + rel_offset, size))

        for name, off, size in entries:
            f.seek(off)
            data = f.read(size)
            if data.startswith(b'DSC FORMAT 1.00\x00'):
                try:
                    decomp = DscDecoder(data).unpack()
                except Exception:
                    continue
            else:
                decomp = data

            scene_quotes = parse_script_dialogues(decomp, chapter, name)
            quotes.extend(scene_quotes)

    return quotes


def run_full_extraction(game_dir: str, output_file: str):
    """Extract all quotes from the game directory and save to JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    arc_files = sorted(glob.glob(os.path.join(game_dir, 'data01*.arc')))
    loose_files = sorted(glob.glob(os.path.join(game_dir, '*_trans')))

    all_quotes = []
    seen = set()

    for af in arc_files:
        print(f'Processing {os.path.basename(af)}...')
        quotes = extract_from_arc(af)
        for q in quotes:
            key = (q['speaker'], q['text'])
            if key not in seen:
                seen.add(key)
                all_quotes.append(q)

    for lf in loose_files:
        print(f'Processing loose file {os.path.basename(lf)}...')
        try:
            with open(lf, 'rb') as f:
                d = f.read()
            quotes = parse_script_dialogues(d, 'Looking-glass Insects', os.path.basename(lf))
            for q in quotes:
                key = (q['speaker'], q['text'])
                if key not in seen:
                    seen.add(key)
                    all_quotes.append(q)
        except Exception as e:
            print(f'Error reading {lf}: {e}')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_quotes, f, ensure_ascii=False, indent=2)

    print(f'Extracted {len(all_quotes)} unique quotes to {output_file}!')
    return len(all_quotes)


if __name__ == '__main__':
    default_game_dir = '/home/PurpleX/Documents/Wonderful.Everyday.DTRH.Uncensored/Wonderful.Everyday.DTRH.Uncensored'
    default_out = os.path.expanduser('~/.local/share/subahibi-quotes/quotes.json')
    g_dir = sys.argv[1] if len(sys.argv) > 1 else default_game_dir
    o_file = sys.argv[2] if len(sys.argv) > 2 else default_out
    run_full_extraction(g_dir, o_file)
