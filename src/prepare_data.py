import argparse
from pathlib import Path

def extract_7z(archive: Path, out_dir: Path) -> None:
    try:
        import py7zr  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Установите зависимости: pip install -r requirements.txt"
        ) from e

    out_dir.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(archive, mode="r") as z:
        z.extractall(path=out_dir)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=str, default="data/raw", help="Папка с архивами .7z")
    p.add_argument("--out", type=str, default="data/instances", help="Куда распаковать")
    args = p.parse_args()

    raw = Path(args.raw)
    out = Path(args.out)
    archives = sorted(raw.glob("*.7z"))
    if not archives:
        raise SystemExit(f"В {raw} не найдено архивов .7z")

    for a in archives:
        sub = out / a.stem
        print(f"[extract] {a.name} -> {sub}")
        extract_7z(a, sub)

    print("Готово. Внутри data/instances/* должны быть .vrp файлы.")

if __name__ == "__main__":
    main()
