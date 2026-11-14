from datetime import datetime
import json
import os
import re
import urllib.parse
import requests

ARCHIVO_JSON = "torneos.json"
ARCHIVO_HTML = "index.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

MESES_MAP = {
    "jan": "01",
    "ene": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "abr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "ago": "08",
    "sep": "09",
    "set": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
    "dic": "12",
}


def url_respaldo_espana(nombre, circuito="Smoothcomp"):
  q = urllib.parse.quote_plus(nombre)
  c = circuito.upper()
  if "IBJJF" in c:
    return "https://ibjjf.com/events/championships"
  if "AJP" in c:
    return "https://ajptour.com/en/events/upcoming"
  return f"https://smoothcomp.com/es/events/upcoming?search={q}&countries=ES"


TORNEOS_BASE = [
    {
        "id": "sc-green-capital-2026",
        "nombre": "Green Capital 2026 (Nordfighter)",
        "fecha": "2026-11-14",
        "ciudad": "Vitoria-Gasteiz",
        "recinto": "Polideportivo Vitoria-Gasteiz, Álava",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://smoothcomp.com/es/event/35054",
    },
    {
        "id": "sc-vinyols-challenge-fall-2026",
        "nombre": "Vinyols Challenge Fall 2026",
        "fecha": "2026-11-14",
        "ciudad": "Vinyols i els Arcs (Tarragona)",
        "recinto": "Pavelló Municipal Vinyols i els Arcs",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://smoothcomp.com/es/event/33733",
    },
    {
        "id": "sc-european-cup-guadalajara-2026",
        "nombre": "European Cup 2026 / Gi - No Gi / Kids",
        "fecha": "2026-11-15",
        "ciudad": "Guadalajara",
        "recinto": "Palacio Multiusos de Guadalajara",
        "circuito": "AEBJJ / FIJJD",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://spainbjjtour.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-bjjpro-zaragoza-2026",
        "nombre": "BJJPRO Zaragoza 2026 | Oso Duro (D-BJJ)",
        "fecha": "2026-11-15",
        "ciudad": "Zaragoza",
        "recinto": "Polideportivo Municipal Siglo XXI",
        "circuito": "D-BJJ / Oso Duro",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://dbjj.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-europe-cup-valencia-2026",
        "nombre": "Europe Cup BJJ 2026 (Spain BJJ Tour)",
        "fecha": "2026-11-21",
        "ciudad": "Valencia",
        "recinto": "Pabellón Municipal de Valencia (FIJJD)",
        "circuito": "AEBJJ / FIJJD",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://spainbjjtour.smoothcomp.com/es/event/34652",
    },
    {
        "id": "sc-open-cantabria-2026",
        "nombre": "Open Cantabria 2026 | Oso Duro (D-BJJ)",
        "fecha": "2026-11-21",
        "ciudad": "Soto de la Marina (Cantabria)",
        "recinto": "Polideportivo Soto de la Marina",
        "circuito": "D-BJJ / Oso Duro",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://dbjj.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-aranha-interclub-2026",
        "nombre": "Aranha Interclub 2026 (Niños & Adultos)",
        "fecha": "2026-11-28",
        "ciudad": "Barcelona",
        "recinto": "Sede Aranha BJJ Barcelona",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": (
            "https://smoothcomp.com/es/events/upcoming?search=Aranha+Interclub&countries=ES"
        ),
    },
    {
        "id": "torneo-madrid-autumn-2026",
        "nombre": "Madrid Autumn International Open IBJJF Championship",
        "fecha": "2026-11-28",
        "ciudad": "Madrid",
        "recinto": "Pabellón Deportivo Europa (Leganés)",
        "circuito": "IBJJF",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://ibjjf.com/events/championships",
    },
    {
        "id": "sc-spain-bjj-cup-sevilla-2026",
        "nombre": "Spain BJJ Cup Gi & No-Gi 2026 (Spain BJJ Tour)",
        "fecha": "2026-12-05",
        "ciudad": "Sevilla",
        "recinto": "Centro Deportivo Sevilla (FIJJD)",
        "circuito": "AEBJJ / FIJJD",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://spainbjjtour.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-grand-slam-baiona-2026",
        "nombre": "Grand Slam Baiona | D-BJJ",
        "fecha": "2026-12-05",
        "ciudad": "Baiona (Pontevedra)",
        "recinto": "Pabellón Municipal de Deportes de Baiona",
        "circuito": "D-BJJ / Oso Duro",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://dbjj.smoothcomp.com/es/event/34473",
    },
    {
        "id": "sc-bcn-challenge-winter-2026",
        "nombre": "BCN Challenge Winter 2026",
        "fecha": "2026-12-05",
        "ciudad": "El Papiol (Barcelona)",
        "recinto": "Pavelló Poliesportiu Municipal El Papiol",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://smoothcomp.com/es/event/32650",
    },
    {
        "id": "sc-wn-pro-opens-madrid-2026",
        "nombre": "WN Pro Opens - Madrid",
        "fecha": "2026-12-06",
        "ciudad": "Alcobendas (Madrid)",
        "recinto": "Polideportivo Alcobendas, Madrid",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": (
            "https://smoothcomp.com/es/events/upcoming?search=WN+Pro+Opens+Madrid&countries=ES"
        ),
    },
    {
        "id": "sc-campeonato-espana-adcc-2026",
        "nombre": "Campeonato de España ADCC",
        "fecha": "2026-12-12",
        "ciudad": "La Nucía (Alicante)",
        "recinto": "Ciutat Esportiva Camilo Cano (La Nucía)",
        "circuito": "ADCC",
        "modalidades": ["No-Gi"],
        "enlace": "https://adcc-spain.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-kimura-cup-zaragoza-2026",
        "nombre": "Kimura Cup Zaragoza 2026",
        "fecha": "2026-12-12",
        "ciudad": "Zaragoza",
        "recinto": "Pabellón Deportivo Zaragoza (Tour 26/27)",
        "circuito": "Kimura Cup",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://kimuracup.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-all-stars-bjj-madrid-2026",
        "nombre": "All Stars BJJ Madrid",
        "fecha": "2026-12-13",
        "ciudad": "Madrid",
        "recinto": "Pabellón Deportivo Madrid",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://allstarsbjj.smoothcomp.com/es/event/33644",
    },
    {
        "id": "sc-nacional-euskadi-2026",
        "nombre": "Nacional de Euskadi 2026 | Oso Duro",
        "fecha": "2026-12-13",
        "ciudad": "Zamudio (Vizcaya - Euskadi)",
        "recinto": "Polideportivo Zamudio",
        "circuito": "D-BJJ / Oso Duro",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://dbjj.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-ibiza-bjj-cup-2026",
        "nombre": "Ibiza BJJ Cup Gi & No-Gi 2026 (Spain BJJ Tour)",
        "fecha": "2026-12-19",
        "ciudad": "Santa Eulària des Riu (Ibiza)",
        "recinto": "Polideportivo Municipal Santa Eulària, Ibiza (FIJJD)",
        "circuito": "AEBJJ / FIJJD",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://spainbjjtour.smoothcomp.com/es/event/34443",
    },
    {
        "id": "sc-gsls-albacete-open-2026",
        "nombre": "GSLS Albacete International Open",
        "fecha": "2026-12-19",
        "ciudad": "Albacete",
        "recinto": "Pabellón Universitario de Albacete",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://gsl-spain.smoothcomp.com/es/event/33821",
    },
    {
        "id": "sc-dojjo-open-altea-2027",
        "nombre": "Dojjo Open Challenge Altea",
        "fecha": "2027-01-09",
        "ciudad": "Altea (Alicante)",
        "recinto": "Palau dels Esports Vila d'Altea",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": (
            "https://smoothcomp.com/es/events/upcoming?search=Dojjo+Open+Challenge+Altea&countries=ES"
        ),
    },
    {
        "id": "sc-cataluna-bjj-cup-2027",
        "nombre": "Cataluña BJJ Cup Gi & No-Gi 2027 (Spain BJJ Tour)",
        "fecha": "2027-01-09",
        "ciudad": "Castelldefels (Barcelona)",
        "recinto": "Poliesportiu Municipal Can Vinader (FIJJD)",
        "circuito": "AEBJJ / FIJJD",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://spainbjjtour.smoothcomp.com/es/event/34442",
    },
    {
        "id": "sc-euskadi-bjj-cup-2027",
        "nombre": "Euskadi BJJ Cup Gi & No-Gi 2027 (Spain BJJ Tour)",
        "fecha": "2027-01-30",
        "ciudad": "Legutio (Álava - Euskadi)",
        "recinto": "Polideportivo Municipal de Legutio (FIJJD)",
        "circuito": "AEBJJ / FIJJD",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://spainbjjtour.smoothcomp.com/es/event/35049",
    },
    {
        "id": "sc-kimura-cup-madrid-2027",
        "nombre": "Kimura Cup Madrid 2027",
        "fecha": "2027-01-31",
        "ciudad": "Arganda del Rey (Madrid)",
        "recinto": "Ciudad Deportiva Príncipe Felipe (Arganda del Rey)",
        "circuito": "Kimura Cup",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": "https://kimuracup.smoothcomp.com/es/events/upcoming",
    },
    {
        "id": "sc-polaris-open-madrid-2027",
        "nombre": "Polaris Open Spain - Madrid",
        "fecha": "2027-02-20",
        "ciudad": "Madrid",
        "recinto": "Centro Deportivo Amorós, Madrid",
        "circuito": "Polaris / Smoothcomp",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://polaris.smoothcomp.com/es/event/36137",
    },
    {
        "id": "sc-open-villanueva-rio-segura-2027",
        "nombre": "Open de Villanueva del Río Segura (Liga BJJ)",
        "fecha": "2027-02-20",
        "ciudad": "Villanueva del Río Segura (Murcia)",
        "recinto": "Pabellón Municipal Villanueva del Río Segura",
        "circuito": "Smoothcomp",
        "modalidades": ["Gi", "No-Gi", "Kids"],
        "enlace": (
            "https://smoothcomp.com/es/events/upcoming?search=Villanueva+del+Rio+Segura&countries=ES"
        ),
    },
    {
        "id": "torneo-spain-national-ajp-2027",
        "nombre": "AJP Tour Spain National Jiu-Jitsu Pro",
        "fecha": "2027-02-20",
        "ciudad": "Valencia",
        "recinto": "Velódromo Luis Puig",
        "circuito": "AJP Tour",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://ajptour.com/en/events/upcoming",
    },
    {
        "id": "torneo-madrid-spring-ibjjf-2027",
        "nombre": "Madrid Spring International Open IBJJF Championship",
        "fecha": "2027-03-27",
        "ciudad": "Madrid",
        "recinto": "Polideportivo Municipal Gallur",
        "circuito": "IBJJF",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://ibjjf.com/events/championships",
    },
    {
        "id": "sc-abierto-leon-dbjj-2027",
        "nombre": "Abierto de León | D-BJJ 2027",
        "fecha": "2027-04-24",
        "ciudad": "León",
        "recinto": "Palacio de los Deportes de León",
        "circuito": "D-BJJ / Oso Duro",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://smoothcomp.com/es/event/35370",
    },
    {
        "id": "torneo-barcelona-open-ibjjf-2027",
        "nombre": "Barcelona International Open IBJJF Championship",
        "fecha": "2027-05-15",
        "ciudad": "Barcelona",
        "recinto": "Complex Esportiu Municipal Mar Bella",
        "circuito": "IBJJF",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": "https://ibjjf.com/events/championships",
    },
    {
        "id": "sc-grappling-industries-madrid-2027",
        "nombre": "Grappling Industries Madrid (Round Robin)",
        "fecha": "2027-05-22",
        "ciudad": "Madrid",
        "recinto": "Pabellón Deportivo Madrid",
        "circuito": "Grappling Industries",
        "modalidades": ["Gi", "No-Gi"],
        "enlace": (
            "https://grapplingindustries.smoothcomp.com/es/events/upcoming"
        ),
    },
]


