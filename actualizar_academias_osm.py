import json
import os
import time
import requests

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"

HEADERS = {
    "User-Agent": "JiuJitsuEsDirectory/1.0 (https://jiu-jitsu.es)",
    "Accept": "application/json",
}

# Coordenadas aproximadas (lat, lng, radio_en_metros) de las principales zonas de España
ZONAS_ESPANA = [
    ("Madrid", 40.4168, -3.7038, 45000),
    ("Barcelona", 41.3851, 2.1734, 45000),
    ("Valencia", 39.4699, -0.3763, 40000),
    ("Alicante", 38.3452, -0.4810, 45000),
    ("Sevilla", 37.3891, -5.9845, 40000),
    ("Málaga", 36.7213, -4.4214, 50000),
    ("Granada", 37.1773, -3.5986, 35000),
    ("Cádiz", 36.5271, -6.2886, 45000),
    ("Murcia", 37.9922, -1.1307, 40000),
    ("Zaragoza", 41.6488, -0.8891, 35000),
    ("Bilbao", 43.2630, -2.9350, 40000),
    ("San Sebastián", 43.3183, -1.9812, 30000),
    ("Vitoria", 42.8467, -2.6716, 25000),
    ("A Coruña", 43.3623, -8.4115, 40000),
    ("Vigo", 42.2406, -8.7207, 35000),
    ("Gijón / Oviedo", 43.4600, -5.7500, 35000),
    ("Santander", 43.4623, -3.8099, 30000),
    ("Pamplona", 42.8125, -1.6458, 30000),
    ("Valladolid", 41.6523, -4.7245, 30000),
    ("Palma de Mallorca", 39.5696, 2.6502, 45000),
    ("Ibiza", 38.9067, 1.4206, 25000),
    ("Las Palmas de Gran Canaria", 28.1235, -15.4363, 40000),
    ("Santa Cruz de Tenerife", 28.4636, -16.2518, 45000),
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


def detectar_region(zona, ciudad):
  texto = f"{zona} {ciudad}".lower()
  mapa_regiones = {
      "madrid": "Madrid",
      "barcelona": "Cataluña",
      "valencia": "Comunidad Valenciana",
      "alicante": "Comunidad Valenciana",
      "sevilla": "Andalucía",
      "málaga": "Andalucía",
      "granada": "Andalucía",
      "cádiz": "Andalucía",
      "palma": "Islas Baleares",
      "ibiza": "Islas Baleares",
      "palmas": "Islas Canarias",
      "tenerife": "Islas Canarias",
      "bilbao": "País Vasco",
      "sebastián": "País Vasco",
      "vitoria": "País Vasco",
      "zaragoza": "Aragón",
      "murcia": "Región de Murcia",
      "coruña": "Galicia",
      "vigo": "Galicia",
      "gijón": "Asturias",
      "santander": "Cantabria",
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


def consultar_zona(lat, lng, radio):
  query = f"""
    [out:json][timeout:25];
    (
      node["sport"~"brazilian_jiu_jitsu|bjj|jiu-jitsu",i](around:{radio},{lat},{lng});
      way["sport"~"brazilian_jiu_jitsu|bjj|jiu-jitsu",i](around:{radio},{lat},{lng});
      node["name"~"Brazilian Jiu|BJJ|Jiu-Jitsu Brasile|Jiu Jitsu Brasile",i](around:{radio},{lat},{lng});
      way["name"~"Brazilian Jiu|BJJ|Jiu-Jitsu Brasile|Jiu Jitsu Brasile",i](around:{radio},{lat},{lng});
    );
    out center tags;
    """
  for url in OVERPASS_SERVERS:
    try:
      resp = requests.post(
          url, data={"data": query}, headers=HEADERS, timeout=30
      )
      if resp.status_code == 200:
        return resp.json().get("elements", [])
    except Exception:
      continue
  return []


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
  for zona, lat_c, lng_c, radio in ZONAS_ESPANA:
    print(f"Buscando en {zona}...")
    elementos = consultar_zona(lat_c, lng_c, radio)
    for el in elementos:
      tags = el.get("tags", {})
      nombre = tags.get("name")
      if not nombre:
        continue

      lat = el.get("lat") or el.get("center", {}).get("lat")
      lng = el.get("lon") or el.get("center", {}).get("lon")
      if not lat or not lng:
        continue

      clave = (
          f"{nombre.lower().strip()}_{round(float(lat), 3)}_{round(float(lng), 3)}"
      )
      if clave in vistos:
        continue
      vistos.add(clave)

      calle = tags.get("addr:street", "")
      numero = tags.get("addr:housenumber", "")
      ciudad = tags.get("addr:city") or tags.get("addr:town") or zona
      cp = tags.get("addr:postcode", "")
      direccion = ", ".join(
          filter(None, [f"{calle} {numero}".strip(), cp, ciudad])
      )

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
          "region": detectar_region(zona, ciudad),
          "direccion": direccion if direccion else "Ver ubicación en mapa",
          "lat": float(lat),
          "lng": float(lng),
          "web": web,
          "telefono": tags.get("phone") or tags.get("contact:phone") or "",
          "fuente": "OpenStreetMap",
      })
      nuevas += 1
    time.sleep(1)  # Pausa corta para no saturar el servidor

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
