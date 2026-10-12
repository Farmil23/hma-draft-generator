from src.utils.config import load_all

cfg = load_all()
models, spec, template = cfg["models"], cfg["spec_bersama"], cfg["template_draf"]


def test_semua_config_termuat():
    for nama, isi in cfg.items():
        assert isinstance(isi, dict) and isi, f"{nama} kosong"


def test_generator_dan_judge_beda_keluarga():
    assert models["generator"]["keluarga"] != models["judge"]["keluarga"]
    assert models["generator"]["model"] != models["judge"]["model"]


def test_parameter_penting():
    assert isinstance(models["validator"]["max_retry"], int)
    assert all(isinstance(k, int) and k > 0 for k in models["retrieval"]["top_k"].values())
    assert models["judge"]["temperature"] == 0.0
    assert models["eksperimen"]["pengulangan"] >= 1


def test_bahasa_valid():
    assert spec["bahasa_draf"] in spec["nama_bahasa"]
    assert spec["bahasa_draf"] in spec["frasa_bukti_tidak_cukup"]
    assert spec["bahasa_draf"] in spec["kata_penguat_terbatas"]


def test_template_konsisten():
    for nama in template["urutan_bagian"]:
        assert nama in template["bagian"], f"bagian {nama} tidak didefinisikan"
    for nama, b in template["bagian"].items():
        if "target_kata" in b:
            assert b["target_kata"]["min"] < b["target_kata"]["max"]
            assert b.get("heading"), f"{nama} butuh heading"


def test_penanda_tabel_punya_id():
    assert "{id}" in template["penanda_tabel"]


def test_retrieval_embedding():
    r = models["retrieval"]
    assert r["metode"] == "embedding"
    e = r["embedding"]
    assert e["model"] and e["awalan_query"] and e["awalan_passage"]
    assert set(r["kueri_per_bagian"]) == set(r["top_k"])
    
    