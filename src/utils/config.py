"""Pemuat konfigurasi YAML.

Muat sekali di awal (cli.py atau run_scenario.py), lalu oper sebagai argumen ke node,
supaya semua bagian memakai pengaturan yang sama.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # folder utama repo
CONFIG_DIR = ROOT / "configs"
NAMA_CONFIG = ("models", "spec_bersama", "template_draf")


def load_config(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config tidak ditemukan: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all() -> dict:
    return {nama: load_config(nama) for nama in NAMA_CONFIG}