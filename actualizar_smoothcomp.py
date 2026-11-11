import json
import os
import re
import urllib.request
from datetime import datetime, date

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12
}

CIUDADES_ESPANA = [
    "madrid", "barcelona", "valencia", "sevilla", "seville", "malaga", "málaga",
    "bilbao", "zaragoza", "alicante", "murcia", "palma", "mallorca", "ibiza",
    "tenerife", "gran canaria", "las palmas", "leon", "león", "vitoria",
    "guadalajara", "albacete", "castelldefels", "badalona", "leganes", "leganés",
    "alcobendas", "arganda", "nucia", "nucía", "altea", "baiona", "zamudio",
    "spain", "españa"
]

def es_evento_espana(texto):
    t = str(texto).lower()
    return any(c in t for c in CIUDADES_ESPANA)

def parsear_fecha_smoothcomp(texto_fecha, anio_actual=None):
    """
    Convierte fechas de Smoothcomp e IBJJF como 'diciembre 12', '2027 enero 31',
    'noviembre 21 - 22', 'Nov 28 - Nov 29, 2026' o '2026-12-12' al formato ISO 'YYYY-MM-DD'.
    """
    if not texto_fecha:
        return ""
    texto = str(texto_fecha).strip().lower()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", texto):
        return texto

    hoy = date.today()
    anio_def = anio_actual or hoy.year

    # Buscar si ya trae año explícito (ej. '2027 enero 31' o 'Nov 28, 2026')
    m_anio = re.search(r"\b(202\d)\b", texto)
    if m_anio:
        anio_def = int(m_anio.group(1))

    # Buscar mes por nombre
    mes_num = None
    for nombre_mes, num in sorted(MESES_ES.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(nombre_mes) + r"\b", texto):
            mes_num = num
            break

    # Buscar primer día numérico (1 a 31) que no sea el año
    texto_sin_anio = re.sub(r"\b202\d\b", "", texto)
    m_dia = re.search(r"\b(\d{1,2})\b", texto_sin_anio)
    if mes_num and m_dia:
        dia_num = int(m_dia.group(1))
        if not m_anio and mes_num < hoy.month:
            anio_def = hoy.year + 1
        try:
            return f"{anio_def:04d}-{mes_num:02d}-{dia_num:02d}"
        except ValueError:
            return ""
    return ""

def detectar_circuito(titulo):
    t = titulo.upper()
    if "IBJJF" in t:
        return "IBJJF"
    if "AJP" in t:
        return "AJP Tour"
    if "ADCC" in t:
        return "ADCC"
    if "KIMURA" in t:
        return "Kimura Cup"
    if "D-BJJ" in t or "OSO DURO" in t:
        return "D-BJJ / Oso Duro"
    if "FIJJD" in t or "AEBJJ" in t or "SPAIN BJJ" in t or "CUP BJJ" in t:
        return "AEBJJ / FIJJD"
    if "GRAPPLING INDUSTRIES" in t:
        return "Grappling Industries"
    if "POLARIS" in t:
        return "Polaris / Smoothcomp"
    return "Smoothcomp"

def detectar_modalidades(titulo):
    t = titulo.upper()
    if "NO-GI" in t or "NOGI" in t:
        if "GI" in re.sub(r"NO[-\s]?GI", "", t):
            mods = ["Gi", "No-Gi"]
        else:
            mods = ["No-Gi"]
    else:
        mods = ["Gi", "No-Gi"]
    if "ADCC" in t and "GI" not in t.replace("NOGI", "").replace("NO-GI", ""):
        mods = ["No-Gi"]
    if "KIDS" in t or "NIÑOS" in t or "INFANTIL" in t:
        if "Kids" not in mods:
            mods.append("Kids")
    return mods

