import json
import os
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"

NOMINATIM_HEADERS = {
    "User-Agent": "JiuJitsuEsDirectory/1.0 (contacto@jiu-jitsu.es)",
    "Accept-Language": "es",
}

# Palabras obligatorias en el nombre o etiquetas para evitar falsos positivos (como panaderías o comercios)
PALABRAS_VALIDAS = [
    "jiu",
    "bjj",
    "gracie",
    "grappling",
    "mma",
    "dojo",
    "checkmat",
    "alliance",
    "atos",
    "lotus",
    "gfteam",
    "tenth planet",
    "10th planet",
    "fight",
    "combat",
    "artes marciales",
    "martial",
    "tatami",
    "kimura",
    "budo",
    "zenit",
    "carpe diem",
    "nova uniao",
    "de la riva",
    "carlson",
    "roger",
]

PALABRAS_EXCLUIDAS = ["fleca", "panader", "restaurante", "bar ", "farmacia"]

TERMINOS_BUSQUEDA = [
    # Términos generales y grandes equipos en toda España
    "Brazilian Jiu Jitsu",
    "Jiu-Jitsu",
    "Jiu Jitsu",
    "BJJ",
    "Grappling",
    "Gracie Barra",
    "Gracie Jiu Jitsu",
    "Roger Gracie",
    "Carlson Gracie",
    "Checkmat",
    "Alliance",
    "Atos",
    "GFTeam",
    "Lotus Club",
    "Tenth Planet",
    "10th Planet",
    "De La Riva",
    "Nova Uniao",
    "Zenit BJJ",
    "Mathias Ribeiro",
    "Ases Jiu Jitsu",
    "Aranha",
    # Búsqueda específica por ciudades y provincias clave
    "Jiu Jitsu Madrid",
    "BJJ Madrid",
    "Grappling Madrid",
    "Jiu Jitsu Barcelona",
    "BJJ Barcelona",
    "Grappling Barcelona",
    "Jiu Jitsu Valencia",
    "BJJ Valencia",
    "Jiu Jitsu Sevilla",
    "BJJ Sevilla",
    "Jiu Jitsu Málaga",
    "BJJ Málaga",
    "BJJ Marbella",
    "Jiu Jitsu Alicante",
    "BJJ Alicante",
    "BJJ Elche",
    "Jiu Jitsu Bilbao",
    "BJJ Bilbao",
    "Jiu Jitsu San Sebastián",
    "Jiu Jitsu Zaragoza",
    "BJJ Zaragoza",
    "Jiu Jitsu Murcia",
    "BJJ Murcia",
    "Jiu Jitsu Palma",
    "BJJ Mallorca",
    "BJJ Ibiza",
    "Jiu Jitsu Las Palmas",
    "BJJ Gran Canaria",
    "Jiu Jitsu Tenerife",
    "BJJ Tenerife",
    "Jiu Jitsu Granada",
    "Jiu Jitsu Cádiz",
    "Jiu Jitsu Córdoba",
    "Jiu Jitsu A Coruña",
    "Jiu Jitsu Vigo",
    "Jiu Jitsu Gijón",
    "Jiu Jitsu Oviedo",
    "Jiu Jitsu Santander",
    "Jiu Jitsu Pamplona",
    "Jiu Jitsu Valladolid",
    "Jiu Jitsu Tarragona",
    "Jiu Jitsu Girona",
]


def es_academia_valida(nombre, categoria="", tipo=""):
  texto = f"{nombre} {categoria} {tipo}".lower()
  if any(ex in texto for ex in PALABRAS_EXCLUIDAS):
    return False
  return any(val in texto for val in PALABRAS_VALIDAS)


def cargar_existentes():
  if not os.path.exists(ARCHIVO_JSON):
    return []
  with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    try:
      data = json.load(f)
      lista = data if isinstance(data, list) else data.get("academias", [])
      # Limpiar posibles falsos positivos previos (como Baobab Fleca)
      return [
          ac
          for ac in lista
          if not any(
              ex in str(ac.get("nombre", "")).lower()
              for ex in PALABRAS_EXCLUIDAS
          )
      ]
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
      "vic": "Cataluña",
      "valencia": "Comunidad Valenciana",
      "alicante": "Comunidad Valenciana",
      "elche": "Comunidad Valenciana",
      "castell": "Comunidad Valenciana",
      "quart de poblet": "Comunidad Valenciana",
      "sevilla": "Andalucía",
      "málaga": "Andalucía",
      "malaga": "Andalucía",
      "marbella": "Andalucía",
      "fuengirola": "Andalucía",
      "antequera": "Andalucía",
      "granada": "Andalucía",
      "cádiz": "Andalucía",
      "cadiz": "Andalucía",
      "tarifa": "Andalucía",
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
  print(f"Academias válidas previas: {len(academias)}")

  vistos = set()
  for ac in academias:
    nombre = str(ac.get("nombre") or ac.get("name") or "").lower().strip()
    lat = float(ac.get("lat") or ac.get("latitude") or 0)
    lng = float(ac.get("lng") or ac.get("lon") or ac.get("longitude") or 0
    vistos.add(f"{nombre}_{round(lat, 2)}_{round(lng, 2)}")

  nuevas = 0
  for termino in TERMINOS_BUSQUEDA:
    try:
      resp = requests.get(
          NOMINATIM_URL,
          params={
              "q": termino,
              "format": "jsonv2",
              "countrycodes": "es",
              "addressdetails": 1,
              "extratags": 1,
              "limit": 50,
          },
          headers=NOMINATIM_HEADERS,
          timeout=12,
      )
      time.sleep(1.1)
      if resp.status_code != 200:
        continue

      for item in resp.json():
        nombre = item.get("name")
        if not nombre:
          continue

        extratags = item.get("extratags") or {}
        deporte = extratags.get("sport", "")
        if not es_academia_valida(nombre, deporte, item.get("type", "")):
          continue

        lat = float(item["lat"])
        lng = float(item["lon"])
        clave = f"{nombre.lower().strip()}_{round(lat, 2)}_{round(lng, 2)}"
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
        print(f"  + {nombre} ({ciudad})")
    except Exception as e:
      print(f"Error en '{termino}': {e}")

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
