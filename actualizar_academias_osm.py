import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

SMOOTHCOMP_ACADEMIES_URL = "https://smoothcomp.com/es/academies"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}

NOMINATIM_HEADERS = {
    "User-Agent": "JiuJitsuEsDirectory/1.0 (contacto@jiu-jitsu.es)",
    "Accept-Language": "es",
}

# Cache de coordenadas por ciudad para no repetir llamadas innecesarias a Nominatim
CACHE_CIUDADES = {}


def cargar_existentes():
  if not os.path.exists(ARCHIVO_JSON):
    return []
  with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    try:
      data = json.load(f)
      return data if isinstance(data, list) else data.get("academias", [])
    except Exception:
      return []


def detectar_region(texto_completo):
  texto = texto_completo.lower()
  mapa_regiones = {
      "madrid": "Madrid",
      "barcelona": "Cataluña",
      "girona": "Cataluña",
      "tarragona": "Cataluña",
      "lleida": "Cataluña",
      "badalona": "Cataluña",
      "hospitalet": "Cataluña",
      "sabadell": "Cataluña",
      "terrassa": "Cataluña",
      "valencia": "Comunidad Valenciana",
      "alicante": "Comunidad Valenciana",
      "elche": "Comunidad Valenciana",
      "castell": "Comunidad Valenciana",
      "sevilla": "Andalucía",
      "málaga": "Andalucía",
      "malaga": "Andalucía",
      "marbella": "Andalucía",
      "fuengirola": "Andalucía",
      "granada": "Andalucía",
      "cádiz": "Andalucía",
      "cadiz": "Andalucía",
      "jerez": "Andalucía",
      "córdoba": "Andalucía",
      "cordoba": "Andalucía",
      "almería": "Andalucía",
      "almeria": "Andalucía",
      "huelva": "Andalucía",
      "jaén": "Andalucía",
      "jaen": "Andalucía",
      "palma": "Islas Baleares",
      "ibiza": "Islas Baleares",
      "eivissa": "Islas Baleares",
      "mallorca": "Islas Baleares",
      "menorca": "Islas Baleares",
      "baleares": "Islas Baleares",
      "palmas": "Islas Canarias",
      "tenerife": "Islas Canarias",
      "canarias": "Islas Canarias",
      "lanzarote": "Islas Canarias",
      "fuerteventura": "Islas Canarias",
      "bilbao": "País Vasco",
      "bizkaia": "País Vasco",
      "vizcaya": "País Vasco",
      "san sebasti": "País Vasco",
      "donostia": "País Vasco",
      "gipuzkoa": "País Vasco",
      "vitoria": "País Vasco",
      "zaragoza": "Aragón",
      "murcia": "Región de Murcia",
      "cartagena": "Región de Murcia",
      "coruña": "Galicia",
      "vigo": "Galicia",
      "pontevedra": "Galicia",
      "santiago": "Galicia",
      "asturias": "Asturias",
      "gijón": "Asturias",
      "oviedo": "Asturias",
      "cantabria": "Cantabria",
      "santander": "Cantabria",
      "navarra": "Navarra",
      "pamplona": "Navarra",
      "valladolid": "Castilla y León",
      "león": "Castilla y León",
      "salamanca": "Castilla y León",
      "burgos": "Castilla y León",
      "toledo": "Castilla-La Mancha",
      "albacete": "Castilla-La Mancha",
      "badajoz": "Extremadura",
      "cáceres": "Extremadura",
      "logroño": "La Rioja",
      "rioja": "La Rioja",
  }
  for clave, region in mapa_regiones.items():
    if clave in texto:
      return region
  return "Otras"


def geocodificar(nombre, ciudad):
  # 1. Intentar primero buscar el nombre exacto de la academia en España
  clave_cache = f"{nombre.lower()}_{ciudad.lower()}"
  if clave_cache in CACHE_CIUDADES:
    return CACHE_CIUDADES[clave_cache]

  for query in [f"{nombre}, {ciudad}, España", f"{ciudad}, España"]:
    if not ciudad and query.startswith(","):
      continue
    if query in CACHE_CIUDADES:
      return CACHE_CIUDADES[query]
    try:
      resp = requests.get(
          NOMINATIM_URL,
          params={
              "q": query,
              "format": "jsonv2",
              "countrycodes": "es",
              "limit": 1,
          },
          headers=NOMINATIM_HEADERS,
          timeout=10,
      )
      time.sleep(1.1)
      if resp.status_code == 200 and resp.json():
        item = resp.json()[0]
        coords = (
            float(item["lat"]),
            float(item["lon"]),
            item.get("display_name", ""),
        )
        CACHE_CIUDADES[query] = coords
        return coords
    except Exception:
      continue
  return None


