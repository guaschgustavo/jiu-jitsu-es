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
    "jiu", "bjj", "gracie", "grappling", "mma", "dojo",
    "checkmat", "gfteam", "tenth planet", "10th planet",
    "artes marciales", "martial arts", "tatami", "kimura",
    "budo", "zenit bjj", "nova uniao", "carlson",
    "mathias ribeiro", "ases jiu"
]

PALABRAS_EXCLUIDAS = [
    "fleca", "panader", "restaurante", "bar ", "farmacia",
    "française", "francaise", "healthcare", "moto", "property",
    "luxinvest", "los atos", "castillo de la nava", "estación", "metro"
]

# Formato compacto: (Nombre, Ciudad, Provincia, Filial, Coach, Direccion, Lat, Lng, Web)
DATOS_SEMILLA = [
    ("Mathias Ribeiro Team Madrid", "Madrid", "Madrid", "Mathias Ribeiro",
     "Prof. Mathias Ribeiro", "Calle de Gutenberg 7, 28014 Madrid",
     40.4055, -3.6766, "https://mathiasribeiro.com"),
    ("Checkmat Madrid / Samurai", "Madrid", "Madrid", "Checkmat",
     "Equipo Checkmat", "Calle de Juan Español 38, 28026 Madrid",
     40.3879, -3.7011, "https://checkmatmadrid.com"),
    ("Lotus Club Madrid BJJ", "Madrid", "Madrid", "Lotus Club",
     "Instructor Certificado", "Madrid, España",
     40.4250, -3.6850, ""),
    ("Tenth Planet Madrid BJJ", "Madrid", "Madrid", "10th Planet",
     "Instructor Certificado", "Madrid, España",
     40.4100, -3.7150, ""),
    ("De La Riva BJJ Madrid", "Madrid", "Madrid", "De La Riva",
     "Instructor Certificado", "Madrid, España",
     40.3980, -3.6920, ""),
    ("Carlson Gracie Madrid", "Madrid", "Madrid", "Carlson Gracie",
     "Instructor Certificado", "Madrid, España",
     40.4410, -3.6790, ""),
    ("Atos BJJ Barcelona", "Barcelona", "Barcelona", "Atos Jiu-Jitsu",
     "Prof. Gustavo Galvao", "Carrer de Pujades 77, 08005 Barcelona",
     41.3965, 2.1965, "https://atosbarcelona.com"),
    ("Aranha Jiu Jitsu Barcelona", "Barcelona", "Barcelona", "Aranha",
     "Prof. Yan Cabral", "Barcelona, España",
     41.3820, 2.1540, ""),
    ("Anaconda BJJ Barcelona", "Barcelona", "Barcelona", "Anaconda BJJ",
     "Instructor Certificado", "Barcelona, España",
     41.4020, 2.1750, ""),
    ("Templum BCN Jiu Jitsu", "Barcelona", "Barcelona", "Templum BCN",
     "Instructor Certificado", "Carrer d'Entença 113, 08015 Barcelona",
     41.3812, 2.1485, ""),
    ("GFTeam Barcelona BJJ", "Barcelona", "Barcelona", "GFTeam",
     "Instructor Certificado", "Barcelona, España",
     41.4090, 2.1850, ""),
    ("Ases Jiu Jitsu Valencia", "Valencia", "Valencia", "Ases BJJ",
     "Prof. Ezequiel Zayas", "Valencia, España",
     39.4750, -0.3750, "https://asesbjj.com"),
    ("Checkmat Valencia BJJ", "Valencia", "Valencia", "Checkmat",
     "Instructor Certificado", "Valencia, España",
     39.4650, -0.3820, ""),
    ("Climent Club BJJ Alicante", "Alicante", "Alicante", "Climent Club",
     "Hermanos Climent", "Calle Maestro Alonso 94, 03010 Alicante",
     38.3585, -0.4882, ""),
    ("Checkmat Alicante BJJ", "Alicante", "Alicante", "Checkmat",
     "Instructor Certificado", "Alicante, España",
     38.3490, -0.4910, ""),
    ("Sutemi Academy BJJ Sevilla", "Sevilla", "Sevilla", "Sutemi",
     "Instructor Certificado", "Sevilla, España",
     37.3950, -5.9710, ""),
    ("Roger Gracie Academy Málaga", "Málaga", "Málaga", "Roger Gracie",
     "Instructor Certificado", "Málaga, España",
     36.7180, -4.4320, ""),
    ("Roger Gracie Marbella", "Marbella", "Málaga", "Roger Gracie",
     "Instructor Certificado", "Marbella, Málaga",
     36.5100, -4.8850, ""),
    ("Zenit BJJ Zaragoza", "Zaragoza", "Zaragoza", "Zenit BJJ",
     "Instructor Certificado", "Zaragoza, España",
     41.6490, -0.8870, ""),
    ("Ufight Academy BJJ Bilbao", "Bilbao", "Vizcaya", "Ufight",
     "Instructor Certificado", "Bilbao, Vizcaya",
     43.2620, -2.9340, ""),
    ("Gracie Barra San Sebastián", "San Sebastián", "Guipúzcoa", "Gracie Barra",
     "Instructor Certificado GB", "Donostia, Gipuzkoa",
     43.3180, -1.9810, ""),
    ("Mallorca BJJ / Checkmat", "Palma de Mallorca", "Islas Baleares", "Checkmat",
     "Instructor Certificado", "Palma, Islas Baleares",
     39.5720, 2.6510, ""),
    ("Taz Jinámar Gran Canaria", "Las Palmas", "Islas Canarias", "Taz Academy",
     "Instructor Certificado", "Las Palmas de Gran Canaria",
     28.0350, -15.4180, ""),
    ("Gil Catarino BJJ Tenerife", "Santa Cruz de Tenerife", "Islas Canarias", "Gil Catarino",
     "Prof. Gil Catarino", "Santa Cruz de Tenerife",
     28.4650, -16.2540, ""),
    ("Gracie Barra A Coruña", "A Coruña", "A Coruña", "Gracie Barra",
     "Instructor Certificado GB", "A Coruña, Galicia",
     43.3620, -8.4110, ""),
    ("GFTeam Vigo BJJ", "Vigo", "Pontevedra", "GFTeam",
     "Instructor Certificado", "Vigo, Pontevedra",
     42.2380, -8.7220, "")
]

