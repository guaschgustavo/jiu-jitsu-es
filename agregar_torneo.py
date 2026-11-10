import json
import os
import re

def main():
    print("="*62)
    print(" 🏆 AGREGAR NUEVO TORNEO MANUALMENTE - JIU-JITSU.ES")
    print("="*62)
    nombre = input("Nombre del Torneo (ej. Copa Valencia BJJ): ").strip()
    fecha = input("Fecha en formato AAAA-MM-DD (ej. 2027-04-10): ").strip()
    ciudad = input("Ciudad (ej. Valencia): ").strip()
    recinto = input("Recinto / Pabellón (ej. Velódromo Luis Puig): ").strip()
    circuito = input("Circuito (IBJJF / AJP Tour / ADCC / AEBJJ / Open) [Open]: ").strip() or "Open"
    mods_raw = input("Modalidades separadas por coma [Gi, No-Gi]: ").strip()
    modalidades = [m.strip() for m in mods_raw.split(",") if m.strip()] if mods_raw else ["Gi", "No-Gi"]
    enlace = input("Link de inscripción (Smoothcomp / IBJJF / AJP): ").strip() or "https://smoothcomp.com/en/events/upcoming"

    if os.path.exists("torneos.json"):
        with open("torneos.json", "r", encoding="utf-8") as f:
            torneos = json.load(f)
    else:
        torneos = []

    nuevo_id = f"torneo-{len(torneos)+1:02d}-{fecha}"
    torneos.append({
        "id": nuevo_id,
        "nombre": nombre,
        "fecha": fecha,
        "ciudad": ciudad,
        "recinto": recinto,
        "circuito": circuito,
        "modalidades": modalidades,
        "enlace": enlace
    })

    torneos.sort(key=lambda x: x.get("fecha", "9999-12-31"))

    with open("torneos.json", "w", encoding="utf-8") as f:
        json.dump(torneos, f, ensure_ascii=False, indent=2)

    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        torneos_js_str = json.dumps(torneos, ensure_ascii=False)
        html_nuevo = re.sub(
            r'const FALLBACK_TORNEOS = \[.*?\];',
            lambda _: f'const FALLBACK_TORNEOS = {torneos_js_str};',
            html
        )
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_nuevo)

    print(f"\n✅ Torneo '{nombre}' ({fecha}) agregado y ordenado exitosamente.")
    input("Presioná ENTER para salir...")

if __name__ == "__main__":
    main()
