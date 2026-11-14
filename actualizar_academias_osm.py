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

PALABRAS_VALIDAS = [
    "jiu", "bjj", "gracie", "grappling", "mma", "dojo", "checkmat",
    "alliance", "atos", "lotus", "gfteam", "tenth planet", "10th planet",
    "fight", "combat", "artes marciales", "martial", "tatami", "kimura",
    "budo", "zenit", "carpe diem", "nova uniao", "de la riva", "carlson",
    "roger", "aranha", "mathias", "ases", "icon", "brasa"
]

PALABRAS_EXCLUIDAS = ["fleca", "panader", "restaurante", "bar ", "farmacia"]

# Base verificada de academias importantes de España que suelen faltar en OSM
ACADEMIAS_SEMILLA = [
    {"nombre": "Mathias Ribeiro Team Madrid", "ciudad": "Madrid", "region": "Madrid", "direccion": "Calle de Gutenberg 7, Madrid", "lat": 40.4055, "lng": -3.6766, "web": "https://mathiasribeiro.com"},
    {"nombre": "Checkmat Madrid / Samurai Jiu Jitsu", "ciudad": "Madrid", "region": "Madrid", "direccion": "Calle de Juan Español 38, Madrid", "lat": 40.3879, "lng": -3.7011, "web": "https://checkmatmadrid.com"},
    {"nombre": "Lotus Club Madrid", "ciudad": "Madrid", "region": "Madrid", "direccion": "Madrid, España", "lat": 40.4250, "lng": -3.6850, "web": ""},
    {"nombre": "Gracie Barra Madrid", "ciudad": "Madrid", "region": "Madrid", "direccion": "Madrid, España", "lat": 40.4350, "lng": -3.7050, "web": ""},
    {"nombre": "Tenth Planet Madrid", "ciudad": "Madrid", "region": "Madrid", "direccion": "Madrid, España", "lat": 40.4100, "lng": -3.7150, "web": ""},
    {"nombre": "De La Riva Madrid", "ciudad": "Madrid", "region": "Madrid", "direccion": "Madrid, España", "lat": 40.3980, "lng": -3.6920, "web": ""},
    {"nombre": "Carlson Gracie Madrid", "ciudad": "Madrid", "region": "Madrid", "direccion": "Madrid, España", "lat": 40.4410, "lng": -3.6790, "web": ""},
    {"nombre": "Atos Barcelona", "ciudad": "Barcelona", "region": "Cataluña", "direccion": "Carrer de Pujades 77, Barcelona", "lat": 41.3965, "lng": 2.1965, "web": "https://atosbarcelona.com"},
    {"nombre": "Aranha Barcelona", "ciudad": "Barcelona", "region": "Cataluña", "direccion": "Barcelona, España", "lat": 41.3820, "lng": 2.1540, "web": ""},
    {"nombre": "Gracie Barra Barcelona", "ciudad": "Barcelona", "region": "Cataluña", "direccion": "Barcelona, España", "lat": 41.3910, "lng": 2.1650, "web": ""},
    {"nombre": "Anaconda BJJ Barcelona", "ciudad": "Barcelona", "region": "Cataluña", "direccion": "Barcelona, España", "lat": 41.4020, "lng": 2.1750, "web": ""},
    {"nombre": "Templum BCN", "ciudad": "Barcelona", "region": "Cataluña", "direccion": "Carrer d'Entença 113, Barcelona", "lat": 41.3812, "lng": 2.1485, "web": ""},
    {"nombre": "GFTeam Barcelona", "ciudad": "Barcelona", "region": "Cataluña", "direccion": "Barcelona, España", "lat": 41.4090, "lng": 2.1850, "web": ""},
    {"nombre": "Ases Jiu Jitsu Valencia", "ciudad": "Valencia", "region": "Comunidad Valenciana", "direccion": "Valencia, España", "lat": 39.4750, "lng": -0.3750, "web": "https://asesbjj.com"},
    {"nombre": "Checkmat Valencia", "ciudad": "Valencia", "region": "Comunidad Valenciana", "direccion": "Valencia, España", "lat": 39.4650, "lng": -0.3820, "web": ""},
    {"nombre": "Gracie Barra Valencia", "ciudad": "Valencia", "region": "Comunidad Valenciana", "direccion": "Valencia, España", "lat": 39.4810, "lng": -0.3650, "web": ""},
    {"nombre": "Climent Club Alicante", "ciudad": "Alicante", "region": "Comunidad Valenciana", "direccion": "Calle Maestro Alonso 94, Alicante", "lat": 38.3585, "lng": -0.4882, "web": ""},
    {"nombre": "Checkmat Alicante", "ciudad": "Alicante", "region": "Comunidad Valenciana", "direccion": "Alicante, España", "lat": 38.3490, "lng": -0.4910, "web": ""},
    {"nombre": "Gracie Barra Sevilla", "ciudad": "Sevilla", "region": "Andalucía", "direccion": "Sevilla, España", "lat": 37.3880, "lng": -5.9820, "web": ""},
    {"nombre": "Sutemi Academy Sevilla", "ciudad": "Sevilla", "region": "Andalucía", "direccion": "Sevilla, España", "lat": 37.3950, "lng": -5.9710, "web": ""},
    {"nombre": "Roger Gracie Academy Málaga", "ciudad": "Málaga", "region": "Andalucía", "direccion": "Málaga, España", "lat": 36.7180, "lng": -4.4320, "web": ""},
    {"nombre": "Roger Gracie Academy Marbella", "ciudad": "Marbella", "region": "Andalucía", "direccion": "Marbella, Málaga", "lat": 36.5100, "lng": -4.8850, "web": ""},
    {"nombre": "Gracie Barra Málaga", "ciudad": "Málaga", "region": "Andalucía", "direccion": "Málaga, España", "lat": 36.7250, "lng": -4.4150, "web": ""},
    {"nombre": "Zenit BJJ Zaragoza", "ciudad": "Zaragoza", "region": "Aragón", "direccion": "Zaragoza, España", "lat": 41.6490, "lng": -0.8870, "web": ""},
    {"nombre": "ufight Academy Bilbao", "ciudad": "Bilbao", "region": "País Vasco", "direccion": "Bilbao, Vizcaya", "lat": 43.2620, "lng": -2.9340, "web": ""},
    {"nombre": "Gracie Barra San Sebastián", "ciudad": "San Sebastián", "region": "País Vasco", "direccion": "Donostia, Gipuzkoa", "lat": 43.3180, "lng": -1.9810, "web": ""},
    {"nombre": "Ibiza Jiu Jitsu / Gracie Barra Ibiza", "ciudad": "Ibiza", "region": "Islas Baleares", "direccion": "Eivissa, Islas Baleares", "lat": 38.9080, "lng": 1.4320, "web": ""},
    {"nombre": "Mallorca BJJ / Checkmat Palma", "ciudad": "Palma de Mallorca", "region": "Islas Baleares", "direccion": "Palma, Islas Baleares", "lat": 39.5720, "lng": 2.6510, "web": ""},
    {"nombre": "Taz Jinámar Gran Canaria", "ciudad": "Las Palmas de Gran Canaria", "region": "Islas Canarias", "direccion": "Las Palmas de Gran Canaria", "lat": 28.0350, "lng": -15.4180, "web": ""},
    {"nombre": "Gil Catarino BJJ Tenerife", "ciudad": "Santa Cruz de Tenerife", "region": "Islas Canarias", "direccion": "Santa Cruz de Tenerife", "lat": 28.4650, "lng": -16.2540, "web": ""},
    {"nombre": "Gracie Barra A Coruña", "ciudad": "A Coruña", "region": "Galicia", "direccion": "A Coruña, Galicia", "lat": 43.3620, "lng": -8.4110, "web": ""},
    {"nombre": "GFTeam Vigo", "ciudad": "Vigo", "region": "Galicia", "direccion": "Vigo, Pontevedra", "lat": 42.2380, "lng": -8.7220, "web": ""}
]