def parsear_fecha_sc(texto_fecha):
  if not texto_fecha:
    return None
  m_iso = re.search(r"(\d{4}-\d{2}-\d{2})", str(texto_fecha))
  if m_iso:
    return m_iso.group(1)
  m_txt = re.search(r"(\d{1,2})\s+([A-Za-z]{3})", str(texto_fecha))
  if m_txt:
    dia = m_txt.group(1).zfill(2)
    mes_str = m_txt.group(2).lower()[:3]
    mes = MESES_MAP.get(mes_str)
    if mes:
      hoy = datetime.utcnow()
      anio = hoy.year
      if int(mes) < hoy.month - 1:
        anio += 1
      return f"{anio}-{mes}-{dia}"
  return None


def descubrir_eventos_smoothcomp_espana():
  """Escanea Smoothcomp España y devuelve una lista de eventos encontrados en vivo."""
  encontrados = []
  url = "https://smoothcomp.com/es/events/upcoming?countries=ES"
  try:
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
      return encontrados

    # Buscar bloques JSON de eventos en el HTML de Smoothcomp
     patron_ev = re.compile(
        r'\{[^{}]*?"id"\s*:\s*(\d+)[^{}]*?"title"\s*:\s*"([^"]+)"[^{}]*?\}'
    )
    for match in patron_ev.finditer(r.text):
      bloque = match.group(0)
      ev_id = match.group(1)
      titulo = (
          match.group(2)
          .encode("utf-8")
          .decode("unicode_escape", errors="ignore")
          .strip()
      )

      url_ m = re.search(r'"url"\s*:\s*"([^"]+)"', bloque)
      link = (
          url_m.group(1).replace("\\/", "/")
          if url_m
          else f"https://smoothcomp.com/es/event/{ev_id}"
      )
      if "/en/event/" in link:
        link = link.replace("/en/event/", "/es/event/")

      city_m = re.search(r'"location_city"\s*:\s*"([^"]+)"', bloque)
      ciudad = (
          city_m.group(1)
          .encode("utf-8")
          .decode("unicode_escape", errors="ignore")
          .strip()
          if city_m
          else "España"
      )

      date_m = re.search(
          r'"(?:startdate|datestart|date)"\s*:\s*"([^"]+)"', bloque
      )
      fecha_iso = parsear_fecha_sc(date_m.group(1)) if date_m else None

      encontrados.append({
          "id": f"sc-auto-{ev_id}",
          "event_id": ev_id,
          "nombre": titulo,
          "fecha": fecha_iso,
          "ciudad": ciudad,
          "recinto": f"{ciudad} (Smoothcomp Oficial)",
          "circuito": "Smoothcomp",
          "modalidades": ["Gi", "No-Gi"],
          "enlace": link,
      })
  except Exception as e:
    print(f"Aviso en escaneo vivo de Smoothcomp: {e}")
  return encontrados