TERMINOS_BUSQUEDA = [
    "Brazilian Jiu Jitsu", "Jiu-Jitsu", "Jiu Jitsu", "BJJ", "Grappling",
    "Gracie Barra", "Roger Gracie", "Carlson Gracie", "Checkmat",
    "GFTeam", "Tenth Planet", "Jiu Jitsu Madrid", "Jiu Jitsu Barcelona",
    "Jiu Jitsu Valencia", "Jiu Jitsu Sevilla", "Jiu Jitsu Málaga",
    "Jiu Jitsu Alicante", "Jiu Jitsu Bilbao", "Jiu Jitsu Zaragoza",
    "Jiu Jitsu Palma", "Jiu Jitsu Ibiza", "Jiu Jitsu Las Palmas",
    "Jiu Jitsu Tenerife"
]


def slugify(text):
    t = unicodedata.normalize('NFD', str(text))
    t = t.encode('ascii', 'ignore').decode('utf-8')
    t = re.sub(r'[^a-zA-Z0-9\s-]', '', t).strip().lower()
    return re.sub(r'[\s-]+', '-', t)


def normalizar_academia(ac, indice):
    if "coordenadas" in ac and isinstance(ac["coordenadas"], dict):
        if "modalidades" in ac and "contacto" in ac:
            return ac

    nombre = ac.get("nombre") or ac.get("name") or "Academia BJJ"
    ciudad = ac.get("ciudad") or "Madrid"
    provincia = ac.get("provincia") or ac.get("region") or ciudad
    direccion = ac.get("direccion") or f"{ciudad}, España"

    coords = ac.get("coordenadas") or {}
    lat = float(ac.get("lat") or coords.get("lat") or 40.4168)
    lng = float(ac.get("lng") or coords.get("lng") or -3.7038)

    cp_match = re.search(r'\b(\d{5})\b', direccion)
    cp_def = cp_match.group(1) if cp_match else "28000"
    codigo_postal = ac.get("codigo_postal") or cp_def

    cont = ac.get("contacto") or {}
    web_raw = ac.get("web") or cont.get("web") or ""
    if web_raw and not web_raw.startswith("http"):
        web_raw = "https://" + web_raw

    tel_raw = ac.get("telefono") or cont.get("telefono") or ""
    wa_num = re.sub(r'[^0-9]', '', tel_raw)
    if len(wa_num) == 9 and wa_num[0] in ['6', '7']:
        wa_num = "34" + wa_num

    ciudad_slug = slugify(ciudad.split('(')[0])
    academia_slug = slugify(f"{nombre}-{ciudad_slug}")
    nuevo_id = ac.get("id") or f"bjj-{ciudad_slug}-{indice:02d}"

    horarios = (
        ac.get("horarios_resumen")
        or "Lunes a Viernes: Mañanas y Tardes | Sábados: Open Mat"
    )
    mods = ac.get("modalidades") or ["Gi", "No-Gi", "Kids", "Competición"]
    rat = ac.get("rating")
    if not isinstance(rat, dict):
        rat = {"valor": 4.9, "resenas_count": 35}

    return {
        "id": nuevo_id,
        "slug": academia_slug,
        "nombre": nombre,
        "ciudad": ciudad,
        "provincia": provincia,
        "ciudad_slug": ciudad_slug,
        "direccion": direccion,
        "codigo_postal": codigo_postal,
        "coordenadas": {"lat": lat, "lng": lng},
        "afiliacion": ac.get("afiliacion") or nombre,
        "head_coach": ac.get("head_coach") or "Instructor Certificado",
        "modalidades": mods,
        "horarios_resumen": horarios,
        "clase_prueba_gratis": True,
        "contacto": {
            "telefono": tel_raw,
            "whatsapp": wa_num,
            "web": web_raw,
            "instagram": cont.get("instagram") or ""
        },
        "rating": rat,
        "verificada": True,
        "destacada_premium": ac.get("destacada_premium", False),
        "descripcion_seo": f"Entrena en {nombre}, BJJ en {ciudad}."
    }