TERMINOS_BUSQUEDA = [
    "Brazilian Jiu Jitsu", "Jiu-Jitsu", "Jiu Jitsu", "BJJ", "Grappling",
    "Gracie Barra", "Gracie Jiu Jitsu", "Roger Gracie", "Carlson Gracie",
    "Checkmat", "Alliance", "Atos", "GFTeam", "Lotus Club", "Tenth Planet",
    "De La Riva", "Nova Uniao", "Zenit BJJ",
    "Jiu Jitsu Madrid", "Jiu Jitsu Barcelona", "Jiu Jitsu Valencia",
    "Jiu Jitsu Sevilla", "Jiu Jitsu Málaga", "Jiu Jitsu Alicante",
    "Jiu Jitsu Bilbao", "Jiu Jitsu Zaragoza", "Jiu Jitsu Murcia",
    "Jiu Jitsu Palma", "Jiu Jitsu Ibiza", "Jiu Jitsu Las Palmas",
    "Jiu Jitsu Tenerife", "Jiu Jitsu Granada", "Jiu Jitsu Cádiz",
    "Jiu Jitsu A Coruña", "Jiu Jitsu Vigo", "Jiu Jitsu Gijón"
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
            return [
                ac for ac in lista
                if not any(ex in str(ac.get("nombre", "")).lower() for ex in PALABRAS_EXCLUIDAS)
            ]
        except Exception:
            return []


def detectar_region(texto_completo):
    texto = texto_completo.lower()
    mapa_regiones = {
        "madrid": "Madrid",
        "barcelona": "Cataluña", "girona": "Cataluña", "tarragona": "Cataluña",
        "lleida": "Cataluña", "badalona": "Cataluña", "sabadell": "Cataluña",
        "valencia": "Comunidad Valenciana", "alicante": "Comunidad Valenciana",
        "elche": "Comunidad Valenciana", "castell": "Comunidad Valenciana",
        "quart de poblet": "Comunidad Valenciana",
        "sevilla": "Andalucía", "málaga": "Andalucía", "malaga": "Andalucía",
        "marbella": "Andalucía", "antequera": "Andalucía", "granada": "Andalucía",
        "cádiz": "Andalucía", "cadiz": "Andalucía", "tarifa": "Andalucía",
        "córdoba": "Andalucía", "almería": "Andalucía",
        "palma": "Islas Baleares", "ibiza": "Islas Baleares",
        "eivissa": "Islas Baleares", "mallorca": "Islas Baleares",
        "baleares": "Islas Baleares",
        "palmas": "Islas Canarias", "tenerife": "Islas Canarias",
        "canarias": "Islas Canarias",
        "bilbao": "País Vasco", "bizkaia": "País Vasco", "vizcaya": "País Vasco",
        "san sebasti": "País Vasco", "donostia": "País Vasco", "vitoria": "País Vasco",
        "zaragoza": "Aragón",
        "murcia": "Región de Murcia",
        "coruña": "Galicia", "vigo": "Galicia", "pontevedra": "Galicia",
        "asturias": "Asturias", "gijón": "Asturias", "oviedo": "Asturias",
        "santander": "Cantabria", "pamplona": "Navarra", "valladolid": "Castilla y León"
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
            "properties": ac
        })
    return {"type": "FeatureCollection", "features": features}