def generar_geojson(academias):
  features = []
  for ac in academias:
    lat = ac.get("lat") or ac.get("latitude")
    lng = ac.get("lng") or ac.get("lon") or ac.get("longitude")
    if lat is None or lng is None:
      continue
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(lng), float(lat)]},
        "properties": ac,
    })
  return {"type": "FeatureCollection", "features": features}


def obtener_academias_smoothcomp():
  encontradas = []
  # Recorre las primeras páginas filtradas por país España (country=ES)
  for page in range(1, 15):
    url = f"{SMOOTHCOMP_ACADEMIES_URL}?country=ES&page={page}"
    print(f"Consultando Smoothcomp página {page}...")
    try:
      resp = requests.get(url, headers=HEADERS, timeout=20)
      if resp.status_code != 200:
        print(f"  -> HTTP {resp.status_code}, deteniendo paginación.")
        break
    except Exception as e:
      print(f"  -> Error de conexión: {e}")
      break

    soup = BeautifulSoup(resp.text, "html.parser")
    tarjetas = soup.select(
        ".academy-card, .panel-academy, a[href*='/academies/']"
    )

    items_pagina = 0
    for tag in tarjetas:
      href = tag.get("href") or ""
      if "/academies/" not in href or href.endswith("/academies/"):
        continue

      texto = " ".join(tag.get_text(" ", strip=True).split())
      if not texto or len(texto) < 3:
        continue

      # Limpiar nombre y posible ciudad del texto de la tarjeta
      nombre = texto.split("Spain")[0].split("España")[0].strip()
      if len(nombre) > 80:
        nombre = nombre[:80].strip()

      link = (
          href
          if href.startswith("http")
          else f"https://smoothcomp.com{href}"
      )
      encontradas.append({
          "nombre": nombre,
          "web": link,
          "texto_completo": texto,
      })
      items_pagina += 1

    print(f"  -> Enlaces detectados en página {page}: {items_pagina}")
    if items_pagina == 0:
      break
    time.sleep(1)

  return encontradas


def main():
  academias = cargar_existentes()
  print(f"Academias previas cargadas: {len(academias)}")

  nombres_existentes = {
      str(ac.get("nombre") or ac.get("name") or "").lower().strip()
      for ac in academias
  }

  crudo = obtener_academias_smoothcomp()
  print(f"Total bruto extraído de Smoothcomp: {len(crudo)}")

  nuevas = 0
  for item in crudo:
    nombre = item["nombre"]
    if not nombre or nombre.lower().strip() in nombres_existentes:
      continue

    # Intentar extraer ciudad si aparece después de una coma o palabra clave
    ciudad = ""
    match_ciudad = re.search(
        r"(Madrid|Barcelona|Valencia|Sevilla|Málaga|Alicante|Bilbao|Zaragoza|Murcia|Palma|Ibiza|Tenerife|Las Palmas|Granada|Cádiz|Vigo|Coruña|Gijón|Oviedo|Santander|Pamplona|Valladolid|Marbella|Elche)",
        item["texto_completo"],
        re.I,
    )
    if match_ciudad:
      ciudad = match_ciudad.group(1).title()

    coords = geocodificar(nombre, ciudad)
    if not coords:
      continue

    lat, lng, display_name = coords
    nombres_existentes.add(nombre.lower().strip())

    academias.append({
        "nombre": nombre,
        "ciudad": ciudad if ciudad else "España",
        "region": detectar_region(f"{ciudad} {display_name}"),
        "direccion": display_name if display_name else "España",
        "lat": lat,
        "lng": lng,
        "web": item["web"],
        "telefono": "",
        "fuente": "Smoothcomp",
    })
    nuevas += 1
    print(f"  + Agregada: {nombre} ({ciudad or 'España'})")

  with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(academias, f, ensure_ascii=False, indent=2)

  geojson = generar_geojson(academias)
  with open(ARCHIVO_GEOJSON, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

  print(
      f"Proceso finalizado: {nuevas} academias nuevas agregadas (Total:"
      f" {len(academias)})."
  )


if __name__ == "__main__":
  main()
