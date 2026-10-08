import socket, json, sys

def blender_exec(code, strict=True, timeout=30):
    s = socket.create_connection(("127.0.0.1", 9876), timeout=10)
    try:
        req = json.dumps({"type": "execute", "code": code, "strict_json": strict})
        s.sendall(req.encode("utf-8") + b"\x00")
        s.settimeout(timeout)
        buf = bytearray()
        while b"\x00" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)
        raw = bytes(buf[: buf.index(b"\x00")])
        return json.loads(raw)
    finally:
        s.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="file .py berisi kode untuk dieksekusi di Blender (default: stdin)")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            code = f.read()
    else:
        code = sys.stdin.read()
    print(json.dumps(blender_exec(code, timeout=args.timeout), indent=2)[:4000])
