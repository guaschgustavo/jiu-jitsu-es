import json
import os
import html
from datetime import date

CIUDADES_TOP_5 = [
    {
        "slug": "madrid",
        "nombre": "Madrid",
        "titulo": "Academias de Jiu-Jitsu Brasileño (BJJ) en Madrid | Mapa y Clases",
        "descripcion": "Encuentra dónde entrenar Jiu-Jitsu Brasileño (BJJ) y Grappling en Madrid y alrededores. Mapa interactivo, academias verificadas, horarios y próximos torneos.",
        "lat": 40.4168,
        "lng": -3.7038,
        "zoom": 11,
        "match_provincias": ["madrid"],
        "match_ciudades": ["madrid", "las-rozas-de-madrid", "alcobendas", "mostoles", "leganes", "arganda"]
    },
    {
        "slug": "barcelona",
        "nombre": "Barcelona",
        "titulo": "Academias de Jiu-Jitsu Brasileño (BJJ) en Barcelona | Mapa y Clases",
        "descripcion": "Directorio oficial de academias de BJJ y Grappling en Barcelona, Badalona, Sabadell y Terrassa. Consulta el mapa, profesores y calendario de torneos.",
        "lat": 41.3874,
        "lng": 2.1686,
        "zoom": 11,
        "match_provincias": ["barcelona"],
        "match_ciudades": ["barcelona", "badalona", "sabadell", "terrassa", "castelldefels", "el-papiol"]
    },
    {
        "slug": "valencia",
        "nombre": "Valencia",
        "titulo": "Academias de Jiu-Jitsu Brasileño (BJJ) en Valencia | Mapa y Clases",
        "descripcion": "Descubre las mejores escuelas de Jiu-Jitsu Brasileño (Gi y No-Gi) en Valencia. Mapa interactivo, clases de prueba gratis y torneos en la Comunidad Valenciana.",
        "lat": 39.4699,
        "lng": -0.3763,
        "zoom": 12,
        "match_provincias": ["valencia"],
        "match_ciudades": ["valencia", "quart-de-poblet"]
    },
    {
        "slug": "sevilla",
        "nombre": "Sevilla",
        "titulo": "Academias de Jiu-Jitsu Brasileño (BJJ) en Sevilla | Mapa y Clases",
        "descripcion": "Dónde entrenar Jiu-Jitsu Brasileño y Grappling en Sevilla. Listado de academias verificadas, mapa interactivo y próximas competiciones en Andalucía.",
        "lat": 37.3891,
        "lng": -5.9845,
        "zoom": 12,
        "match_provincias": ["sevilla"],
        "match_ciudades": ["sevilla"]
    },
    {
        "slug": "malaga",
        "nombre": "Málaga",
        "titulo": "Academias de Jiu-Jitsu Brasileño (BJJ) en Málaga | Mapa y Clases",
        "descripcion": "Directorio de academias de BJJ en Málaga, Marbella, Torremolinos y Fuengirola. Encuentra clases de Gi, No-Gi, MMA y competición cerca de ti.",
        "lat": 36.7213,
        "lng": -4.4214,
        "zoom": 10,
        "match_provincias": ["málaga", "malaga"],
        "match_ciudades": ["malaga", "torremolinos", "marbella", "fuengirola", "antequera"]
    }
]

