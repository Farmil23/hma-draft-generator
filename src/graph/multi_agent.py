from typing import TypedDict

class DraftState(TypedDict):
    # input pengguna (tidak berubah)
    metadata: dict
    rumusan_masalah: list[str]
    tujuan: list[str]
    gambaran_isi: str
    metode: str
    results: list[dict]          # tabel + id (T1, T2)
    fakta_tabel: dict            # fakta turunan dihitung kode (maks, min, selisih, tren)

    # dibuat sekali di awal, lalu dibekukan
    reference_bank: dict         # {'R1': {...}, 'R2': {...}}
    konteks_bagian: dict         # {'pendahuluan': ['R1','R4'], ...} hasil retrieval top-k

    # output tiap agen (satu bagian = satu field)
    pendahuluan: str
    metode_teks: str
    pembahasan: str
    kesimpulan: str
    abstrak: str

    # kontrol
    rencana: dict                # keputusan Supervisor: bagian, urutan, entri bank
    validasi: dict               # hasil Validator per bagian
    bagian_gagal: list[str]      # bagian yang perlu diulang
    retry_count: dict            # {'pendahuluan': 0, ...}
    log_penggunaan: list[dict]   # token, latensi, per node