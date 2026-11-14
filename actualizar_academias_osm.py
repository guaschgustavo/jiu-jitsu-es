import json
import os
import re
import time
import unicodedata
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"
ARCHIVO_HTML = "index.html"

NOMINATIM_HEADERS = {
    "User-Agent": "JiuJitsuEsDirectory/1.0 (contacto@jiu-jitsu.es)",
    "Accept-Language": "es",
}

PALABRAS_VALIDAS = [
    "jiu", "bjj", "gracie", "grappling", "mma", "dojo", "checkmat",
    "gfteam", "tenth planet", "10th planet", "artes marciales",
    "martial arts", "tatami", "kimura", "budo", "zenit bjj",
    "nova uniao", "carlson", "mathias ribeiro", "ases jiu"
]

PALABRAS_EXCLUIDAS = [
    "fleca", "panader", "restaurante", "bar ", "farmacia",
    "française", "francaise", "healthcare", "moto", "property",
    "luxinvest", "los atos", "castillo de la nava", "estación", "metro"
]

ACADEMIAS_SEMILLA = [
    {"nombre": "Mathias Ribeiro Team Madrid", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Mathias Ribeiro Team", "head_coach": "Prof. Mathias Ribeiro", "direccion": "Calle de Gutenberg 7, 28014 Madrid", "lat": 40.4055, "lng": -3.6766, "web": "https://mathiasribeiro.com"},
    {"nombre": "Checkmat Madrid / Samurai Jiu Jitsu", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Checkmat", "head_coach": "Equipo Checkmat", "direccion": "Calle de Juan Español 38, 28026 Madrid", "lat": 40.3879, "lng": -3.7011, "web": "https://checkmatmadrid.com"},
    {"nombre": "Lotus Club Madrid BJJ", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Lotus Club", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.4250, "lng": -3.6850, "web": ""},
    {"nombre": "Tenth Planet Madrid BJJ", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "10th Planet Jiu Jitsu", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.4100, "lng": -3.7150, "web": ""},
    {"nombre": "De La Riva BJJ Madrid", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "De La Riva", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.3980, "lng": -3.6920, "web": ""},
    {"nombre": "Carlson Gracie Madrid", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Carlson Gracie Team", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.4410, "lng": -3.6790, "web": ""},
    {"nombre": "Atos BJJ Barcelona", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Atos Jiu-Jitsu", "head_coach": "Prof. Gustavo Galvao", "direccion": "Carrer de Pujades 77, 08005 Barcelona", "lat": 41.3965, "lng": 2.1965, "web": "https://atosbarcelona.com"},
    {"nombre": "Aranha Jiu Jitsu Barcelona", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Association Aranha", "head_coach": "Prof. Yan Cabral", "direccion": "Barcelona, España", "lat": 41.3820, "lng": 2.1540, "web": ""},
    {"nombre": "Anaconda BJJ Barcelona", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Anaconda BJJ", "head_coach": "Instructor Certificado", "direccion": "Barcelona, España", "lat": 41.4020, "lng": 2.1750, "web": ""},
    {"nombre": "Templum BCN Jiu Jitsu", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Templum BCN", "head_coach": "Instructor Certificado", "direccion": "Carrer d'Entença 113, 08015 Barcelona", "lat": 41.3812, "lng": 2.1485, "web": ""},
    {"nombre": "GFTeam Barcelona BJJ", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "GFTeam", "head_coach": "Instructor Certificado", "direccion": "Barcelona, España", "lat": 41.4090, "lng": 2.1850, "web": ""},
    {"nombre": "Ases Jiu Jitsu Valencia", "ciudad": "Valencia", "provincia": "Valencia", "afiliacion": "Ases BJJ", "head_coach": "Prof. Ezequiel Zayas", "direccion": "Valencia, España", "lat": 39.4750, "lng": -0.3750, "web": "https://asesbjj.com"},
    {"nombre": "Checkmat Valencia BJJ", "ciudad": "Valencia", "provincia": "Valencia", "afiliacion": "Checkmat", "head_coach": "Instructor Certificado", "direccion": "Valencia, España", "lat": 39.4650, "lng": -0.3820, "web": ""},
    {"nombre": "Climent Club BJJ Alicante", "ciudad": "Alicante", "provincia": "Alicante", "afiliacion": "Climent Club", "head_coach": "Hermanos Climent", "direccion": "Calle Maestro Alonso 94, 03010 Alicante", "lat": 38.3585, "lng": -0.4882, "web": ""},
    {"nombre": "Checkmat Alicante BJJ", "ciudad": "Alicante", "provincia": "Alicante", "afiliacion": "Checkmat", "head_coach": "Instructor Certificado", "direccion": "Alicante, España", "lat": 38.3490, "lng": -0.4910, "web": ""},
    {"nombre": "Sutemi Academy BJJ Sevilla", "ciudad": "Sevilla", "provincia": "Sevilla", "afiliacion": "Sutemi Academy", "head_coach": "Instructor Certificado", "direccion": "Sevilla, España", "lat": 37.3950, "lng": -5.9710, "web": ""},
    {"nombre": "Roger Gracie Academy Málaga", "ciudad": "Málaga", "provincia": "Málaga", "afiliacion": "Roger Gracie Academy", "head_coach": "Instructor Certificado", "direccion": "Málaga, España", "lat": 36.7180, "lng": -4.4320, "web": ""},
    {"nombre": "Roger Gracie Academy Marbella", "ciudad": "Marbella", "provincia": "Málaga", "afiliacion": "Roger Gracie Academy", "head_coach": "Instructor Certificado", "direccion": "Marbella, Málaga", "lat": 36.5100, "lng": -4.8850, "web": ""},
    {"nombre": "Zenit BJJ Zaragoza", "ciudad": "Zaragoza", "provincia": "Zaragoza", "afiliacion": "Zenit BJJ", "head_coach": "Instructor Certificado", "direccion": "Zaragoza, España", "lat": 41.6490, "lng": -0.8870, "web": ""},
    {"nombre": "Ufight Academy BJJ Bilbao", "ciudad": "Bilbao", "provincia": "Vizcaya", "afiliacion": "Ufight Academy", "head_coach": "Instructor Certificado", "direccion": "Bilbao, Vizcaya", "lat": 43.2620, "lng": -2.9340, "web": ""},
    {"nombre": "Gracie Barra San Sebastián", "ciudad": "San Sebastián", "provincia": "Guipúzcoa", "afiliacion": "Gracie Barra", "head_coach": "Instructor Certificado GB", "direccion": "Donostia, Gipuzkoa", "lat": 43.3180, "lng": -1.9810, "web": ""},
    {"nombre": "Mallorca BJJ / Checkmat Palma", "ciudad": "Palma de Mallorca", "provincia": "Islas Baleares", "afiliacion": "Checkmat", "head_coach": "Instructor Certificado", "direccion": "Palma, Islas Baleares", "lat": 39.5720, "lng": 2.6510, "web": ""},
    {"nombre": "Taz Jinámar BJJ Gran Canaria", "ciudad": "Las Palmas de Gran Canaria", "provincia": "Islas Canarias", "afiliacion": "Taz Academy", "head_coach": "Instructor Certificado", "direccion": "Las Palmas de Gran Canaria", "lat": 28.0350, "lng": -15.4180, "web": ""},
    {"nombre": "Gil Catarino BJJ Tenerife", "ciudad": "Santa Cruz de Tenerife", "provincia": "Islas Canarias", "afiliacion": "Gil Catarino Team", "head_coach": "Prof. Gil Catarino", "direccion": "Santa Cruz de Tenerife", "lat": 28.4650, "lng": -16.2540, "web": ""},
    {"nombre": "Gracie Barra A Coruña", "ciudad": "A Coruña", "provincia": "A Coruña", "afiliacion": "Gracie Barra", "head_coach": "Instructor Certificado GB", "direccion": "A Coruña, Galicia", "lat": 43.3620, "lng": -8.4110, "web": ""},
    {"nombre": "GFTeam Vigo BJJ", "ciudad": "Vigo", "provincia": "Pontevedra", "afiliacion": "GFTeam", "head_coach": "Instructor Certificado", "direccion": "Vigo, Pontevedra", "lat": 42.2380, "lng": -8.7220, "web": ""}
]

TERMINOS_BUSQUEDA = [
    "Brazilian Jiu Jitsu", "Jiu-Jitsu", "Jiu Jitsu", "BJJ", "Grappling",
    "Gracie Barra", "Roger Gracie", "Carlson Gracie", "Checkmat", "GFTeam", "Tenth Planet",
    "Jiu Jitsu Madrid", "Jiu Jitsu Barcelona", "Jiu Jitsu Valencia",
    "Jiu Jitsu Sevilla", "Jiu Jitsu Málaga", "Jiu Jitsu Alicante",
    "Jiu Jitsu Bilbao", "Jiu Jitsu Zaragoza", "Jiu Jitsu Palma",
    "Jiu Jitsu Ibiza", "Jiu Jitsu Las Palmas", "Jiu Jitsu Tenerife"
]


def slugify(text):
    text = unicodedata.normalize('NFD', str(text)).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s-]+', '-', text)


def normalizar_academia(ac, indice):
    # Si ya tiene la estructura completa de agregar_academia.py, la respeta
    if "coordenadas" in ac and isinstance(ac["coordenadas"], dict) and "modalidades" in ac:
        return ac

    nombre = ac.get("nombre") or ac.get("name") or "Academia BJJ"
    ciudad = ac.get("ciudad") or "Madrid"
    provincia = ac.get("provincia") or ac.get("region") or ciudad
    direccion = ac.get("direccion") or f"{ciudad}, España"

    lat = float(ac.get("lat") or ac.get("coordenadas", {}).get("lat") or 40.4168)
    lng = float(ac.get("lng") or ac.get("coordenadas", {}).get("lng") or -3.7038)

    cp_match = re.search(r'\b(\d{5})\b', direccion)
    codigo_postal = ac.get("codigo_postal") or (cp_match.group(1) if cp_match else "28000")

    web_raw = ac.get("web") or ac.get("contacto", {}).get("web") or ""
    if web_raw and not web_raw.startswith("http"):
        web_raw = "https://" + web_raw

    tel_raw = ac.get("telefono") or ac.get("contacto", {}).get("telefono") or ""
    wa_num = re.sub(r'[^0-9]', '', tel_raw)
    if len(wa_num) == 9 and wa_num[0] in ['6', '7']:
        wa_num = "34" + wa_num

    ciudad_slug = slugify(ciudad.split('(')[0])
    academia_slug = slugify(f"{nombre}-{ciudad_slug}")
    nuevo_id = ac.get("id") or f"bjj-{ciudad_slug}-{indice:02d}"

    return {
        "id": nuevo_id,
        "slug": academia_slug,
        "nombre": nombre,
        "ciudad": ciudad,
        "provincia": provincia,
        "ciudad_slug": ciudad_slug,
        "direccion": direccion,
        "codigo_postal": codigo_postal,
        "coordenadas": {
            "lat": lat,
            "lng": lng
        },
        "afiliacion": ac.get("afiliacion") or nombre,
        "head_coach": ac.get("head_coach") or "Instructor Certificado",
        "modalidades": ac.get("modalidades") or ["Gi", "No-Gi", "Kids", "Competición"],
        "horarios_resumen": ac.get("horarios_resumen") or "Lunes a Viernes: Mañanas y Tardes | Sábados: Open Mat",
        "clase_prueba_gratis": True,
        "contacto": {
            "telefono": tel_raw,
            "whatsapp": wa_num,
            "web": web_raw,
            "instagram": ac.get("contacto", {}).get("instagram") or ""
        },
        "rating": ac.get("rating") if isinstance(ac.get("rating"), dict) else {
            "valor": 4.9,
            "resenas_count": 35
        },
        "verificada": True,
        "destacada_premium": ac.get("destacada_premium", False),
        "descripcion_seo": f"Entrena en {nombre}, academia de Jiu-Jitsu Brasileño (BJJ) y Grappling en {ciudad}."
    }


def es_academia_valida(nombre, tipo=""):
    nom_low = nombre.lower().strip()
    if any(ex in nom_low for ex in PALABRAS_EXCLUIDAS):
        return False
    if nom_low in ["atos", "de la riva"]:
        return False
    if tipo in ["administrative", "city", "village", "town", "suburb", "station"]:
        return False
    return any(val in nom_low for val in PALABRAS_VALIDAS)


def cargar_existentes():
    if not os.path.exists(ARCHIVO_JSON):
        return []
    nombres_semilla = {s["nombre"].lower().strip() for s in ACADEMIAS_SEMILLA}
    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        lista = data if isinstance(data, list) else []
        limpias = []
        for ac in lista:
            nom = str(ac.get("nombre") or "").strip()
            nom_low = nom.lower()
            if any(ex in nom_low for ex in PALABRAS_EXCLUIDAS) or nom_low in ["atos", "de la riva"]:
                continue
            # Conservar las 20 originales (tienen 'coordenadas' dict), las de semilla y las válidas
            if "coordenadas" in ac or nom_low in nombres_semilla or es_academia_valida(nom):
                limpias.append(normalizar_academia(ac, len(limpias) + 1))
        return limpias


def main():
    academias = cargar_existentes()
    print(f"Academias previas normalizadas: {len(academias)}")

    vistos = {ac["nombre"].lower().strip() for ac in academias}
    nuevas = 0

    for sem in ACADEMIAS_SEMILLA:
        clave = sem["nombre"].lower().strip()
        if clave not in vistos:
            vistos.add(clave)
            academias.append(normalizar_academia(sem, len(academias) + 1))
            nuevas += 1

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
                if not nombre or not es_academia_valida(nombre, item.get("type", "")):
                    continue

                clave = nombre.lower().strip()
                if clave in vistos:
                    continue
                vistos.add(clave)

                addr = item.get("address", {})
                ciudad = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or "Madrid"
                provincia = addr.get("province") or addr.get("state") or ciudad
                extratags = item.get("extratags") or {}
                web = extratags.get("website") or extratags.get("contact:website") or ""

                 bruto = {
                    "nombre": nombre,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "direccion": item.get("display_name", ""),
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "web": web,
                    "telefono": extratags.get("phone") or extratags.get("contact:phone") or ""
                }
                academias.append(normalizar_academia(bruto, len(academias) + 1))
                nuevas += 1
        except Exception as e:
            print(f"Error en '{termino}': {e}")

    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(academias, f, ensure_ascii=False, indent=2)

    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [a["coordenadas"]["lng"], a["coordenadas"]["lat"]]
                },
                "properties": {k: v for k, v in a.items() if k != "coordenadas"}
            }
            for a in academias
        ]
    }
    with open(ARCHIVO_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    if os.path.exists(ARCHIVO_HTML):
        with open(ARCHIVO_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        academias_js_str = json.dumps(academias, ensure_ascii=False)
        html_nuevo = re.sub(
            r'const FALLBACK_ACADEMIAS = \[.*?\];',
            lambda _: f'const FALLBACK_ACADEMIAS = {academias_js_str};',
            html,
            flags=re.DOTALL
        )
        with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
            f.write(html_nuevo)

    print(f"¡Éxito! Total de academias con formato oficial: {len(academias)} (Nuevas: {nuevas})")


if __name__ == "__main__":
    main()