def obtener_eventos_smoothcomp_espana():
    """
    Consulta Smoothcomp en español filtrando por España (ES) y las 4 categorías de BJJ/Grappling.
    """
    urls_a_consultar = [
        "https://smoothcomp.com/es/events/upcoming?countries=ES&categories%5B%5D=1&categories%5B%5D=7&categories%5B%5D=2&categories%5B%5D=3",
        "https://smoothcomp.com/es/events/upcoming?countries=ES&categories=1%2C2%2C3%2C4%2C7",
        "https://smoothcomp.com/es/events/upcoming?countries=ES",
        "https://smoothcomp.com/en/events/upcoming?countries=ES"
    ]
    eventos_extraidos = []
    vistos = set()

    for url in urls_a_consultar:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

                # 1. Extraer el JSON interno que Smoothcomp inyecta para Vue.js (var events = [...];)
                m_json = re.search(r"var\s+events\s*=\s*(\[.*?\]);\s*\n", html, re.DOTALL)
                if m_json:
                    try:
                        lista_raw = json.loads(m_json.group(1))
                        for item in lista_raw:
                            ev_id = str(item.get("id", ""))
                            titulo = (item.get("title") or "").strip()
                            if not ev_id or not titulo or ev_id in vistos:
                                continue
                            vistos.add(ev_id)
                            link = item.get("url") or f"https://smoothcomp.com/es/event/{ev_id}"
                            ciudad = item.get("location_city") or item.get("city") or "España"
                            fecha_raw = item.get("startdate") or item.get("date") or ""
                            fecha_iso = parsear_fecha_smoothcomp(fecha_raw)
                            if fecha_iso:
                                eventos_extraidos.append({
                                    "id": f"sc-{ev_id}",
                                    "nombre": titulo,
                                    "fecha": fecha_iso,
                                    "ciudad": ciudad,
                                    "recinto": f"{ciudad}, España",
                                    "circuito": detectar_circuito(titulo),
                                    "modalidades": detectar_modalidades(titulo),
                                    "enlace": link
                                })
                    except Exception:
                        pass

                # 2. Respaldo por Regex sobre las tarjetas HTML
                matches = re.findall(
                    r'href=["\'](https://smoothcomp\.com/[a-z]{2}/event/(\d+))["\'][^>]*>\s*([^<]+?)\s*</a>',
                    html
                )
                for link, ev_id, titulo in matches:
                    titulo_limpio = titulo.strip()
                    if ev_id not in vistos and len(titulo_limpio) > 4:
                        vistos.add(ev_id)
                        eventos_extraidos.append({
                            "id": f"sc-{ev_id}",
                            "nombre": titulo_limpio,
                            "fecha": "",
                            "ciudad": "España",
                            "recinto": "Sede oficial en Smoothcomp",
                            "circuito": detectar_circuito(titulo_limpio),
                            "modalidades": detectar_modalidades(titulo_limpio),
                            "enlace": link
                        })
        except Exception as e:
            print(f"[Aviso Smoothcomp] Consulta a {url} omitida ({e}).")

    return eventos_extraidos

