import json
import os
import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"

# Consulta Overpass QL para toda España (ISO3166-1 = ES)
overpass_query = """
[out:json][timeout:60];
area["ISO3166-1"="ES"][admin_level=2]->.espana;
(
  node["sport"~"brazilian_jiu_jitsu|bjj|jiu-jitsu",i](area.espana);
  way["sport"~"brazilian_jiu_jitsu|bjj|jiu-jitsu",i](area.espana);
  node["name"~"Brazilian Jiu|BJJ|Jiu-Jitsu Brasile|Jiu Jitsu Brasile",i](area.espana);
  way["name"~"Brazilian Jiu|BJJ|Jiu-Jitsu Brasile|Jiu Jitsu Brasile",i](area.espana);
);
out center tags;
"""


def cargar_existentes():
  if not os.path.exists(ARCHIVO_JSON):
    return []
  with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    try:
      data = json.load(f)
      return data if isinstance(data, list) else data.get("academias", [])
    except Exception:
      return []


def detectar_region(ciudad, provincia):
  texto = f"{ciudad} {provincia}".lower()
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
      "palmas": "Islas Canarias",
      "tenerife": "Islas Canarias",
      "canaria": "Islas Canarias",
      "bilbao": "País Vasco",
      "vizcaya": "País Vasco",
      "bizkaia": "País Vasco",
      "san sebasti": "País Vasco",
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

  # Índice de control para evitar duplicados (por nombre normalizado o coordenada cercana)
  vistos = set()
  for ac in academias:
    nombre = str(ac.get("nombre") or ac.get("name") or "").lower().strip()
    lat = ac.get("lat") or ac.get("latitude") or 0
    lng = ac.get("lng") or ac.get("lon") or ac.get("longitude") or 0
    vistos.add(f"{nombre}_{round(float(lat), 3)}_{round(float(lng), 3)}")

  print("Consultando OpenStreetMap para España...")
  resp = requests.post(OVERPASS_URL, data={"data": overpass_query}, timeout=90)
  resp.raise_for_status()
  elementos = resp.json().get("elements", [])

  nuevas = 0
  for el in elementos:
    tags = el.get("tags", {})
    nombre = tags.get("name")
    if not nombre:
      continue

    lat = el.get("lat") or el.get("center", {}).get("lat")
    lng = el.get("lon") or el.get("center", {}).get("lon")
    if not lat or not lng:
      continue

    clave = f"{nombre.lower().strip()}_{round(float(lat), 3)}_{round(float(lng), 3)}"
    if clave in vistos:
      continue
    vistos.add(clave)

    calle = tags.get("addr:street", "")
    numero = tags.get("addr:housenumber", "")
    ciudad = (
        tags.get("addr:city")
        or tags.get("addr:town")
        or tags.get("addr:municipality")
        or "España"
    )
    provincia = tags.get("addr:province") or tags.get("addr:state") or ""
    cp = tags.get("addr:postcode", "")
    direccion = ", ".join(filter(None, [f"{calle} {numero}".strip(), cp, ciudad]))

    web = (
        tags.get("website")
        or tags.get("contact:website")
        or tags.get("contact:instagram")
        or tags.get("instagram")
        or ""
    )

    academias.append({
        "nombre": nombre,
        "ciudad": ciudad,
        "region": detectar_region(ciudad, provincia),
        "direccion": direccion if direccion else "Ver ubicación en mapa",
        "lat": float(lat),
        "lng": float(lng),
        "web": web,
        "telefono": tags.get("phone") or tags.get("contact:phone") or "",
        "fuente": "OpenStreetMap",
    })
    nuevas += 1

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
