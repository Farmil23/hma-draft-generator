from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]  # folder utama project

def load_config(name: str) -> dict:
    path = ROOT / "configs" / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    models = load_config("models")
    print(models["generator"]["model"])