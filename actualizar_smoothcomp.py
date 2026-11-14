import json
import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

ARCHIVO_JSON = "torneos.json"
ARCHIVO_HTML = "index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

def url_busqueda_directa(nombre, circuito="Smoothcomp"):
    q = urllib.parse.quote_plus(nombre)
    c = circuito.upper()
    if "IBJJF" in c:
        q_ibjjf = urllib.parse.quote_plus(f"site:ibjjf.com {nombre}")
        return f"https://www.google.com/search?q={q_ibjjf}&btnI=1"
    if "AJP" in c:
        return f"https://ajptour.com/en/events/upcoming?search={q}"
    return f"https://smoothcomp.com/es/events/upcoming?search={q}"

# Base verificada de torneos en España (Temporada 2026 / 2027)
TORNEOS_BASE = [
    {"id": "sc-green-capital-2026", "nombre": "Green Capital 2026 (Nordfighter)", "fecha": "2026-11-14", "ciudad": "Vitoria-Gasteiz", "recinto": "Polideportivo Vitoria-Gasteiz, Álava", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-vinyols-challenge-fall-2026", "nombre": "Vinyols Challenge Fall 2026", "fecha": "2026-11-14", "ciudad": "Vinyols i els Arcs (Tarragona)", "recinto": "Pavelló Municipal Vinyols i els Arcs", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-european-cup-guadalajara-2026", "nombre": "European Cup 2026 / Gi - No Gi / Kids", "fecha": "2026-11-15", "ciudad": "Guadalajara", "recinto": "Palacio Multiusos de Guadalajara", "circuito": "AEBJJ / FIJJD", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-bjjpro-zaragoza-2026", "nombre": "BJJPRO Zaragoza 2026 | Oso Duro (D-BJJ)", "fecha": "2026-11-15", "ciudad": "Zaragoza", "recinto": "Polideportivo Municipal Siglo XXI", "circuito": "D-BJJ / Oso Duro", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-europe-cup-valencia-2026", "nombre": "Europe Cup BJJ 2026 (Spain BJJ Tour)", "fecha": "2026-11-21", "ciudad": "Valencia", "recinto": "Pabellón Municipal de Valencia (FIJJD)", "circuito": "AEBJJ / FIJJD", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-open-cantabria-2026", "nombre": "Open Cantabria 2026 | Oso Duro (D-BJJ)", "fecha": "2026-11-21", "ciudad": "Soto de la Marina (Cantabria)", "recinto": "Polideportivo Soto de la Marina", "circuito": "D-BJJ / Oso Duro", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-aranha-interclub-2026", "nombre": "Aranha Interclub 2026 (Niños & Adultos)", "fecha": "2026-11-28", "ciudad": "Barcelona", "recinto": "Sede Aranha BJJ Barcelona", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "torneo-madrid-autumn-2026", "nombre": "Madrid Autumn International Open IBJJF Championship", "fecha": "2026-11-28", "ciudad": "Madrid", "recinto": "Pabellón Deportivo Europa (Leganés)", "circuito": "IBJJF", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-spain-bjj-cup-sevilla-2026", "nombre": "Spain BJJ Cup Gi & No-Gi 2026 (Spain BJJ Tour)", "fecha": "2026-12-05", "ciudad": "Sevilla", "recinto": "Centro Deportivo Sevilla (FIJJD)", "circuito": "AEBJJ / FIJJD", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-grand-slam-baiona-2026", "nombre": "Grand Slam Baiona | D-BJJ", "fecha": "2026-12-05", "ciudad": "Baiona (Pontevedra)", "recinto": "Pabellón Municipal de Deportes de Baiona", "circuito": "D-BJJ / Oso Duro", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-bcn-challenge-winter-2026", "nombre": "BCN Challenge Winter 2026", "fecha": "2026-12-05", "ciudad": "El Papiol (Barcelona)", "recinto": "Pavelló Poliesportiu Municipal El Papiol", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-wn-pro-opens-madrid-2026", "nombre": "WN Pro Opens - Madrid", "fecha": "2026-12-06", "ciudad": "Alcobendas (Madrid)", "recinto": "Polideportivo Alcobendas, Madrid", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-campeonato-espana-adcc-2026", "nombre": "Campeonato de España ADCC", "fecha": "2026-12-12", "ciudad": "La Nucía (Alicante)", "recinto": "Ciutat Esportiva Camilo Cano (La Nucía)", "circuito": "ADCC", "modalidades": ["No-Gi"]},
    {"id": "sc-kimura-cup-zaragoza-2026", "nombre": "Kimura Cup Zaragoza 2026", "fecha": "2026-12-12", "ciudad": "Zaragoza", "recinto": "Pabellón Deportivo Zaragoza (Tour 26/27)", "circuito": "Kimura Cup", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-all-stars-bjj-madrid-2026", "nombre": "All Stars BJJ Madrid", "fecha": "2026-12-13", "ciudad": "Madrid", "recinto": "Pabellón Deportivo Madrid", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-nacional-euskadi-2026", "nombre": "Nacional de Euskadi 2026 | Oso Duro", "fecha": "2026-12-13", "ciudad": "Zamudio (Vizcaya - Euskadi)", "recinto": "Polideportivo Zamudio", "circuito": "D-BJJ / Oso Duro", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-ibiza-bjj-cup-2026", "nombre": "Ibiza BJJ Cup Gi & No-Gi 2026 (Spain BJJ Tour)", "fecha": "2026-12-19", "ciudad": "Santa Eulària des Riu (Ibiza)", "recinto": "Polideportivo Municipal Santa Eulària, Ibiza (FIJJD)", "circuito": "AEBJJ / FIJJD", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-gsls-albacete-open-2026", "nombre": "GSLS Albacete International Open", "fecha": "2026-12-19", "ciudad": "Albacete", "recinto": "Pabellón Universitario de Albacete", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-dojjo-open-altea-2027", "nombre": "Dojjo Open Challenge Altea", "fecha": "2027-01-09", "ciudad": "Altea (Alicante)", "recinto": "Palau dels Esports Vila d'Altea", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-cataluna-bjj-cup-2027", "nombre": "Cataluña BJJ Cup Gi & No-Gi 2027 (Spain BJJ Tour)", "fecha": "2027-01-09", "ciudad": "Castelldefels (Barcelona)", "recinto": "Poliesportiu Municipal Can Vinader (FIJJD)", "circuito": "AEBJJ / FIJJD", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-euskadi-bjj-cup-2027", "nombre": "Euskadi BJJ Cup Gi & No-Gi 2027 (Spain BJJ Tour)", "fecha": "2027-01-30", "ciudad": "Legutio (Álava - Euskadi)", "recinto": "Polideportivo Municipal de Legutio (FIJJD)", "circuito": "AEBJJ / FIJJD", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-kimura-cup-madrid-2027", "nombre": "Kimura Cup Madrid 2027", "fecha": "2027-01-31", "ciudad": "Arganda del Rey (Madrid)", "recinto": "Ciudad Deportiva Príncipe Felipe (Arganda del Rey)", "circuito": "Kimura Cup", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "sc-polaris-open-madrid-2027", "nombre": "Polaris Open Spain - Madrid", "fecha": "2027-02-20", "ciudad": "Madrid", "recinto": "Centro Deportivo Amorós, Madrid", "circuito": "Polaris / Smoothcomp", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-open-villanueva-rio-segura-2027", "nombre": "Open de Villanueva del Río Segura (Liga BJJ)", "fecha": "2027-02-20", "ciudad": "Villanueva del Río Segura (Murcia)", "recinto": "Pabellón Municipal Villanueva del Río Segura", "circuito": "Smoothcomp", "modalidades": ["Gi", "No-Gi", "Kids"]},
    {"id": "torneo-spain-national-ajp-2027", "nombre": "AJP Tour Spain National Jiu-Jitsu Pro", "fecha": "2027-02-20", "ciudad": "Valencia", "recinto": "Velódromo Luis Puig", "circuito": "AJP Tour", "modalidades": ["Gi", "No-Gi"]},
    {"id": "torneo-madrid-spring-ibjjf-2027", "nombre": "Madrid Spring International Open IBJJF Championship", "fecha": "2027-03-27", "ciudad": "Madrid", "recinto": "Polideportivo Municipal Gallur", "circuito": "IBJJF", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-abierto-leon-dbjj-2027", "nombre": "Abierto de León | D-BJJ 2027", "fecha": "2027-04-24", "ciudad": "León", "recinto": "Palacio de los Deportes de León", "circuito": "D-BJJ / Oso Duro", "modalidades": ["Gi", "No-Gi"]},
    {"id": "torneo-barcelona-open-ibjjf-2027", "nombre": "Barcelona International Open IBJJF Championship", "fecha": "2027-05-15", "ciudad": "Barcelona", "recinto": "Complex Esportiu Municipal Mar Bella", "circuito": "IBJJF", "modalidades": ["Gi", "No-Gi"]},
    {"id": "sc-grappling-industries-madrid-2027", "nombre": "Grappling Industries Madrid (Round Robin)", "fecha": "2027-05-22", "ciudad": "Madrid", "recinto": "Pabellón Deportivo Madrid", "circuito": "Grappling Industries", "modalidades": ["Gi", "No-Gi"]}
]

def extraer_enlaces_smoothcomp():
    """Intenta capturar enlaces directos /event/XXXX desde Smoothcomp para España."""
    mapa_enlaces = {}
    urls = [
        "https://smoothcomp.com/es/events/upcoming?countries=ES",
        "https://smoothcomp.com/en/events/upcoming?countries=ES"
    ]
    for u in urls:
        try:
            r = requests.get(u, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                match = re.search(r"/event/(\d+)", href)
                if match:
                    event_id = match.group(1)
                    titulo = a.get_text(strip=True)
                    if titulo and len(titulo) > 4:
                        url_limpia = f"https://smoothcomp.com/es/event/{event_id}"
                        mapa_enlaces[titulo.lower()] = url_limpia
        except Exception as e:
            print(f"Aviso leyendo {u}: {e}")
    return mapa_enlaces

def main():
    enlaces_sc = extraer_enlaces_smoothcomp()
    print(f"Enlaces individuales detectados en vivo en Smoothcomp: {len(enlaces_sc)}")

    torneos_finales = []
    for t in TORNEOS_BASE:
        item = dict(t)
        nom_low = item["nombre"].lower()
        enlace_especifico = None

        for k_titulo, link_real in enlaces_sc.items():
            if k_titulo in nom_low or nom_low in k_titulo:
                enlace_especifico = link_real
                break

        if enlace_especifico:
            item["enlace"] = enlace_especifico
        else:
            item["enlace"] = url_busqueda_directa(item["nombre"], item["circuito"])

        torneos_finales.append(item)

    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(torneos_finales, f, ensure_ascii=False, indent=2)

    if os.path.exists(ARCHIVO_HTML):
        with open(ARCHIVO_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        torneos_js_str = json.dumps(torneos_finales, ensure_ascii=False)
        patron = r"const FALLBACK_TORNEOS = \[.*?\];"
        html_nuevo = re.sub(
            patron,
            lambda _: f"const FALLBACK_TORNEOS = {torneos_js_str};",
            html,
            flags=re.DOTALL
        )
        with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
            f.write(html_nuevo)

    print(f"Exito! {len(torneos_finales)} torneos actualizados con enlaces directos en {ARCHIVO_JSON} e {ARCHIVO_HTML}.")

if __name__ == "__main__":
    main()
