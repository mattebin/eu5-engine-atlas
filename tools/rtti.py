"""Map MSVC RTTI class name -> vtable VA, for a PE32+ image."""
import struct, re
from pe import PE

class RTTI:
    def __init__(self, pe: PE):
        self.pe = pe
        d = pe.data
        # 1. type descriptors: ".?AV<Name>@@" preceded by 2 pointers
        self.td_by_name = {}
        for m in re.finditer(rb"\.\?AV([A-Za-z_][A-Za-z0-9_@?$<>,\-]{2,120})@@\x00", d):
            name = m.group(1).decode(errors="replace")
            td_off = m.start() - 16          # TypeDescriptor starts 16 bytes earlier
            if td_off < 0:
                continue
            rva = pe.off_to_rva(td_off)
            if rva is not None:
                self.td_by_name.setdefault(name, rva)
        # 2. index COL structures by the type-descriptor RVA they point at
        #    x64 COL: sig, offset, cdOffset, pTypeDescriptor, pClassDescriptor, pSelf
        self.col_by_td = {}
        rd = next(s for s in pe.sections if s["name"] == ".rdata")
        lo, hi = rd["rawptr"], rd["rawptr"] + rd["rawsize"]
        for off in range(lo, hi - 24, 4):
            sig, _o, _cd, ptd = struct.unpack_from("<IIII", d, off)
            if sig != 1:
                continue
            self.col_by_td.setdefault(ptd, []).append(off)
        # 3. vtables: a QWORD holding the COL's VA, vtable starts right after
        self.vt_by_col_off = {}
        for m in re.finditer(rb"(?=.)", b""):   # placeholder, filled lazily
            pass

    def vtable_for(self, name):
        """Return list of vtable VAs for a class name."""
        pe, d = self.pe, self.pe.data
        td_rva = self.td_by_name.get(name)
        if td_rva is None:
            return []
        out = []
        for col_off in self.col_by_td.get(td_rva, []):
            col_va = pe.image_base + pe.off_to_rva(col_off)
            needle = struct.pack("<Q", col_va)
            for m in re.finditer(re.escape(needle), d):
                vt_off = m.start() + 8            # vtable[0] sits after the COL ptr
                rva = pe.off_to_rva(vt_off)
                if rva is not None:
                    out.append(pe.image_base + rva)
        return out

if __name__ == "__main__":
    pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
    r = RTTI(pe)
    print("type descriptors indexed:", len(r.td_by_name))
    print("COL structures indexed  :", sum(len(v) for v in r.col_by_td.values()))
    for cls in ("CRefreshMapColorsEffect", "CGarrisonSortieEffect"):
        vts = r.vtable_for(cls)
        print(f"{cls}: {len(vts)} vtable(s) {[hex(v) for v in vts[:3]]}")
