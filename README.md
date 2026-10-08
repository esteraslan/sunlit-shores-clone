# Sunlit Shores — tiny trails clone

Diorama pulau low-poly organik ala *Tiny Trails: Sunlit Shores*.
Pulau dimodelkan di **Blender** (smooth, deform-noise, vertex color),
dirender real-time di **Three.js** (ombak, foam, bloom, SSAO),
dengan HUD web 1:1 referensi.

```
Web (Three.js)                Blender (via MCP bridge)
┌─────────────────────┐      ┌──────────────────────┐
│ main.js             │      │ build_v3.py          │──▶ sunlit_shores_v3.blend
│  ├ GLB loader (v3)  │◀─────│ export_v3.py         │──▶ public/sunlit_shores_v3.glb
│  ├ air animasi      │      │ render_preview.py    │──▶ blender/preview.png
│  ├ foam + partikel  │      │ bridge_exec.py       │──▶ klien TCP bridge
│  ├ SSAO/Bloom/grade │      └──────────────────────┘
│  └ awan + perahu    │
└─────────────────────┘
```

## 1. Jalankan web

```powershell
cd sunlit-shores-clone
npm install
npm run dev      # buka http://localhost:5173
npm run build    # output deploy di dist/
```

| Kontrol | Aksi |
|---|---|
| Drag / scroll | Orbit / zoom |
| Q / E, tombol + − | Rotate / zoom (UI) |

## 2. Struktur proyek

```
sunlit-shores-clone/
├── index.html          # HUD ala Tiny Trails (judul, star card, quest card, hints)
├── src/
│   ├── main.js         # scene: GLB + air + foam + awan + partikel + post-processing
│   └── style.css       # font Nunito, cream cards, loader
├── public/
│   ├── sunlit_shores_v3.glb   # ← ASET AKTIF (organik, vertex color) 589 KB
│   ├── sunlit_shores_v2.glb   # generasi lama (kaku, arsip)
│   ├── sunlit_shores_pro.glb  # generasi lama (miring, arsip)
│   └── sunlit_shores.glb      # generasi pertama (arsip)
├── blender/
│   ├── bridge_exec.py  # klien TCP → Blender  (python bridge_exec.py <file.py> [--timeout N])
│   ├── build_v3.py     # ← BUILDER AKTIF: pulau organik (164 objek)
│   ├── build_v2.py / build_sunlit.py / build_tiny_trails.py  # builder lama (arsip)
│   ├── export_v3.py    # export koleksi SunlitV3 → public/sunlit_shores_v3.glb
│   ├── polish_v3.py    # Standard transform + exposure + framing kamera
│   ├── render_preview.py  # render EEVEE DioramaCam → preview.png (deferred)
│   ├── fix_cam_v2*.py / fix_scene.py / fix_look.py / polish_save.py  # util arsip
│   ├── probe_scene.py  # contoh query scene (versi, daftar objek)
│   ├── generate_island.py  # builder standalone tanpa bridge (bpy langsung)
│   ├── sunlit_shores_v3.blend # ← FILE AKTIF
│   └── preview.png     # render terakhir dari Blender
├── package.json        # three@0.160, vite@5
└── vite.config.js      # base './' (aman untuk deploy sub-path)
```

## 3. Pipeline aset Blender → Web

1. Edit `blender/build_v3.py`, kirim ke Blender yang sedang terbuka:
   ```powershell
   cd blender
   python bridge_exec.py build_v3.py --timeout 240
   ```
2. Cek render: `python bridge_exec.py render_preview.py --timeout 300` → buka `preview.png`.
3. Poles bila perlu (`polish_v3.py`), lalu export:
   ```powershell
   python bridge_exec.py export_v3.py --timeout 120
   ```
4. Web otomatis memakai `public/sunlit_shores_v3.glb` (dev hot-reload; `npm run build` untuk produksi).

> Aturan orientasi: JANGAN tambah rotasi di Three.js. Export glTF sudah
> mengonversi Z-up (Blender) → Y-up. Rotasi manual `rotation.x = -PI/2`
> adalah bug yang dulu membuat pulau miring 90°.

### Isi builder v3 (`build_v3.py`)

