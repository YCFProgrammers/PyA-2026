import aiohttp
import asyncio
import json
import os

OUTPUT_FILE = "exercises.json"

USUARIOS = [
    "g964",
    "GiacomoSorbi",
    "smile67",
    "FArekkusu",
    "hobovsky",
    "Blind4Basics",
]

def normalizar_kyu(nombre: str) -> str:
    return nombre.replace(" ", "").lower()

# Cargar y normalizar el JSON existente
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    KATAS = {}
    for key, slugs in raw.items():
        normalized = normalizar_kyu(key)
        if normalized not in KATAS:
            KATAS[normalized] = []
        KATAS[normalized].extend(slugs)
    print(f"✅ JSON cargado y normalizado — {sum(len(v) for v in KATAS.values())} katas existentes")
else:
    KATAS = {}
    print("📄 No se encontró exercises.json, se creará uno nuevo")

SLUGS_EXISTENTES = {slug for slugs in KATAS.values() for slug in slugs}

async def fetch_katas_usuario(session: aiohttp.ClientSession, usuario: str) -> list[str]:
    slugs = []
    page = 0
    print(f"\n📡 Obteniendo katas de '{usuario}'...")
    while True:
        url = f"https://www.codewars.com/api/v1/users/{usuario}/code-challenges/completed?page={page}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"  ❌ Error {response.status} en página {page}")
                    break
                data = await response.json()
                items = data.get("data", [])
                if not items:
                    break
                for item in items:
                    slugs.append(item["slug"])
                total_pages = data.get("totalPages", 1)
                print(f"  📄 Página {page + 1}/{total_pages} — {len(items)} katas")
                if page + 1 >= total_pages:
                    break
                page += 1
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ❌ Excepción: {e}")
            break
    print(f"  ✅ {len(slugs)} katas obtenidos de '{usuario}'")
    return slugs

async def fetch_kata_info(session: aiohttp.ClientSession, slug: str) -> dict | None:
    url = f"https://www.codewars.com/api/v1/code-challenges/{slug}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                return await response.json()
            return None
    except Exception:
        return None

def guardar(result: dict):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

async def main():
    result = {k: list(v) for k, v in KATAS.items()}
    nuevos = 0

    async with aiohttp.ClientSession() as session:
        for usuario in USUARIOS:
            slugs = await fetch_katas_usuario(session, usuario)
            slugs_nuevos = [s for s in slugs if s not in SLUGS_EXISTENTES]
            print(f"  🆕 {len(slugs_nuevos)} katas nuevos de '{usuario}'")

            for slug in slugs_nuevos:
                kata = await fetch_kata_info(session, slug)
                if not kata:
                    continue

                rank_info = kata.get("rank") or {}
                real_kyu = (rank_info.get("name") or "").strip()

                if not real_kyu:
                    print(f"  ⚠️ {slug} -> sin kyu, se omite")
                    continue

                real_kyu = normalizar_kyu(real_kyu)

                if real_kyu not in result:
                    result[real_kyu] = []

                result[real_kyu].append(slug)
                SLUGS_EXISTENTES.add(slug)
                nuevos += 1
                print(f"  ✅ [{nuevos}] {slug} -> {real_kyu}")

                if nuevos % 100 == 0:
                    guardar(result)
                    print(f"  💾 Guardado parcial — {nuevos} katas")

                await asyncio.sleep(0.3)

    guardar(result)
    print(f"\n✅ Listo — {nuevos} katas nuevos agregados")
    print(f"📊 Total por dificultad:")
    for kyu, slugs in sorted(result.items()):
        print(f"   {kyu}: {len(slugs)} katas")

if __name__ == "__main__":
    asyncio.run(main())