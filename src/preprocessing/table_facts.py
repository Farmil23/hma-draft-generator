"""Membaca, memvalidasi, dan menghitung fakta dari tabel hasil (CSV).

Aturan format ada di templates/PETUNJUK_TABEL.md.
- periksa_tabel()  : dipakai Input Checker (mengumpulkan semua kesalahan format).
- proses_results() : dipakai praproses; membaca tabel, menghitung fakta, mengembalikan data.
- simpan_fakta()   : menyimpan fakta ke data/scenarios/<ID>/fakta_tabel.json untuk audit.
Semua hitungan deterministik (tanpa LLM).
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

TIPE_VALID = ("perbandingan", "deret_waktu")
BATAS_BARIS_BESAR = 50
MAKS_CONTOH = 3


class TabelError(ValueError):
    """Dilempar jika tabel tidak memenuhi format; pesan berisi semua kesalahan."""


@dataclass
class HasilPeriksa:
    df: pd.DataFrame | None = None
    kolom_label: str | None = None
    kesalahan: list[str] = field(default_factory=list)
    peringatan: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.kesalahan


def _daftar(nomor: list[int], maks: int = 5) -> str:
    teks = ", ".join(str(n) for n in nomor[:maks])
    return teks + (", ..." if len(nomor) > maks else "")


def periksa_tabel(jalur, tipe: str = "perbandingan", kolom_label: str | None = None) -> HasilPeriksa:
    """Memeriksa satu file CSV. Nomor baris pada pesan = nomor baris di spreadsheet (judul = baris 1)."""
    h = HasilPeriksa()
    jalur = Path(jalur)

    if tipe not in TIPE_VALID:
        h.kesalahan.append(f"Tipe tabel '{tipe}' tidak dikenal; pilih salah satu: {', '.join(TIPE_VALID)}.")
        return h
    if not jalur.exists():
        h.kesalahan.append(f"File tidak ditemukan: {jalur}.")
        return h

    try:
        with open(jalur, encoding="utf-8-sig", newline="") as f:
            baris = [b for b in csv.reader(f) if any(sel.strip() for sel in b)]
    except UnicodeDecodeError:
        h.kesalahan.append("File bukan UTF-8. Simpan ulang sebagai 'CSV UTF-8'.")
        return h
    if not baris:
        h.kesalahan.append("File kosong.")
        return h

    header = [s.strip() for s in baris[0]]
    if len(header) == 1 and (";" in header[0] or "\t" in header[0]):
        h.kesalahan.append("Pemisah kolom bukan koma (terdeteksi titik koma atau tab). Simpan sebagai CSV dengan pemisah koma.")
        return h
    if len(header) < 2:
        h.kesalahan.append("Minimal 2 kolom: satu kolom label dan satu kolom angka.")
    if any(not s for s in header):
        h.kesalahan.append("Ada judul kolom yang kosong.")
    dup = sorted({s for s in header if s and header.count(s) > 1})
    if dup:
        h.kesalahan.append(f"Judul kolom duplikat: {', '.join(dup)}.")

    data = baris[1:]
    if len(data) < 2:
        h.kesalahan.append("Minimal 2 baris data (di luar baris judul).")
    salah_lebar = [i + 2 for i, b in enumerate(data) if len(b) != len(header)]
    if salah_lebar:
        h.kesalahan.append(f"Jumlah kolom tidak sama dengan baris judul pada baris: {_daftar(salah_lebar)}.")
    if h.kesalahan:  # kesalahan struktur: berhenti sebelum memeriksa isi
        return h

    df = pd.DataFrame([[s.strip() for s in b] for b in data], columns=header)
    label = kolom_label or header[0]
    if label not in df.columns:
        h.kesalahan.append(f"kolom_label '{label}' tidak ada di judul kolom ({', '.join(header)}).")
        return h

    # --- kolom label ---
    kosong = [i + 2 for i, v in df[label].items() if v == ""]
    if kosong:
        h.kesalahan.append(f"Kolom label '{label}': sel kosong pada baris {_daftar(kosong)}.")
    nilai_dup = sorted({v for v in df[label] if v and (df[label] == v).sum() > 1})
    if nilai_dup:
        h.kesalahan.append(f"Kolom label '{label}': nilai duplikat ({', '.join(nilai_dup[:MAKS_CONTOH])}). Label harus unik.")

    # --- kolom angka ---
    for kol in [c for c in df.columns if c != label]:
        s = df[kol]
        kosong = [i + 2 for i, v in s.items() if v == ""]
        if kosong:
            h.kesalahan.append(f"Kolom '{kol}': sel kosong pada baris {_daftar(kosong)}.")
            continue
        n = pd.to_numeric(s, errors="coerce")
        buruk = [(i + 2, s[i]) for i in s.index if pd.isna(n[i]) or not np.isfinite(n[i])]
        if buruk:
            contoh = ", ".join(f"baris {r}: '{v}'" for r, v in buruk[:MAKS_CONTOH])
            h.kesalahan.append(
                f"Kolom '{kol}': nilai bukan angka ({contoh}). "
                "Gunakan titik sebagai pemisah desimal (84.2), tanpa %, satuan, atau pemisah ribuan."
            )
        else:
            df[kol] = n.astype(float)

    if len(df) > BATAS_BARIS_BESAR:
        h.peringatan.append(
            f"Tabel besar ({len(df)} baris). Agen hanya menerima ringkasan fakta; tabel lengkap tetap disisipkan utuh."
        )
    if h.kesalahan:
        return h
    h.df, h.kolom_label = df, label
    return h


def _ekstrem(df: pd.DataFrame, kol: str, label: str, fungsi: str, d: int) -> dict:
    nilai = df[kol]
    target = nilai.max() if fungsi == "max" else nilai.min()
    labels = df.loc[nilai == target, label].tolist()
    hasil = {"label": labels[0], "nilai": round(float(target), d)}
    if len(labels) > 1:
        hasil["seri"] = labels
    return hasil


def hitung_fakta(df: pd.DataFrame, kolom_label: str, tipe: str = "perbandingan", desimal: int = 2) -> dict:
    """Menghitung fakta per kolom angka. Hanya angka dan arah; tanpa interpretasi."""
    fakta = {
        "tipe": tipe,
        "kolom_label": kolom_label,
        "jumlah_baris": int(len(df)),
        "label_baris": df[kolom_label].tolist(),
        "kolom": {},
    }
    for kol in df.columns:
        if kol == kolom_label:
            continue
        s = df[kol]
        info = {
            "tertinggi": _ekstrem(df, kol, kolom_label, "max", desimal),
            "terendah": _ekstrem(df, kol, kolom_label, "min", desimal),
            "rata_rata": round(float(s.mean()), desimal),
            "rentang": round(float(s.max() - s.min()), desimal),
        }
        if tipe == "perbandingan":
            info["peringkat"] = df.sort_values(kol, ascending=False, kind="stable")[kolom_label].tolist()
        else:  # deret_waktu
            awal, akhir = float(s.iloc[0]), float(s.iloc[-1])
            a, b = round(awal, desimal), round(akhir, desimal)
            info["tren"] = {
                "awal": a,
                "akhir": b,
                "perubahan": round(akhir - awal, desimal),
                "persen_perubahan": round((akhir - awal) / abs(awal) * 100, desimal) if awal != 0 else None,
                "arah": "naik" if b > a else "turun" if b < a else "tetap",
            }
        fakta["kolom"][kol] = info
    return fakta


def proses_results(inp: dict, folder, desimal: int = 2) -> tuple[list, dict, list]:
    """Membaca semua tabel di inp['results'] (relatif terhadap folder skenario).

    Mengembalikan (results_dengan_data, fakta_tabel, peringatan).
    Melempar TabelError berisi semua kesalahan dari semua tabel.
    """
    folder = Path(folder)
    results, fakta, peringatan, galat = [], {}, [], []
    for item in inp["results"]:
        tipe = item.get("tipe", "perbandingan")
        h = periksa_tabel(folder / item["file"], tipe, item.get("kolom_label"))
        peringatan += [f"{item['id']}: {p}" for p in h.peringatan]
        if not h.ok:
            galat += [f"{item['id']} ({item['file']}): {k}" for k in h.kesalahan]
            continue
        fakta[item["id"]] = hitung_fakta(h.df, h.kolom_label, tipe, desimal)
        results.append({**item, "data": h.df.to_dict("records")})
    if galat:
        raise TabelError("\n".join(galat))
    return results, fakta, peringatan


def simpan_fakta(fakta: dict, folder) -> Path:
    """Menyimpan fakta ke <folder>/fakta_tabel.json (untuk audit)."""
    jalur = Path(folder) / "fakta_tabel.json"
    jalur.parent.mkdir(parents=True, exist_ok=True)
    jalur.write_text(json.dumps(fakta, ensure_ascii=False, indent=2), encoding="utf-8")
    return jalur