- **Tebing**: ring bmesh 56 segmen, deform noise 3 oktaf (`noise2`), profil
  bertingkat melebar ke atas (overhang), tutup bawah mengerucut.
- **Rumput**: cakram berlapis menjuntai (lip radius 1.06), tepi atas diterangkan.
- **Warna**: 1 material putih + vertex color `Color` — gradasi tebing
  gelap-dingin → terang-hangat + fake AO; rumput/pasir sisi gelap, atas vivid.
- **Vegetasi**: 3 cluster pohon (tengah/kiri/mercusuar) + palem pantai;
  skala 0.7–1.3, rotasi Y acak, miring 0–6°; tajuk 4–5 blob icosphere
  ber-noise; semak, batu kecil, bunga 3 warna; 5 tonjolan batu tebing; tangga.
- **Props**: mercusuar garis merah-putih + kubah, hut, 3 jembatan papan
  melengkung, perahu (lambung + tiang + layar), pulau jauh ×2.
- **Sun + DioramaCam** (34, −38, 28 → target (0,0,3)) ikut tersimpan di `.blend`.

## 4. Teknik render Three.js (`src/main.js`)

| Fitur | Implementasi |
|---|---|
| Material pulau | `vertexColors = true` (warna dari Blender, bukan lighting) |
| Pohon goyang | `onBeforeCompile` + `uTime`: sway sin berdasar posisi dunia, bobot tinggi lokal; amp 0.09 tajuk / 0.05 semak / 0.04 bunga |
| Perahu | mesh `Boat_*` di-`attach` ke grup (SETELAH traverse!) → bobbing easing `s²(3−2s)` + oleng |
| Foam | 2 ring/pulau (solid + dash berputar, opacity berdenyut), koordinat Blender (x,y) → three (x,−y) |
| Air | `MeshPhysicalMaterial` transmisi + vertex wave + `computeVertexNormals` |
| Cahaya | Hemisphere (langit `#cfe8ff`, tanah `#a8b06a`) + directional hangat `#ffe7c4`, PCFSoft 2048 |
| Fog | `Fog(0x3bb8f2, 70, 200)` tipis biru |
| Post | `EffectComposer`: Render → SSAO (½ res) → Bloom (0.28) → grading hangat + vignette → Output |
| Awan/partikel | sphere-fluff melayang + 180 fireflies additive |

> Pelajaran bug: `group.attach()` DI DALAM `traverse()` merusak iterasi
> (`Cannot read properties of undefined`). Kumpulkan dulu, attach belakangan.

## 5. Blender MCP bridge

Add-on resmi **Blender Lab MCP v1.0.3** (port `9876`) BUKAN server HTTP —
melainkan **bridge TCP**: request JSON + null-byte, respons JSON + null-byte.

```
{"type": "execute", "code": "<python, diakhiri result = {...}>", "strict_json": true}\0
→ {"status": "ok", "result": {...}}\0
```

- `blender/bridge_exec.py` = klien siap pakai (baca `.py` / stdin, `--timeout`).
- Render berat memakai pola **deferred**: definisikan `check_is_finished()`
  (return `None` = pending, `dict` = selesai), koneksi ditahan hingga render jadi.
- Cek via konsol devtools browser (`browser.console`) bila GLB gagal load.
- Integrasi OpenCode MCP native butuh biner MCP-server resmi
  (https://www.blender.org/lab/mcp-server/) didaftarkan di `mcp.servers`;
  sampai saat itu, `bridge_exec.py` adalah jalur kontrol langsung.

## 6. Deploy

```powershell
npm run build   # → dist/ (index.html + assets + *.glb), siap ke Netlify/Vercel/GH Pages
```

## 7. Roadmap

- [ ] Karakter pemain (pengganti kapsul/voxel) + kontrol WASD + lompat
- [ ] Sistem bintang/quest sesuai HUD (2/5 → interaktif)
- [ ] Air terjun + gua + interior mercusuar
- [ ] LOD / kompresi meshopt GLB (saat ini 589 KB, chunk JS ~600 KB)
- [ ] Mode malam (sun-cycle) via tombol UI yang sudah ada
