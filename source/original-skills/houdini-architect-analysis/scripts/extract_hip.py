"""Extract a Houdini .hip file (ASCII cpio old format, magic 070707).

Usage:
    python extract_hip.py <path/to/file.hip> [output_dir]

If output_dir is omitted, defaults to <hip_file>_extracted next to the input.
"""
import os
import sys
from pathlib import Path


def extract_cpio_odc(src_path, dst_dir):
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    with open(src_path, "rb") as f:
        data = f.read()

    pos = 0
    files = []
    while pos < len(data):
        magic = data[pos:pos+6]
        if magic != b"070707":
            print(f"Bad magic at {pos}: {magic!r}")
            break

        # 6+6+6+6+6+6+6+6+11+6+11 = 76 byte header (POSIX cpio "odc" format)
        try:
            dev      = int(data[pos+6:pos+12], 8)
            ino      = int(data[pos+12:pos+18], 8)
            mode     = int(data[pos+18:pos+24], 8)
            uid      = int(data[pos+24:pos+30], 8)
            gid      = int(data[pos+30:pos+36], 8)
            nlink    = int(data[pos+36:pos+42], 8)
            rdev     = int(data[pos+42:pos+48], 8)
            mtime    = int(data[pos+48:pos+59], 8)
            namesize = int(data[pos+59:pos+65], 8)
            filesize = int(data[pos+65:pos+76], 8)
        except ValueError as e:
            print(f"Header parse error at {pos}: {e}")
            break

        name_start = pos + 76
        name_end   = name_start + namesize
        name = data[name_start:name_end].rstrip(b"\x00").decode("utf-8", errors="replace")

        file_start = name_end
        file_end   = file_start + filesize
        content    = data[file_start:file_end]

        if name == "TRAILER!!!":
            break

        out_path = dst_dir / name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if mode & 0o040000:  # directory
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path.write_bytes(content)
            files.append((name, filesize))

        pos = file_end

    return files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    if len(sys.argv) > 2:
        dst = sys.argv[2]
    else:
        # default: <hip_file>_extracted next to the input
        src_path = Path(src)
        dst = str(src_path.with_name(src_path.stem + "_extracted"))
    files = extract_cpio_odc(src, dst)
    print(f"\nExtracted {len(files)} entries to: {dst}\n")
    for name, size in files[:50]:
        print(f"  {size:>10}  {name}")
    if len(files) > 50:
        print(f"  ... and {len(files)-50} more entries")
