"""Minimal PE reader: sections, image base, RVA<->file-offset mapping."""
import struct, pathlib

class PE:
    def __init__(self, path):
        self.data = pathlib.Path(path).read_bytes()
        d = self.data
        pe_off = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[pe_off:pe_off+4] == b"PE\0\0", "not a PE"
        coff = pe_off + 4
        self.machine, self.nsec = struct.unpack_from("<HH", d, coff)
        opt_size = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from("<H", d, opt)[0]
        self.pe32plus = magic == 0x20B
        self.image_base = struct.unpack_from("<Q" if self.pe32plus else "<I",
                                             d, opt + (24 if self.pe32plus else 28))[0]
        sec = opt + opt_size
        self.sections = []
        for i in range(self.nsec):
            o = sec + i * 40
            name = d[o:o+8].rstrip(b"\0").decode(errors="replace")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
            chars = struct.unpack_from("<I", d, o + 36)[0]
            self.sections.append(dict(name=name, vaddr=vaddr, vsize=vsize,
                                      rawptr=rawptr, rawsize=rawsize, chars=chars))

    def off_to_rva(self, off):
        for s in self.sections:
            if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
                return s["vaddr"] + (off - s["rawptr"])
        return None

    def rva_to_off(self, rva):
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"]):
                o = s["rawptr"] + (rva - s["vaddr"])
                return o if o < len(self.data) else None
        return None

    def va_to_off(self, va):
        return self.rva_to_off(va - self.image_base)

    def section_of_off(self, off):
        for s in self.sections:
            if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
                return s["name"]
        return None

if __name__ == "__main__":
    pe = PE(r"C:\SteamLibrary\steamapps\common\Europa Universalis V\binaries\eu5.exe")
    print(f"PE32+: {pe.pe32plus}  image_base: 0x{pe.image_base:X}  sections: {pe.nsec}")
    for s in pe.sections:
        print(f"  {s['name']:8} vaddr=0x{s['vaddr']:08X} vsize=0x{s['vsize']:08X} "
              f"raw=0x{s['rawptr']:08X} rawsize=0x{s['rawsize']:08X}")
    off = pe.data.find(b"refresh_map_colors")
    print(f"\nanchor off=0x{off:X} section={pe.section_of_off(off)} "
          f"rva=0x{pe.off_to_rva(off):X} va=0x{pe.image_base + pe.off_to_rva(off):X}")
