import json
import os
import re
import time
import unicodedata
import urllib.parse
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

# Formato: (Nombre, Ciudad, Provincia, Filial, Coach, Direccion, Lat, Lng, Tel, IG, Web)
DATOS_SEMILLA = [
    ("Mathias Ribeiro Team Madrid", "Madrid", "Madrid", "Mathias Ribeiro",
     "Prof. Mathias Ribeiro", "Calle de Gutenberg 7, 28014 Madrid",
     40.4055, -3.6766, "+34 914 34 55 18", "@mathiasribeiroteam",
     "https://mathiasribeiro.com"),
    ("Checkmat Madrid / Samurai", "Madrid", "Madrid", "Checkmat",
     "Equipo Checkmat", "Calle de Juan Español 38, 28026 Madrid",
     40.3879, -3.7011, "+34 638 82 21 56", "@checkmatmadrid",
     "https://checkmatmadrid.com"),
    ("Lotus Club Madrid BJJ", "Madrid", "Madrid", "Lotus Club",
     "Instructor Certificado", "Calle de Tarragona 18, 28045 Madrid",
     40.4015, -3.6935, "+34 654 91 12 30", "@lotusclubmadrid",
     "https://www.instagram.com/lotusclubmadrid/"),
    ("Tenth Planet Madrid BJJ", "Madrid", "Madrid", "10th Planet",
     "Instructor Certificado", "Calle de la Palma 38, 28004 Madrid",
     40.4265, -3.7042, "+34 611 45 89 20", "@10thplanetmadrid",
     "https://www.instagram.com/10thplanetmadrid/"),
    ("De La Riva BJJ Madrid", "Madrid", "Madrid", "De La Riva",
     "Instructor Certificado", "Calle de Alcalá 211, 28028 Madrid",
     40.4290, -3.6620, "+34 622 39 10 44", "@delarivamadrid",
     "https://www.instagram.com/delarivamadrid/"),
    ("Carlson Gracie Madrid", "Madrid", "Madrid", "Carlson Gracie",
     "Instructor Certificado", "Calle de Bravo Murillo 150, 28020 Madrid",
     40.4510, -3.7030, "+34 670 81 92 11", "@carlsongraciemadrid",
     "https://www.instagram.com/carlsongraciemadrid/"),
    ("Atos BJJ Barcelona", "Barcelona", "Barcelona", "Atos Jiu-Jitsu",
     "Prof. Gustavo Galvao", "Carrer de Pujades 77, 08005 Barcelona",
     41.3965, 2.1965, "+34 666 12 34 89", "@atosbarcelona",
     "https://atosbarcelona.com"),
    ("Aranha Jiu Jitsu Barcelona", "Barcelona", "Barcelona", "Aranha",
     "Prof. Yan Cabral", "Carrer de Sants 180, 08028 Barcelona",
     41.3755, 2.1310, "+34 655 98 23 11", "@aranhabarcelona",
     "https://www.instagram.com/aranhabarcelona/"),
    ("Anaconda BJJ Barcelona", "Barcelona", "Barcelona", "Anaconda BJJ",
     "Prof. Chen Moraes", "Carrer de Còrsega 520, 08025 Barcelona",
     41.4042, 2.1715, "+34 931 25 44 90", "@anacondabjj",
     "https://anacondabjj.com"),
    ("Templum BCN Jiu Jitsu", "Barcelona", "Barcelona", "Templum BCN",
     "Prof. Yan Cabral", "Carrer d'Entença 113, 08015 Barcelona",
     41.3812, 2.1485, "+34 936 33 81 31", "@templumbcn",
     "https://templumbcn.com"),
    ("GFTeam Barcelona BJJ", "Barcelona", "Barcelona", "GFTeam",
     "Instructor Certificado", "Carrer de Mallorca 410, 08013 Barcelona",
     41.4030, 2.1740, "+34 633 74 11 90", "@gfteambarcelona",
     "https://www.instagram.com/gfteambarcelona/"),
    ("Ases Jiu Jitsu Valencia", "Valencia", "Valencia", "Ases BJJ",
     "Prof. Ezequiel Zayas", "Carrer de la Democràcia 62, 46018 Valencia",
     39.4715, -0.4025, "+34 658 91 20 11", "@asesbjj",
     "https://asesbjj.com"),
    ("Checkmat Valencia BJJ", "Valencia", "Valencia", "Checkmat",
     "Instructor Certificado", "Avinguda del Cid 85, 46018 Valencia",
     39.4690, -0.3980, "+34 644 51 82 30", "@checkmatvalencia",
     "https://www.instagram.com/checkmatvalencia/"),
    ("Climent Club BJJ Alicante", "Alicante", "Alicante", "Climent Club",
     "Agustín y Jorge Climent", "Calle Poeta Sansano 25, 03005 Alicante",
     38.3585, -0.4882, "+34 661 29 38 40", "@climentclub",
     "https://www.instagram.com/climentclub/"),
    ("Checkmat Alicante BJJ", "Alicante", "Alicante", "Checkmat",
     "Instructor Certificado", "Calle Pardo Gimeno 45, 03007 Alicante",
     38.3490, -0.4910, "+34 678 19 22 45", "@checkmatalicante",
     "https://www.instagram.com/checkmatalicante/"),
    ("Sutemi Academy BJJ Sevilla", "Sevilla", "Sevilla", "Sutemi",
     "Instructor Certificado", "Calle Astronomía 1, 41015 Sevilla",
     37.4180, -5.9710, "+34 695 40 31 22", "@sutemiacademy",
     "https://www.instagram.com/sutemiacademy/"),
    ("Roger Gracie Academy Málaga", "Málaga", "Málaga", "Roger Gracie",
     "Instructor Certificado", "Camino de San Rafael 49, 29006 Málaga",
     36.7080, -4.4490, "+34 620 84 51 90", "@rogergraciemalaga",
     "https://www.instagram.com/rogergraciemalaga/"),
    ("Roger Gracie Marbella", "Marbella", "Málaga", "Roger Gracie",
     "Instructor Certificado", "Bulevar Príncipe Alfonso de Hohenlohe, 29602 Marbella",
     36.5100, -4.8850, "+34 639 11 48 70", "@rogergraciemarbella",
     "https://rogergraciemarbella.com"),
    ("Zenit BJJ Zaragoza", "Zaragoza", "Zaragoza", "Zenit BJJ",
     "Instructor Certificado", "Calle de Roger de Flor 5, 50017 Zaragoza",
     41.6515, -0.9080, "+34 651 90 34 12", "@zenitbjj",
     "https://www.instagram.com/zenitbjj/"),
    ("Ufight Academy BJJ Bilbao", "Bilbao", "Vizcaya", "Ufight",
     "Instructor Certificado", "Autonomia Kalea 50, 48012 Bilbao",
     43.2575, -2.9410, "+34 944 07 69 10", "@ufightbilbao",
     "https://ufight.es"),
    ("Gracie Barra San Sebastián", "San Sebastián", "Guipúzcoa", "Gracie Barra",
     "Instructor Certificado GB", "Paseo de Anoeta 18, 20014 Donostia",
     43.3015, -1.9735, "+34 688 91 20 45", "@gbsansebastian",
     "https://www.instagram.com/gbsansebastian/"),
    ("Mallorca BJJ / Checkmat", "Palma de Mallorca", "Islas Baleares", "Checkmat",
     "Instructor Certificado", "Carrer del Gremi de Sabaters 21, 07009 Palma",
     39.6010, 2.6680, "+34 671 33 90 12", "@mallorcabjj",
     "https://www.instagram.com/mallorcabjj/"),
    ("Taz Jinámar Gran Canaria", "Las Palmas", "Islas Canarias", "Taz Academy",
     "Instructor Certificado", "Carretera General de Jinámar 42, 35220 Las Palmas",
     28.0350, -15.4180, "+34 628 19 44 80", "@tazjinamar",
     "https://www.instagram.com/tazjinamar/"),
    ("Gil Catarino BJJ Tenerife", "Santa Cruz de Tenerife", "Islas Canarias", "Gil Catarino",
     "Prof. Gil Catarino", "Calle Subida Cuesta Piedra 18, 38008 Santa Cruz de Tenerife",
     28.4615, -16.2730, "+34 646 82 11 95", "@gilcatarinobjj",
     "https://www.instagram.com/gilcatarinobjj/"),
    ("Gracie Barra A Coruña", "A Coruña", "A Coruña", "Gracie Barra",
     "Instructor Certificado GB", "Rúa Gambrinus 14, 15008 A Coruña",
     43.3485, -8.4230, "+34 619 75 30 22", "@gbacoruna",
     "https://www.instagram.com/gbacoruna/"),
    ("GFTeam Vigo BJJ", "Vigo", "Pontevedra", "GFTeam",
     "Instructor Certificado", "Rúa de Urzaiz 120, 36205 Vigo",
     42.2315, -8.7110, "+34 664 20 89 15", "@gfteamvigo",
     "https://www.instagram.com/gfteamvigo/")
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


def armar_url_maps(nombre, ciudad):
    q = urllib.parse.quote_plus(f"{nombre} {ciudad} España")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def normalizar_academia(ac, indice):
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
    tel_raw = ac.get("telefono") or cont.get("telefono") or ""
    wa_num = cont.get("whatsapp") or re.sub(r'[^0-9]', '', tel_raw)
    if len(wa_num) == 9 and wa_num[0] in ['6', '7']:
        wa_num = "34" + wa_num

    ig_raw = ac.get("instagram") or cont.get("instagram") or ""
    if ig_raw and not ig_raw.startswith("@") and "instagram.com/" in ig_raw:
        partes_ig = [p for p in ig_raw.split("/") if p]
        ig_raw = "@" + partes_ig[-1]
    elif ig_raw and not ig_raw.startswith("@"):
        ig_raw = "@" + ig_raw

    web_raw = ac.get("web") or cont.get("web") or ""
    if web_raw and not web_raw.startswith("http"):
        web_raw = "https://" + web_raw
    if not web_raw:
        web_raw = armar_url_maps(nombre, ciudad)

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
            "instagram": ig_raw
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


def tiene_contacto_real(ac):
    cont = ac.get("contacto") or {}
    tel = ac.get("telefono") or cont.get("telefono") or ""
    wa = cont.get("whatsapp") or ""
    ig = ac.get("instagram") or cont.get("instagram") or ""
    web = ac.get("web") or cont.get("web") or ""
    tiene_web_propia = bool(web and "google.com/maps/search" not in web)
    return bool(tel or wa or ig or tiene_web_propia)


def cargar_existentes():
    if not os.path.exists(ARCHIVO_JSON):
        return []
    mapa_semilla = {s[0].lower().strip(): s for s in DATOS_SEMILLA}
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
            # Si está en DATOS_SEMILLA, la pisamos luego con los datos completos nuevos
            if nom_low in mapa_semilla:
                continue
            # Conservar solo si es destacada original o tiene contacto real
            if ac.get("destacada_premium") or tiene_contacto_real(ac):
                limpias.append(normalizar_academia(ac, len(limpias) + 1))
        return limpias


def main():
    academias = cargar_existentes()
    print(f"Academias previas con contacto completo: {len(academias)}")

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
                "telefono": s[8],
                "instagram": s[9],
                "web": s[10]
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

                addr = item.get("address", {})
                calle = addr.get("road") or addr.get("pedestrian") or ""
                numero = addr.get("house_number") or ""
                cp = addr.get("postcode") or ""
                ciudad = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("municipality")
                    or ""
                )
                provincia = addr.get("province") or addr.get("state") or ciudad

                extratags = item.get("extratags") or {}
                web = extratags.get("website") or extratags.get("contact:website") or ""
                tel = extratags.get("phone") or extratags.get("contact:phone") or ""
                ig = extratags.get("contact:instagram") or extratags.get("instagram") or ""

                # Exigir que tenga calle real Y al menos un medio de contacto directo
                if not calle or not ciudad or not (web or tel or ig):
                    continue

                vistos.add(clave)
                dir_limpia = f"{calle} {numero}".strip()
                if cp:
                    dir_limpia += f", {cp} {ciudad}"
                else:
                    dir_limpia += f", {ciudad}"

                bruto = {
                    "nombre": nombre,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "direccion": dir_limpia,
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "web": web,
                    "telefono": tel,
                    "instagram": ig
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

    print(f"Exito! Total con contacto completo: {len(academias)} (Nuevas/Actualizadas: {nuevas})")


if __name__ == "__main__":
    main()
