# agregar_kata.py
import asyncio
import aiohttp
import json

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

    with open("exersices.json", "r", encoding="utf-8") as f:
        katas = json.load(f)

    if kyu not in katas:
        print(f"❌ Nivel '{kyu}' no existe. Opciones: {list(katas.keys())}")
        return

    if slug in katas[kyu]:
        print(f"⚠️  '{slug}' ya está en {kyu}.")
        return

    katas[kyu].append(slug)
    with open("exersices.json", "w", encoding="utf-8") as f:
        json.dump(katas, f, indent=4)

    print(f"✅ '{slug}' agregado a {kyu} correctamente.")


async def main():
    slug = input("Slug del kata: ").strip()
    kyu  = input("Nivel (8kyu, 7kyu... 1kyu): ").strip()
    await verificar_y_agregar(slug, kyu)


asyncio.run(main())