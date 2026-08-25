"""Is a keyword-getter pointer a vtable slot? If so, whose vtable?"""
import struct, re, sys
sys.path.insert(0, r"T:\eu5-engine-atlas\tools")
from pe import PE

pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
d = pe.data
PTR_OFF = 0x05D42A50            # .rdata slot holding the refresh_map_colors getter

def is_code_ptr(v):
    if not (pe.image_base <= v < pe.image_base + 0x9000000):
        return False
    o = pe.va_to_off(v)
    return o is not None and pe.section_of_off(o) == ".text"

def looks_like_col(va):
    """A COL: sig==1 and pTypeDescriptor resolves to a '.?AV' name."""
    o = pe.va_to_off(va)
    if o is None or pe.section_of_off(o) != ".rdata":
        return None
    sig, _off, _cd, ptd = struct.unpack_from("<IIII", d, o)
    if sig != 1:
        return None
    tdo = pe.rva_to_off(ptd)
    if tdo is None:
        return None
    name = d[tdo + 16: tdo + 160].split(b"\0")[0]
    if name.startswith(b".?AV"):
        return name.decode(errors="replace")
    return None

# walk backwards to the start of the contiguous code-pointer run
start = PTR_OFF
while start - 8 >= 0 and is_code_ptr(struct.unpack_from("<Q", d, start - 8)[0]):
    start -= 8
print(f"contiguous code-pointer run starts at 0x{start:08X}")
print(f"our slot index within that run: {(PTR_OFF - start)//8}")

prev = struct.unpack_from("<Q", d, start - 8)[0]
print(f"\nQWORD immediately before the run: 0x{prev:016X}")
owner = looks_like_col(prev)
print("resolves to RTTI class:", owner if owner else "(not a COL)")
