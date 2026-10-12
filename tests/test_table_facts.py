import json
from pathlib import Path

import pytest

from src.preprocessing.table_facts import (
    BATAS_BARIS_BESAR,
    TabelError,
    hitung_fakta,
    periksa_tabel,
    proses_results,
    simpan_fakta,
)

ROOT = Path(__file__).resolve().parents[1]
PERBANDINGAN = "model,akurasi,f1\nRandom Forest,84.2,79.5\nLogistic Regression,80.1,74.3\n"


def tulis(tmp_path, isi, nama="t.csv"):
    p = tmp_path / nama
    p.write_text(isi, encoding="utf-8")
    return p


def test_template_perbandingan_valid():
    assert periksa_tabel(ROOT / "templates" / "template_perbandingan.csv").ok


def test_template_deret_waktu_valid():
    assert periksa_tabel(ROOT / "templates" / "template_deret_waktu.csv", "deret_waktu").ok


def test_fakta_perbandingan(tmp_path):
    h = periksa_tabel(tulis(tmp_path, PERBANDINGAN))
    assert h.ok
    k = hitung_fakta(h.df, h.kolom_label, "perbandingan")["kolom"]
   
    assert k["akurasi"]["tertinggi"] == {"label": "Random Forest", "nilai": 84.2}
    assert k["akurasi"]["terendah"]["label"] == "Logistic Regression"
    assert k["akurasi"]["rentang"] == 4.1
    assert k["akurasi"]["rata_rata"] == 82.15
    assert k["akurasi"]["peringkat"] == ["Random Forest", "Logistic Regression"]
    assert k["f1"]["rentang"] == 5.2


def test_fakta_deret_waktu(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "periode,aktual\n2025-01,100\n2025-02,110\n2025-03,121\n"), "deret_waktu")
    assert h.ok
    tren = hitung_fakta(h.df, h.kolom_label, "deret_waktu")["kolom"]["aktual"]["tren"]
    assert tren == {"awal": 100.0, "akhir": 121.0, "perubahan": 21.0, "persen_perubahan": 21.0, "arah": "naik"}


def test_seri_dicatat(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "m,v\nA,5\nB,5\nC,1\n"))
    assert hitung_fakta(h.df, h.kolom_label)["kolom"]["v"]["tertinggi"]["seri"] == ["A", "B"]


def test_koma_desimal_ditolak(tmp_path):
    h = periksa_tabel(tulis(tmp_path, 'model,akurasi\nA,"84,2"\nB,"80,1"\n'))
    assert not h.ok
    assert any("titik sebagai pemisah desimal" in k for k in h.kesalahan)


def test_titik_koma_ditolak(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "model;akurasi\nA;84.2\nB;80.1\n"))
    assert not h.ok
    assert "Pemisah" in h.kesalahan[0]


def test_sel_kosong_ditolak(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "model,akurasi\nA,84.2\nB,\n"))
    assert not h.ok
    assert any("kosong" in k for k in h.kesalahan)


def test_simbol_persen_ditolak(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "model,akurasi\nA,84.2%\nB,80.1%\n"))
    assert not h.ok


def test_label_duplikat_ditolak(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "model,akurasi\nA,1\nA,2\n"))
    assert not h.ok
    assert any("duplikat" in k for k in h.kesalahan)


def test_kolom_label_tidak_ada(tmp_path):
    h = periksa_tabel(tulis(tmp_path, PERBANDINGAN), kolom_label="xyz")
    assert not h.ok


def test_kurang_dari_dua_baris(tmp_path):
    h = periksa_tabel(tulis(tmp_path, "model,akurasi\nA,1\n"))
    assert not h.ok


def test_tabel_besar_hanya_peringatan(tmp_path):
    isi = "id,nilai\n" + "".join(f"B{i},{i}\n" for i in range(BATAS_BARIS_BESAR + 10))
    h = periksa_tabel(tulis(tmp_path, isi))
    assert h.ok and h.peringatan


def test_proses_results_dan_simpan(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "t1.csv").write_text(PERBANDINGAN, encoding="utf-8")
    inp = {"results": [{"id": "T1", "keterangan": "x", "file": "results/t1.csv"}]}
    results, fakta, peringatan = proses_results(inp, tmp_path)
    assert results[0]["data"][0] == {"model": "Random Forest", "akurasi": 84.2, "f1": 79.5}
    assert fakta["T1"]["kolom"]["akurasi"]["rentang"] == 4.1
    jalur = simpan_fakta(fakta, tmp_path)
    assert json.loads(jalur.read_text(encoding="utf-8"))["T1"]["jumlah_baris"] == 2


def test_proses_results_gagal_melempar(tmp_path):
    (tmp_path / "t.csv").write_text("model;akurasi\nA;1\nB;2\n", encoding="utf-8")
    inp = {"results": [{"id": "T1", "keterangan": "x", "file": "t.csv"}]}
    with pytest.raises(TabelError, match="T1"):
        proses_results(inp, tmp_path)
        
    