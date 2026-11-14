import json
import os
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"

HEADERS = {
    "User-Agent": "JiuJitsuEsDirectory/1.0 (contacto@jiu-jitsu.es)",
    "Accept-Language": "es",
}

TERMINOS_BUSQUEDA = [
    "Brazilian Jiu Jitsu España",
    "BJJ España",
    "Jiu Jitsu Brasileño España",
    "Gracie Barra España",
    "Checkmat España",
    "Alliance Jiu Jitsu España",
    "Carlson Gracie España",
    "Atos Jiu Jitsu España",
    "Academia BJJ Madrid",
    "Academia BJJ Barcelona",
    "Academia BJJ Valencia",
    "Academia BJJ Sevilla",
    "Academia BJJ Málaga",
    "Academia BJJ Alicante",
    "Academia BJJ Bilbao",
    "Academia BJJ Zaragoza",
    "Academia BJJ Mallorca",
    "Academia BJJ Canarias",
]


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
      "valencia": "Comunidad Valenciana",
      "alicante": "Comunidad Valenciana",
      "castell": "Comunidad Valenciana",
      "sevilla": "Andalucía",
      "málaga": "Andalucía",
      "malaga": "Andalucía",
      "granada": "Andalucía",
      "cádiz": "Andalucía",
      "cadiz": "Andalucía",
      "córdoba": "Andalucía",
      "cordoba": "Andalucía",
      "almería": "Andalucía",
      "almeria": "Andalucía",
      "palma": "Islas Baleares",
      "ibiza": "Islas Baleares",
      "eivissa": "Islas Baleares",
      "mallorca": "Islas Baleares",
      "menorca": "Islas Baleares",
      "baleares": "Islas Baleares",
      "palmas": "Islas Canarias",
      "tenerife": "Islas Canarias",
      "canarias": "Islas Canarias",
      "bilbao": "País Vasco",
      "bizkaia": "País Vasco",
      "vizcaya": "País Vasco",
      "san sebasti": "País Vasco",
      "donostia": "País Vasco",
      "gipuzkoa": "País Vasco",
      "vitoria": "País Vasco",
      "zaragoza": "Aragón",
      "murcia": "Región de Murcia",
      "coruña": "Galicia",
      "vigo": "Galicia",
      "pontevedra": "Galicia",
      "asturias": "Asturias",
      "gijón": "Asturias",
      "oviedo": "Asturias",
      "cantabria": "Cantabria",
      "santander": "Cantabria",
      "navarra": "Navarra",
      "pamplona": "Navarra",
      "valladolid": "Castilla y León",
  }
  for clave, region in mapa_regiones.items():
    if clave in texto:
      return region
  return "Otras"


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


def main():
  academias = cargar_existentes()
  print(f"Academias previas cargadas: {len(academias)}")

  vistos = set()
  for ac in academias:
    nombre = str(ac.get("nombre") or ac.get("name") or "").lower().strip()
    lat = ac.get("lat") or ac.get("latitude") or 0
    lng = ac.get("lng") or ac.get("lon") or ac.get("longitude") or 0
    vistos.add(f"{nombre}_{round(float(lat), 3)}_{round(float(lng), 3)}")

  nuevas = 0
  for termino in TERMINOS_BUSQUEDA:
    print(f"Buscando: {termino}...")
    params = {
        "q": termino,
        "format": "jsonv2",
        "countrycodes": "es",
        "addressdetails": 1,
        "extratags": 1,
        "limit": 50,
    }
    try:
      resp = requests.get(
          NOMINATIM_URL, params=params, headers=HEADERS, timeout=15
      )
      print(f"  -> HTTP {resp.status_code}")
      if resp.status_code != 200:
        continue
      resultados = resp.json()
    except Exception as e:
      print(f"  -> Error: {e}")
      continue

    for item in resultados:
      nombre = item.get("name")
      if not nombre:
        continue

      lat = float(item["lat"])
      lng = float(item["lon"])
      clave = f"{nombre.lower().strip()}_{round(lat, 3)}_{round(lng, 3)}"
      if clave in vistos:
        continue
      vistos.add(clave)

      addr = item.get("address", {})
      ciudad = (
          addr.get("city")
          or addr.get("town")
          or addr.get("village")
          or addr.get("municipality")
          or "España"
      )
      display_name = item.get("display_name", "")
      extratags = item.get("extratags") or {}

      web = (
          extratags.get("website")
          or extratags.get("contact:website")
          or extratags.get("contact:instagram")
          or ""
      )

      academias.append({
          "nombre": nombre,
          "ciudad": ciudad,
          "region": detectar_region(display_name),
          "direccion": display_name,
          "lat": lat,
          "lng": lng,
          "web": web,
          "telefono": (
              extratags.get("phone") or extratags.get("contact:phone") or ""
          ),
          "fuente": "OpenStreetMap",
      })
      nuevas += 1
      print(f"  + Agregada: {nombre} ({ciudad})")

    time.sleep(1.2)  # Política oficial de Nominatim: máx 1 petición/segundo

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