def cargar_json(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def filtrar_academias(academias, cfg):
    resultado = []
    for a in academias:
        prov = str(a.get("provincia", "")).strip().lower()
        c_slug = str(a.get("ciudad_slug", "")).strip().lower()
        ciudad = str(a.get("ciudad", "")).strip().lower()
        if (prov in cfg["match_provincias"] or
            c_slug in cfg["match_ciudades"] or
            any(m in ciudad for m in cfg["match_ciudades"])):
            resultado.append(a)
    # Ordenar: destacadas primero, luego por rating
    resultado.sort(key=lambda x: (not x.get("destacada_premium", False), -(x.get("rating", {}).get("valor", 0))))
    return resultado

def filtrar_torneos(torneos, cfg):
    hoy = date.today().isoformat()
    resultado = []
    for t in torneos:
        if t.get("fecha", "") < hoy:
            continue
        texto = f"{t.get('ciudad', '')} {t.get('recinto', '')} {t.get('nombre', '')}".lower()
        if any(m in texto for m in cfg["match_ciudades"] + cfg["match_provincias"]):
            resultado.append(t)
    resultado.sort(key=lambda x: x.get("fecha", "9999-12-31"))
    return resultado

def generar_html_ciudad(cfg, academias_ciudad, torneos_ciudad):
    nombre = cfg["nombre"]
    slug = cfg["slug"]
    url_canonica = f"https://jiu-jitsu.es/{slug}/"

    # Tarjetas de academias
    cards_html = []
    marcadores = []
    for a in academias_ciudad:
        nom = html.escape(a.get("nombre", ""))
        dir_txt = html.escape(a.get("direccion", ""))
        coach = html.escape(a.get("head_coach", "Instructor Certificado"))
        horarios = html.escape(a.get("horarios_resumen", "Consultar horarios"))
        mods = "".join(
            f'<span class="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">{html.escape(m)}</span>'
            for m in a.get("modalidades", [])
        )
        rating = a.get("rating", {}).get("valor", 4.9)
        contacto = a.get("contacto", {})
        wa = contacto.get("whatsapp", "")
        web = contacto.get("web", "")

        btn_wa = f'<a href="https://wa.me/{wa}" target="_blank" rel="noopener" class="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition">WhatsApp</a>' if wa else ""
        btn_web = f'<a href="{html.escape(web)}" target="_blank" rel="noopener" class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold border border-slate-700 transition">Web / Info ↗</a>' if web else ""

        cards_html.append(f"""
        <article class="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-amber-500/40 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">{html.escape(a.get("ciudad", nombre))}</span>
              <span class="text-xs font-semibold text-amber-400">★ {rating}</span>
            </div>
            <h3 class="text-lg font-bold text-white mb-1">{nom}</h3>
            <p class="text-xs text-slate-400 mb-2">🥋 Coach: {coach}</p>
            <p class="text-xs text-slate-400 mb-3">📍 {dir_txt}</p>
            <p class="text-xs text-slate-500 mb-3">🕒 {horarios}</p>
            <div class="flex flex-wrap gap-1.5 mb-4">{mods}</div>
          </div>
          <div class="pt-3 border-t border-slate-800 flex items-center gap-2">
            {btn_wa}
            {btn_web}
          </div>
        </article>
        """)

        coords = a.get("coordenadas", {})
        if coords.get("lat") and coords.get("lng"):
            marcadores.append({
                "nombre": a.get("nombre", ""),
                "lat": coords["lat"],
                "lng": coords["lng"],
                "direccion": a.get("direccion", "")
            })

    # Tarjetas de torneos locales
    if torneos_ciudad:
        torneos_html = "".join(f"""
        <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold uppercase px-2 py-0.5 rounded bg-amber-500/10 text-amber-400">{html.escape(t.get("circuito", "BJJ"))}</span>
              <span class="text-xs text-slate-300">📅 {html.escape(t.get("fecha", ""))}</span>
            </div>
            <h3 class="text-base font-bold text-white mb-1">{html.escape(t.get("nombre", ""))}</h3>
            <p class="text-xs text-slate-400 mb-3">📍 {html.escape(t.get("recinto", nombre))}</p>
          </div>
          <a href="{html.escape(t.get("enlace", "https://jiu-jitsu.es/#torneos"))}" target="_blank" rel="noopener" class="text-xs font-bold text-amber-400 hover:text-amber-300">Calendario Oficial ↗</a>
        </div>
        """ for t in torneos_ciudad)
    else:
        torneos_html = f'<p class="text-sm text-slate-400 col-span-full">No hay torneos confirmados próximamente en {nombre}. <a href="/#torneos" class="text-amber-400 underline">Ver los 29 torneos en toda España →</a></p>'

    # Enlaces a las otras ciudades
    otras_ciudades = "".join(
        f'<a href="/{c["slug"]}/" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-amber-500/50 text-xs font-semibold text-slate-300 hover:text-amber-400 transition">BJJ en {c["nombre"]}</a>'
        for c in CIUDADES_TOP_5 if c["slug"] != slug
    )

    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Academias de Jiu-Jitsu Brasileño en {nombre}",
        "url": url_canonica,
        "numberOfItems": len(academias_ciudad),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": a.get("nombre", ""),
                "url": a.get("contacto", {}).get("web") or url_canonica
            }
            for i, a in enumerate(academias_ciudad)
        ]
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(cfg["titulo"])}</title>
  <meta name="description" content="{html.escape(cfg["descripcion"])}">
  <link rel="canonical" href="{url_canonica}">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script type="application/ld+json">{schema_json}</script>
  <style>
    .leaflet-tile-pane {{ filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">

  <header class="border-b border-slate-800 bg-slate-950/90 sticky top-0 z-50 backdrop-blur">
    <div class="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
      <a href="/" class="text-xl font-black tracking-tight text-white">JIU-JITSU<span class="text-sky-400">.ES</span></a>
      <nav class="flex items-center gap-4 text-xs sm:text-sm font-semibold text-slate-300">
        <a href="/" class="hover:text-amber-400 transition">Directorio España</a>
        <a href="/#torneos" class="hover:text-amber-400 transition">Torneos</a>
        <a href="/#calculadora" class="hover:text-amber-400 transition">Pesos IBJJF</a>
      </nav>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 py-10 flex-1 w-full">
    <nav class="text-xs text-slate-400 mb-4">
      <a href="/" class="hover:text-amber-400">Inicio</a> / <span class="text-slate-200">Academias BJJ en {nombre}</span>
    </nav>

    <h1 class="text-3xl sm:text-4xl font-black text-white mb-3">
      Academias de Jiu-Jitsu Brasileño (BJJ) en <span class="text-amber-400">{nombre}</span>
    </h1>
    <p class="text-slate-400 text-sm sm:text-base max-w-3xl mb-8">
      Encuentra dónde entrenar Gi, No-Gi y Grappling en {nombre} y su área metropolitana. Actualmente listamos <strong class="text-white">{len(academias_ciudad)} academias verificadas</strong> con ubicación exacta y contacto directo.
    </p>

    <section class="mb-10">
      <div id="mapa-ciudad" class="w-full h-80 sm:h-96 rounded-2xl border border-slate-800 z-10"></div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-bold text-white mb-5">Listado de Academias en {nombre}</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {"".join(cards_html)}
      </div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-bold text-white mb-5">Próximos Torneos de BJJ en {nombre}</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {torneos_html}
      </div>
    </section>

    <section class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 mb-10">
      <h2 class="text-lg font-bold text-white mb-3">Preguntas frecuentes sobre entrenar BJJ en {nombre}</h2>
      <div class="space-y-3 text-sm text-slate-400">
        <p><strong class="text-slate-200">¿Puedo probar una clase gratis?</strong> La mayoría de las academias de {nombre} en nuestro directorio ofrecen una primera clase de prueba sin compromiso para principiantes.</p>
        <p><strong class="text-slate-200">¿Necesito kimono (Gi) el primer día?</strong> No hace falta comprar un Gi antes de empezar; muchas escuelas prestan kimono o te permiten probar en clase de No-Gi (Grappling) con ropa deportiva.</p>
        <p><strong class="text-slate-200">¿Falta tu academia en {nombre}?</strong> <a href="/" class="text-amber-400 underline">Envíanos los datos gratis desde la portada de JIU-JITSU.ES</a>.</p>
      </div>
    </section>

    <section class="border-t border-slate-800 pt-8">
      <h3 class="text-sm font-bold text-slate-300 mb-3">Explorar otras ciudades de España:</h3>
      <div class="flex flex-wrap gap-2">
        {otras_ciudades}
        <a href="/" class="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs font-bold text-amber-400 hover:bg-amber-500/20 transition">Ver mapa completo de España →</a>
      </div>
    </section>
  </main>

  <footer class="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
    © 2026 JIU-JITSU.ES — Directorio Oficial de Jiu-Jitsu Brasileño y Grappling en España
  </footer>

  <script>
    const marcadores = {json.dumps(marcadores, ensure_ascii=False)};
    const map = L.map('mapa-ciudad').setView([{cfg["lat"]}, {cfg["lng"]}], {cfg["zoom"]});
    L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '© OpenStreetMap contributors'
    }}).addTo(map);
    marcadores.forEach(m => {{
      L.marker([m.lat, m.lng]).addTo(map).bindPopup(`<b>${{m.nombre}}</b><br>${{m.direccion}}`);
    }});
  </script>