def obtener_eventos_ibjjf_espana():
    """
    Consulta automáticamente los endpoints de calendario de IBJJF (ibjjf.com)
    y extrae cualquier campeonato oficial programado en España (Madrid, Barcelona, etc.).
    """
    urls_ibjjf = [
        "https://ibjjf.com/api/v1/events/calendar.json",
        "https://ibjjf.com/api/v1/events/upcomings.json",
        "https://ibjjf.com/events/calendar",
        "https://ibjjf.com/events/championships"
    ]
    eventos_ibjjf = []
    vistos = set()

    for url in urls_ibjjf:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "application/json, text/html, */*"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                contenido = resp.read().decode("utf-8", errors="ignore")

                # Caso 1: Respuesta JSON de la API interna de IBJJF
                if contenido.strip().startswith("{") or contenido.strip().startswith("["):
                    try:
                        data = json.loads(contenido)
                        lista = data.get("events", data.get("championships", data if isinstance(data, list) else []))
                        for item in lista:
                            if not isinstance(item, dict):
                                continue
                            titulo = (item.get("name") or item.get("title") or "").strip()
                            ciudad = (item.get("city") or item.get("location") or "").strip()
                            pais = (item.get("country") or "").strip()
                            recinto = (item.get("local") or item.get("venue") or f"Pabellón Oficial IBJJF ({ciudad or 'España'})").strip()
                            if not es_evento_espana(f"{titulo} {ciudad} {pais}"):
                                continue
                            fecha_raw = item.get("start_date") or item.get("date") or item.get("InitDate") or ""
                            fecha_iso = parsear_fecha_smoothcomp(fecha_raw)
                            slug = re.sub(r"[^a-z0-9]+", "-", titulo.lower()).strip("-")
                            ev_id = f"ibjjf-{slug}"
                            if not titulo or ev_id in vistos or not fecha_iso:
                                continue
                            vistos.add(ev_id)
                            url_ev = item.get("url") or item.get("page_url") or "https://ibjjf.com/events/calendar"
                            if url_ev.startswith("/"):
                                url_ev = f"https://ibjjf.com{url_ev}"
                            if not ciudad:
                                ciudad = "Barcelona" if "barcelona" in titulo.lower() else "Madrid"
                            eventos_ibjjf.append({
                                "id": ev_id,
                                "nombre": titulo if "IBJJF" in titulo.upper() else f"{titulo} IBJJF",
                                "fecha": fecha_iso,
                                "ciudad": ciudad,
                                "recinto": recinto,
                                "circuito": "IBJJF",
                                "modalidades": detectar_modalidades(titulo),
                                "enlace": url_ev
                            })
                    except Exception:
                        pass

                # Caso 2: Extracción desde el HTML o JSON embebido en la página de calendario IBJJF
                bloques_html = re.findall(
                    r'([A-Z][A-Za-z0-9\s\-]*?(?:Madrid|Barcelona|Spain|Valencia|Sevilla|Malaga|Ibiza)[A-Za-z0-9\s\-]*?IBJJF[A-Za-z0-9\s\-]*)',
                    contenido
                )
                for titulo_hallado in bloques_html:
                    t_limpio = " ".join(titulo_hallado.split()).strip()
                    slug = re.sub(r"[^a-z0-9]+", "-", t_limpio.lower()).strip("-")
                    ev_id = f"ibjjf-{slug}"
                    if len(t_limpio) > 12 and ev_id not in vistos:
                        # Buscar fecha cercana en el HTML alrededor del nombre del torneo
                        pos = contenido.find(titulo_hallado)
                        ventana = contenido[max(0, pos - 400):min(len(contenido), pos + 600)]
                        m_fecha = re.search(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:[^<\n]{0,15}202\d)?)", ventana, re.IGNORECASE)
                        fecha_iso = parsear_fecha_smoothcomp(m_fecha.group(1)) if m_fecha else ""
                        if fecha_iso:
                            vistos.add(ev_id)
                            ciudad_det = "Barcelona" if "barcelona" in t_limpio.lower() else "Madrid"
                            eventos_ibjjf.append({
                                "id": ev_id,
                                "nombre": t_limpio,
                                "fecha": fecha_iso,
                                "ciudad": ciudad_det,
                                "recinto": f"Pabellón Oficial IBJJF ({ciudad_det})",
                                "circuito": "IBJJF",
                                "modalidades": detectar_modalidades(t_limpio),
                                "enlace": "https://ibjjf.com/events/calendar"
                            })
        except Exception as e:
            print(f"[Aviso IBJJF] Consulta a {url} omitida ({e}).")

    return eventos_ibjjf

def normalizar_enlace_oficial(torneo):
    """
    Garantiza que los torneos de IBJJF y AJP Tour apunten siempre a sus calendarios oficiales
    y nunca queden con el enlace genérico de Smoothcomp por error.
    """
    circuito = str(torneo.get("circuito", "")).upper()
    nombre = str(torneo.get("nombre", "")).upper()
    enlace_actual = str(torneo.get("enlace", "")).strip()

    if "IBJJF" in circuito or "IBJJF" in nombre:
        if not enlace_actual or "smoothcomp.com" in enlace_actual:
            torneo["enlace"] = "https://ibjjf.com/events/calendar"
        torneo["circuito"] = "IBJJF"
    elif "AJP" in circuito or "AJP" in nombre:
        if not enlace_actual or "smoothcomp.com" in enlace_actual:
            torneo["enlace"] = "https://ajptour.com/en/events/upcoming"
        torneo["circuito"] = "AJP Tour"
    return torneo

