# agregar_kata.py
import asyncio
import aiohttp
import json
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "exercises.json"


def normalizar_kyu(nombre: str) -> str:
    return nombre.replace(" ", "").lower()


async def verificar_y_agregar(slug: str, kyu: str):
    url = f"https://www.codewars.com/api/v1/code-challenges/{slug}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ El slug '{slug}' no existe en Codewars.")
                return

            data = await response.json()
            nombre = data.get("name", slug)
            rank   = data.get("rank", {}).get("name", "?")
            print(f"✅ Encontrado: '{nombre}' ({rank})")

    with OUTPUT_FILE.open("r", encoding="utf-8") as f:
        katas = json.load(f)

    # normalizar kyu igual que kata.py
    kyu = normalizar_kyu(kyu)

    if kyu not in katas:
        katas[kyu] = []

    if slug in katas[kyu]:
        print(f"⚠️  '{slug}' ya está en {kyu}.")
        return

    katas[kyu].append(slug)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(katas, f, indent=4, ensure_ascii=False)

    print(f"✅ '{slug}' agregado a {kyu} correctamente.")


async def main():
    slug = input("Slug del kata: ").strip()
    kyu  = input("Nivel (8kyu, 7kyu... 1kyu): ").strip()
    await verificar_y_agregar(slug, kyu)


if __name__ == "__main__":
    asyncio.run(main())
