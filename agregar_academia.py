import json
import os
import re
import unicodedata

def slugify(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s-]+', '-', text)

def limpiar_valor(linea):
    if ':' in linea:
        val = linea.split(':', 1)[1].strip()
        return val.replace('*', '').strip()
    return ''

def main():
    print("="*62)
    print(" 🥋 GESTOR AUTOMÁTICO DE ALTA DE ACADEMIAS - JIU-JITSU.ES")
    print("="*62)
    print("\nPegá acá abajo el mensaje completo que te llegó por WhatsApp.")
    print("(Cuando termines de pegar el texto, presioná ENTER en una línea vacía):\n")

    lineas = []
    while True:
        try:
            linea = input()
        except EOFError:
            break
        if linea.strip() == "" and len(lineas) >= 3:
            break
        if linea.strip() != "":
            lineas.append(linea.strip())

    datos = {
        "nombre": "",
        "ciudad": "",
        "afiliacion": "",
        "head_coach": "",
        "direccion": "",
        "telefono": "",
        "instagram": "",
        "web": ""
    }

    for l in lineas:
        l_low = l.lower()
        if "academia:" in l_low:
            datos["nombre"] = limpiar_valor(l)
        elif "ciudad:" in l_low:
            datos["ciudad"] = limpiar_valor(l)
        elif "equipo" in l_low or "filial:" in l_low:
            datos["afiliacion"] = limpiar_valor(l)
        elif "coach:" in l_low:
            datos["head_coach"] = limpiar_valor(l)
        elif "direcci" in l_low:
            datos["direccion"] = limpiar_valor(l)
        elif "whatsapp" in l_low or "tel:" in l_low:
            datos["telefono"] = limpiar_valor(l)
        elif "instagram:" in l_low:
            datos["instagram"] = limpiar_valor(l)
        elif "web" in l_low:
            datos["web"] = limpiar_valor(l)

    print("\n--- Verificación de datos leídos (presioná ENTER para aceptar el valor entre corchetes) ---")
    nombre = input(f"Nombre de la Academia [{datos['nombre']}]: ").strip() or datos['nombre']
    ciudad = input(f"Ciudad [{datos['ciudad']}]: ").strip() or datos['ciudad']
    provincia = input(f"Provincia (ej. Madrid, Islas Baleares - Ibiza, Valencia) [{ciudad}]: ").strip() or ciudad
    afiliacion = input(f"Equipo / Filial [{datos['afiliacion']}]: ").strip() or datos['afiliacion']
    if afiliacion.lower() in ["no especificada", "no especificado", ""]:
        afiliacion = nombre

    head_coach = input(f"Head Coach [{datos['head_coach']}]: ").strip() or datos['head_coach']
    direccion = input(f"Dirección Completa [{datos['direccion']}]: ").strip() or datos['direccion']
    
    # Extraer codigo postal de la direccion si tiene 5 digitos seguidos
    cp_match = re.search(r'\b(\d{5})\b', direccion)
    cp_default = cp_match.group(1) if cp_match else "28000"
    codigo_postal = input(f"Código Postal [{cp_default}]: ").strip() or cp_default

    telefono = input(f"Teléfono / WhatsApp [{datos['telefono']}]: ").strip() or datos['telefono']
    tiene_wa = input("¿Este número tiene WhatsApp activo? (s/n) [s]: ").strip().lower() or 's'
    whatsapp_num = re.sub(r'[^0-9]', '', telefono) if tiene_wa == 's' else ""
    if whatsapp_num and len(whatsapp_num) == 9 and whatsapp_num[0] in ['6', '7']:
        whatsapp_num = "34" + whatsapp_num

    ig_default = datos['instagram'] if datos['instagram'].lower() != 'no especificado' else ''
    instagram = input(f"Instagram [{ig_default}]: ").strip() or ig_default
    if instagram and not instagram.startswith('@'):
        instagram = '@' + instagram

    web_default = datos['web'] if datos['web'].lower() != 'no especificada' else ''
    web = input(f"Página Web [{web_default}]: ").strip() or web_default
    if web and not web.startswith('http'):
        web = 'https://' + web

    print("\n📍 Coordenadas de Google Maps:")
    print("(Buscá la dirección en Google Maps, hacé clic derecho sobre el local y copiá los números)")
    coords_raw = input("Pegá las coordenadas acá (ej. 40.4251, -3.7082): ").strip()
    try:
        partes = [ float(x.strip()) for x in coords_raw.replace(';', ',').split(',') ]
        lat, lng = partes[0], partes[1]
    except Exception:
        print("⚠️ Formato no reconocido, se usarán coordenadas del centro de Madrid por defecto (40.4168, -3.7038).")
        lat, lng = 40.4168, -3.7038

    mods_raw = input("Modalidades separadas por coma [Gi, No-Gi, Kids, Competición]: ").strip()
    if mods_raw:
        modalidades = [m.strip() for m in mods_raw.split(',') if m.strip()]
    else:
        modalidades = ["Gi", "No-Gi", "Kids", "Competición"]

    rating_val = input("Puntuación en Google Maps [5.0]: ").strip()
    rating_val = float(rating_val) if rating_val else 5.0
    resenas_cnt = input("Cantidad de reseñas [30]: ").strip()
    resenas_cnt = int(resenas_cnt) if resenas_cnt else 30

    destacada_in = input("¿Es Academia Destacada ★ Premium? (s/n) [n]: ").strip().lower()
    destacada = True if destacada_in == 's' else False

    json_path = "academias.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            academias = json.load(f)
    else:
        academias = []

    ciudad_slug = slugify(ciudad.split('(')[0])
    academia_slug = slugify(f"{nombre}-{ciudad_slug}")
    nuevo_id = f"bjj-{ciudad_slug}-{len(academias) + 1:02d}"

    nueva_academia = {
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
        "afiliacion": afiliacion,
        "head_coach": head_coach,
        "modalidades": modalidades,
        "horarios_resumen": "Lunes a Viernes: Mañanas y Tardes | Sábados: Open Mat",
        "clase_prueba_gratis": True,
        "contacto": {
            "telefono": telefono,
            "whatsapp": whatsapp_num,
            "web": web,
            "instagram": instagram
        },
        "rating": {
            "valor": rating_val,
            "resenas_count": resenas_cnt
        },
        "verificada": True,
        "destacada_premium": destacada,
        "descripcion_seo": f"Entrena en {nombre}, academia de Jiu-Jitsu Brasileño (BJJ) y Grappling en {ciudad}."
    }

    academias.append(nueva_academia)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(academias, f, ensure_ascii=False, indent=2)

    # Actualizar GeoJSON automáticamente
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
    with open("academias.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    # Actualizar también el FALLBACK_ACADEMIAS embebido dentro de index.html si existe
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        academias_js_str = json.dumps(academias, ensure_ascii=False)
        html_nuevo = re.sub(
            r'const FALLBACK_ACADEMIAS = \[.*?\];',
            lambda _: f'const FALLBACK_ACADEMIAS = {academias_js_str};',
            html
        )
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_nuevo)

    print("\n" + "="*62)
    print(f"✅ ¡ÉXITO! '{nombre}' fue agregada correctamente.")
    print(f"📊 Total de academias en el portal: {len(academias)}")
    print("📁 Se actualizaron automáticamente: academias.json, academias.geojson e index.html")
    print("="*62)
    input("\nPresioná ENTER para cerrar...")

if __name__ == "__main__":
    main()