def obtener_calendario_oficial_base():
    """
    Calendario completo de 29 torneos verificados en España (Smoothcomp Gi / NoGi / ADCC / Submission Wrestling + IBJJF + AJP).
    """
    return [
        {
            "id": "sc-green-capital-2026",
            "nombre": "Green Capital 2026 (Nordfighter)",
            "fecha": "2026-11-14",
            "ciudad": "Vitoria-Gasteiz",
            "recinto": "Polideportivo Vitoria-Gasteiz, Álava",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-vinyols-challenge-fall-2026",
            "nombre": "Vinyols Challenge Fall 2026",
            "fecha": "2026-11-14",
            "ciudad": "Vinyols i els Arcs (Tarragona)",
            "recinto": "Pavelló Municipal Vinyols i els Arcs",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-european-cup-guadalajara-2026",
            "nombre": "European Cup 2026 / Gi - No Gi / Kids",
            "fecha": "2026-11-15",
            "ciudad": "Guadalajara",
            "recinto": "Palacio Multiusos de Guadalajara",
            "circuito": "AEBJJ / FIJJD",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-bjjpro-zaragoza-2026",
            "nombre": "BJJPRO Zaragoza 2026 | Oso Duro (D-BJJ)",
            "fecha": "2026-11-15",
            "ciudad": "Zaragoza",
            "recinto": "Polideportivo Municipal Siglo XXI",
            "circuito": "D-BJJ / Oso Duro",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-europe-cup-valencia-2026",
            "nombre": "Europe Cup BJJ 2026 (Spain BJJ Tour)",
            "fecha": "2026-11-21",
            "ciudad": "Valencia",
            "recinto": "Pabellón Municipal de Valencia (FIJJD)",
            "circuito": "AEBJJ / FIJJD",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-open-cantabria-2026",
            "nombre": "Open Cantabria 2026 | Oso Duro (D-BJJ)",
            "fecha": "2026-11-21",
            "ciudad": "Soto de la Marina (Cantabria)",
            "recinto": "Polideportivo Soto de la Marina",
            "circuito": "D-BJJ / Oso Duro",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-aranha-interclub-2026",
            "nombre": "Aranha Interclub 2026 (Niños & Adultos)",
            "fecha": "2026-11-28",
            "ciudad": "Barcelona",
            "recinto": "Sede Aranha BJJ Barcelona",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "torneo-madrid-autumn-2026",
            "nombre": "Madrid Autumn International Open IBJJF Championship",
            "fecha": "2026-11-28",
            "ciudad": "Madrid",
            "recinto": "Pabellón Deportivo Europa (Leganés)",
            "circuito": "IBJJF",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://ibjjf.com/events/calendar"
        },
        {
            "id": "sc-spain-bjj-cup-sevilla-2026",
            "nombre": "Spain BJJ Cup Gi & No-Gi 2026 (Spain BJJ Tour)",
            "fecha": "2026-12-05",
            "ciudad": "Sevilla",
            "recinto": "Centro Deportivo Sevilla (FIJJD)",
            "circuito": "AEBJJ / FIJJD",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-grand-slam-baiona-2026",
            "nombre": "Grand Slam Baiona | D-BJJ",
            "fecha": "2026-12-05",
            "ciudad": "Baiona (Pontevedra)",
            "recinto": "Pabellón Municipal de Deportes de Baiona",
            "circuito": "D-BJJ / Oso Duro",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-bcn-challenge-winter-2026",
            "nombre": "BCN Challenge Winter 2026",
            "fecha": "2026-12-05",
            "ciudad": "El Papiol (Barcelona)",
            "recinto": "Pavelló Poliesportiu Municipal El Papiol",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-wn-pro-opens-madrid-2026",
            "nombre": "WN Pro Opens - Madrid",
            "fecha": "2026-12-06",
            "ciudad": "Alcobendas (Madrid)",
            "recinto": "Polideportivo Alcobendas, Madrid",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-campeonato-espana-adcc-2026",
            "nombre": "Campeonato de España ADCC",
            "fecha": "2026-12-12",
            "ciudad": "La Nucía (Alicante)",
            "recinto": "Ciutat Esportiva Camilo Cano (La Nucía)",
            "circuito": "ADCC",
            "modalidades": ["No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-kimura-cup-zaragoza-2026",
            "nombre": "Kimura Cup Zaragoza 2026",
            "fecha": "2026-12-12",
            "ciudad": "Zaragoza",
            "recinto": "Pabellón Deportivo Zaragoza (Tour 26/27)",
            "circuito": "Kimura Cup",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-all-stars-bjj-madrid-2026",
            "nombre": "All Stars BJJ Madrid",
            "fecha": "2026-12-13",
            "ciudad": "Madrid",
            "recinto": "Pabellón Deportivo Madrid",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-nacional-euskadi-2026",
            "nombre": "Nacional de Euskadi 2026 | Oso Duro",
            "fecha": "2026-12-13",
            "ciudad": "Zamudio (Vizcaya - Euskadi)",
            "recinto": "Polideportivo Zamudio",
            "circuito": "D-BJJ / Oso Duro",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-ibiza-bjj-cup-2026",
            "nombre": "Ibiza BJJ Cup Gi & No-Gi 2026 (Spain BJJ Tour)",
            "fecha": "2026-12-19",
            "ciudad": "Santa Eulària des Riu (Ibiza)",
            "recinto": "Polideportivo Municipal Santa Eulària, Ibiza (FIJJD)",
            "circuito": "AEBJJ / FIJJD",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-gsls-albacete-open-2026",
            "nombre": "GSLS Albacete International Open",
            "fecha": "2026-12-19",
            "ciudad": "Albacete",
            "recinto": "Pabellón Universitario de Albacete",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-dojjo-open-altea-2027",
            "nombre": "Dojjo Open Challenge Altea",
            "fecha": "2027-01-09",
            "ciudad": "Altea (Alicante)",
            "recinto": "Palau dels Esports Vila d'Altea",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-cataluna-bjj-cup-2027",
            "nombre": "Cataluña BJJ Cup Gi & No-Gi 2027 (Spain BJJ Tour)",
            "fecha": "2027-01-09",
            "ciudad": "Castelldefels (Barcelona)",
            "recinto": "Poliesportiu Municipal Can Vinader (FIJJD)",
            "circuito": "AEBJJ / FIJJD",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-euskadi-bjj-cup-2027",
            "nombre": "Euskadi BJJ Cup Gi & No-Gi 2027 (Spain BJJ Tour)",
            "fecha": "2027-01-30",
            "ciudad": "Legutio (Álava - Euskadi)",
            "recinto": "Polideportivo Municipal de Legutio (FIJJD)",
            "circuito": "AEBJJ / FIJJD",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-kimura-cup-madrid-2027",
            "nombre": "Kimura Cup Madrid 2027",
            "fecha": "2027-01-31",
            "ciudad": "Arganda del Rey (Madrid)",
            "recinto": "Ciudad Deportiva Príncipe Felipe (Arganda del Rey)",
            "circuito": "Kimura Cup",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-polaris-open-madrid-2027",
            "nombre": "Polaris Open Spain - Madrid",
            "fecha": "2027-02-20",
            "ciudad": "Madrid",
            "recinto": "Centro Deportivo Amorós, Madrid",
            "circuito": "Polaris / Smoothcomp",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "sc-open-villanueva-rio-segura-2027",
            "nombre": "Open de Villanueva del Río Segura (Liga BJJ)",
            "fecha": "2027-02-20",
            "ciudad": "Villanueva del Río Segura (Murcia)",
            "recinto": "Pabellón Municipal Villanueva del Río Segura",
            "circuito": "Smoothcomp",
            "modalidades": ["Gi", "No-Gi", "Kids"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "torneo-spain-national-ajp-2027",
            "nombre": "AJP Tour Spain National Jiu-Jitsu Pro",
            "fecha": "2027-02-20",
            "ciudad": "Valencia",
            "recinto": "Velódromo Luis Puig",
            "circuito": "AJP Tour",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://ajptour.com/en/events/upcoming"
        },
        {
            "id": "torneo-madrid-spring-ibjjf-2027",
            "nombre": "Madrid Spring International Open IBJJF Championship",
            "fecha": "2027-03-27",
            "ciudad": "Madrid",
            "recinto": "Polideportivo Municipal Gallur",
            "circuito": "IBJJF",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://ibjjf.com/events/calendar"
        },
        {
            "id": "sc-abierto-leon-dbjj-2027",
            "nombre": "Abierto de León | D-BJJ 2027",
            "fecha": "2027-04-24",
            "ciudad": "León",
            "recinto": "Palacio de los Deportes de León",
            "circuito": "D-BJJ / Oso Duro",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        },
        {
            "id": "torneo-barcelona-open-ibjjf-2027",
            "nombre": "Barcelona International Open IBJJF Championship",
            "fecha": "2027-05-15",
            "ciudad": "Barcelona",
            "recinto": "Complex Esportiu Municipal Mar Bella",
            "circuito": "IBJJF",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://ibjjf.com/events/calendar"
        },
        {
            "id": "sc-grappling-industries-madrid-2027",
            "nombre": "Grappling Industries Madrid (Round Robin)",
            "fecha": "2027-05-22",
            "ciudad": "Madrid",
            "recinto": "Pabellón Deportivo Madrid",
            "circuito": "Grappling Industries",
            "modalidades": ["Gi", "No-Gi"],
            "enlace": "https://smoothcomp.com/es/events/upcoming"
        }
    ]

def main():
    hoy_iso = date.today().isoformat()
    print(f"🔄 Ejecutando actualización automática de torneos Smoothcomp + IBJJF España (Fecha actual: {hoy_iso})...")
    print("🎯 Filtros aplicados: Country = Spain (ES) | Smoothcomp (Gi/NoGi/ADCC) + Calendario Oficial IBJJF")

    # 1. Cargar torneos actuales si existen
    torneos_actuales = []
    if os.path.exists("torneos.json"):
        try:
            with open("torneos.json", "r", encoding="utf-8") as f:
                torneos_actuales = json.load(f)
        except Exception:
            torneos_actuales = []

    # 2. Combinar con el calendario oficial completo de España
    mapa_torneos = {t.get("id", t["nombre"]): normalizar_enlace_oficial(t) for t in obtener_calendario_oficial_base()}
    for t in torneos_actuales:
        t = normalizar_enlace_oficial(t)
        tid = t.get("id", t["nombre"])
        if tid not in mapa_torneos:
            mapa_torneos[tid] = t
        else:
            mapa_torneos[tid].update(t)
            mapa_torneos[tid] = normalizar_enlace_oficial(mapa_torneos[tid])

    # 3. Sumar eventos nuevos de Smoothcomp e IBJJF en vivo Y actualizar cambios de fecha/ciudad/enlace
    nuevos_sc = obtener_eventos_smoothcomp_espana()
    nuevos_ibjjf = obtener_eventos_ibjjf_espana()
    nuevos_totales = nuevos_sc + nuevos_ibjjf
    agregados_o_actualizados = 0

    indice_nombres = {t["nombre"].strip().lower(): tid for tid, t in mapa_torneos.items()}

    for ev in nuevos_totales:
        if not ev.get("fecha"):
            continue
        ev = normalizar_enlace_oficial(ev)
        nombre_norm = ev["nombre"].strip().lower()

        if ev["id"] in mapa_torneos:
            if (mapa_torneos[ev["id"]].get("fecha") != ev["fecha"] or
                mapa_torneos[ev["id"]].get("ciudad") != ev["ciudad"]):
                agregados_o_actualizados += 1
            mapa_torneos[ev["id"]]["fecha"] = ev["fecha"]
            mapa_torneos[ev["id"]]["ciudad"] = ev["ciudad"]
            mapa_torneos[ev["id"]]["enlace"] = ev["enlace"]
        elif nombre_norm in indice_nombres:
            tid_existente = indice_nombres[nombre_norm]
            if mapa_torneos[tid_existente].get("fecha") != ev["fecha"]:
                mapa_torneos[tid_existente]["fecha"] = ev["fecha"]
                agregados_o_actualizados += 1
            if ev.get("enlace"):
                mapa_torneos[tid_existente]["enlace"] = ev["enlace"]
        else:
            mapa_torneos[ev["id"]] = ev
            agregados_o_actualizados += 1

    # 4. Filtrar eventos vencidos (solo conservar fecha >= hoy_iso) y ordenar cronológicamente
    torneos_vigentes = [
        normalizar_enlace_oficial(t) for t in mapa_torneos.values()
        if t.get("fecha") and t["fecha"] >= hoy_iso
    ]
    torneos_vigentes.sort(key=lambda x: x.get("fecha", "9999-12-31"))

    # 5. Guardar torneos.json
    with open("torneos.json", "w", encoding="utf-8") as f:
        json.dump(torneos_vigentes, f, ensure_ascii=False, indent=2)

    # 6. Sincronizar FALLBACK_TORNEOS dentro de index.html y corregir cualquier fallback JS a Smoothcomp para IBJJF/AJP
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        torneos_js_str = json.dumps(torneos_vigentes, ensure_ascii=False)
        html_nuevo = re.sub(
            r'const FALLBACK_TORNEOS = \[.*?\];',
            lambda _: f'const FALLBACK_TORNEOS = {torneos_js_str};',
            html,
            flags=re.DOTALL
        )
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_nuevo)

    print(f"✅ ¡Listo! {len(torneos_vigentes)} torneos vigentes en España guardados en torneos.json e index.html (Nuevos o actualizados en vivo: {agregados_o_actualizados}).")

if __name__ == "__main__":
    main()