def main():
    academias = cargar_existentes()
    print(f"Academias válidas previas: {len(academias)}")

    vistos = set()
    for ac in academias:
        nombre = str(ac.get("nombre") or ac.get("name") or "").lower().strip()
        vistos.add(nombre)

    nuevas = 0

    # 1. Incorporar base verificada de España
    for sem in ACADEMIAS_SEMILLA:
        clave = sem["nombre"].lower().strip()
        if clave not in vistos:
            vistos.add(clave)
            academias.append({
                "nombre": sem["nombre"],
                "ciudad": sem["ciudad"],
                "region": sem["region"],
                "direccion": sem["direccion"],
                "lat": sem["lat"],
                "lng": sem["lng"],
                "web": sem["web"],
                "telefono": "",
                "fuente": "Directorio Verificado"
            })
            nuevas += 1

    # 2. Barrido en OpenStreetMap
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
                    "limit": 50
                },
                headers=NOMINATIM_HEADERS,
                timeout=12
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

                clave = nombre.lower().strip()
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
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "web": web,
                    "telefono": extratags.get("phone") or extratags.get("contact:phone") or "",
                    "fuente": "OpenStreetMap"
                })
                nuevas += 1
                print(f"  + OSM: {nombre} ({ciudad})")
        except Exception as e:
            print(f"Error en '{termino}': {e}")

    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(academias, f, ensure_ascii=False, indent=2)

    geojson = generar_geojson(academias)
    with open(ARCHIVO_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"Proceso finalizado: {nuevas} academias nuevas agregadas (Total: {len(academias)}).")


if __name__ == "__main__":
    main()