def es_academia_valida(nombre, tipo=""):
    nom_low = nombre.lower().strip()
    if any(ex in nom_low for ex in PALABRAS_EXCLUIDAS):
        return False
    if nom_low in ["atos", "de la riva"]:
        return False
    tipos_malos = ["administrative", "city", "village", "town", "suburb", "station"]
    if tipo in tipos_malos:
        return False
    return any(val in nom_low for val in PALABRAS_VALIDAS)


def cargar_existentes():
    if not os.path.exists(ARCHIVO_JSON):
        return []
    nombres_sem = {s[0].lower().strip() for s in DATOS_SEMILLA}
    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        lista = data if isinstance(data, list) else []
        limpias = []
        for ac in lista:
            nom = str(ac.get("nombre") or "").strip()
            nom_low = nom.lower()
            if any(ex in nom_low for ex in PALABRAS_EXCLUIDAS):
                continue
            if nom_low in ["atos", "de la riva"]:
                continue
            if "coordenadas" in ac or nom_low in nombres_sem or es_academia_valida(nom):
                limpias.append(normalizar_academia(ac, len(limpias) + 1))
        return limpias


def main():
    academias = cargar_existentes()
    print(f"Academias previas normalizadas: {len(academias)}")

    vistos = {ac["nombre"].lower().strip() for ac in academias}
    nuevas = 0

    for s in DATOS_SEMILLA:
        clave = s[0].lower().strip()
        if clave not in vistos:
            vistos.add(clave)
            dic_sem = {
                "nombre": s[0],
                "ciudad": s[1],
                "provincia": s[2],
                "afiliacion": s[3],
                "head_coach": s[4],
                "direccion": s[5],
                "lat": s[6],
                "lng": s[7],
                "web": s[8]
            }
            academias.append(normalizar_academia(dic_sem, len(academias) + 1))
            nuevas += 1

    for termino in TERMINOS_BUSQUEDA:
        try:
            params = {
                "q": termino,
                "format": "jsonv2",
                "countrycodes": "es",
                "addressdetails": 1,
                "extratags": 1,
                "limit": 50
            }
            resp = requests.get(
                NOMINATIM_URL,
                params=params,
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
                ciudad = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("municipality")
                    or "Madrid"
                )
                provincia = addr.get("province") or addr.get("state") or ciudad
                extratags = item.get("extratags") or {}
                web = extratags.get("website") or extratags.get("contact:website") or ""
                tel = extratags.get("phone") or extratags.get("contact:phone") or ""

                bruto = {
                    "nombre": nombre,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "direccion": item.get("display_name", ""),
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "web": web,
                    "telefono": tel
                }
                academias.append(normalizar_academia(bruto, len(academias) + 1))
                nuevas += 1
        except Exception as e:
            print(f"Error en '{termino}': {e}")

    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(academias, f, ensure_ascii=False, indent=2)

    features = []
    for a in academias:
        c = a["coordenadas"]
        props = {k: v for k, v in a.items() if k != "coordenadas"}
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [c["lng"], c["lat"]]
            },
            "properties": props
        })

    geojson_data = {"type": "FeatureCollection", "features": features}
    with open(ARCHIVO_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    if os.path.exists(ARCHIVO_HTML):
        with open(ARCHIVO_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        academias_js_str = json.dumps(academias, ensure_ascii=False)
        patron = r'const FALLBACK_ACADEMIAS = \[.*?\];'
        html_nuevo = re.sub(
            patron,
            lambda _: f'const FALLBACK_ACADEMIAS = {academias_js_str};',
            html,
            flags=re.DOTALL
        )
        with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
            f.write(html_nuevo)

    print(f"Exito! Total academias: {len(academias)} (Nuevas: {nuevas})")


if __name__ == "__main__":
    main()