</body>
</html>
"""

def actualizar_sitemap():
    hoy = date.today().isoformat()
    urls = ["https://jiu-jitsu.es/"] + [f"https://jiu-jitsu.es/{c['slug']}/" for c in CIUDADES_TOP_5]
    bloques = "\n".join(f"""  <url>
    <loc>{u}</loc>
    <lastmod>{hoy}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{"1.0" if u == "https://jiu-jitsu.es/" else "0.8"}</priority>
  </url>""" for u in urls)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{bloques}
</urlset>
"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml)

def main():
    academias = cargar_json("academias.json")
    torneos = cargar_json("torneos.json")

    for cfg in CIUDADES_TOP_5:
        os.makedirs(cfg["slug"], exist_ok=True)
        ac_ciudad = filtrar_academias(academias, cfg)
        to_ciudad = filtrar_torneos(torneos, cfg)
        html_out = generar_html_ciudad(cfg, ac_ciudad, to_ciudad)
        with open(os.path.join(cfg["slug"], "index.html"), "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"✅ Generado /{cfg['slug']}/index.html ({len(ac_ciudad)} academias, {len(to_ciudad)} torneos)")

    actualizar_sitemap()
    print("✅ sitemap.xml actualizado con las 5 ciudades principales.")

if __name__ == "__main__":
    main()