def main():
  eventos_vivos = descubrir_eventos_smoothcomp_espana()
  print(
      f"Eventos en España detectados en vivo en Smoothcomp: {len(eventos_vivos)}"
  )

  torneos_finales = []
  ids_usados = set()
  nombres_usados = set()

  # 1. Procesar y enriquecer los torneos base
  for t in TORNEOS_BASE:
    item = dict(t)
    nom_low = item["nombre"].lower()
    enlace_actual = item.get("enlace", "")

    for ev in eventos_vivos:
      ev_nom = ev["nombre"].lower()
      if ev_nom in nom_low or nom_low in ev_nom:
        item["enlace"] = ev["enlace"]
        ids_usados.add(ev["event_id"])
        break

    if not item.get("enlace"):
      item["enlace"] = url_respaldo_espana(item["nombre"], item["circuito"])

    m_id = re.search(r"/event/(\d+)", item["enlace"])
    if m_id:
      ids_usados.add(m_id.group(1))

    nombres_usados.add(nom_low)
    torneos_finales.append(item)

  # 2. Agregar automáticamente cualquier torneo nuevo publicado en España con fecha válida
  nuevos_agregados = 0
  for ev in eventos_vivos:
    ev_nom = ev["nombre"].lower()
    if (
        ev["event_id"] not in ids_usados
        and ev_nom not in nombres_usados
        and ev["fecha"]
    ):
      torneos_finales.append({
          "id": ev["id"],
          "nombre": ev["nombre"],
          "fecha": ev["fecha"],
          "ciudad": ev["ciudad"],
          "recinto": ev["recinto"],
          "circuito": ev["circuito"],
          "modalidades": ev["modalidades"],
          "enlace": ev["enlace"],
      })
      ids_usados.add(ev["event_id"])
      nombres_usados.add(ev_nom)
      nuevos_agregados += 1

  print(
      f"Torneos nuevos auto-agregados desde Smoothcomp España: {nuevos_agregados}"
  )

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
        flags=re.DOTALL,
    )
    with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
      f.write(html_nuevo)

  print(
      f"Exito! Total de {len(torneos_finales)} torneos guardados en"
      f" {ARCHIVO_JSON} e {ARCHIVO_HTML}."
  )


if __name__ == "__main__":
  main()
