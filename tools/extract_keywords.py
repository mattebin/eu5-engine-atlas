import struct, re
from pe import PE
pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
ANCHOR = 0x05D42A50

def is_text_ptr(v):
    if not (pe.image_base <= v < pe.image_base + 0x9000000):
        return False
    o = pe.va_to_off(v)
    return o is not None and pe.section_of_off(o) == ".text"

# find table bounds
start = ANCHOR
while start - 8 >= 0 and is_text_ptr(struct.unpack_from("<Q", d, start - 8)[0]):
    start -= 8
end = ANCHOR
while end + 8 < len(d) and is_text_ptr(struct.unpack_from("<Q", d, end + 8)[0]):
    end += 8
n = (end - start) // 8 + 1
print(f"table: file 0x{start:08X}..0x{end:08X}  entries={n}\n")

def keyword_of(fn_va):
    """Extract the string a getter function references via RIP-relative LEA."""
    o = pe.va_to_off(fn_va)
    if o is None:
        return None
    win = d[o:o + 96]
    for m in re.finditer(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", win):
        ins = o + m.start()
        disp = struct.unpack_from("<i", d, ins + 3)[0]
        nxt = pe.off_to_rva(ins + 7)
        if nxt is None:
            continue
        so = pe.va_to_off(pe.image_base + nxt + disp)
        if so is None:
            continue
        s = d[so:so + 96].split(b"\0")[0]
        if re.fullmatch(rb"[a-z][a-z0-9_]{2,63}", s):
            return s.decode()
    return None

words = []
for i in range(n):
    v = struct.unpack_from("<Q", d, start + i * 8)[0]
    words.append((i, keyword_of(v)))
ok = [w for _, w in words if w]
print(f"extracted {len(ok)} keywords from {n} entries\n")
idx = next(i for i, w in words if w == "refresh_map_colors")
for i in range(max(0, idx - 6), min(n, idx + 7)):
    w = words[i][1]
    print(f"  [{i:4}] {w}{'   <<< anchor' if w == 'refresh_map_colors' else ''}")
open("keywords_raw.txt", "w", encoding="utf-8").write("\n".join(w or "" for _, w in words))
print("\nfull list written to keywords_raw.txt")
