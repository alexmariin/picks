"""Cuotas REALES de Winamax (winamax.es) leyendo su web pública. No gasta consultas de ninguna API.

La página de Winamax trae todos sus mercados dentro (PRELOADED_STATE): remates y remates a puerta de cada
jugador, goleador, tarjeta de un jugador, remates y remates a puerta por equipo, córners, tarjetas, etc.

Uso (desde la raíz del repo):
    python3 winamax.py partidos [texto]             -> partidos de fútbol de HOY (hora de España) con su id
    python3 winamax.py mercados <id>                -> lista de todos los mercados de ese partido (solo títulos)
    python3 winamax.py mercados <id> <texto> [...]  -> cuotas de los mercados cuyo título contiene ese texto
        ej.: python3 winamax.py mercados 68932056 "remates a puerta" "tiros a puerta por" goleador tarjetas córneres
    python3 winamax.py volcar                       -> guarda los mercados clave (remates, remates a puerta, goleador,
        tarjeta de jugador, tiros por equipo, córners, tarjetas) de los partidos grandes de hoy
Lo que imprimas con <texto> se guarda en data/cuotas/AAAA-MM-DD-winamax.json (para medir después).
OJO: la red de la rutina en la nube NO llega a winamax.es. Allí, lee data/cuotas/AAAA-MM-DD-winamax.json,
que sube el PC del usuario por la mañana con `volcar` (formato: partidos -> mercados -> [[opción, cuota], ...]).

Pide como mucho una página cada 2 segundos y solo los partidos que vayas a analizar.
En mercados de jugador la cuota es de un solo lado (no hay "no lo hace"), así que no hay probabilidad justa:
1/cuota es lo que dice Winamax CON su margen (que en estos mercados suele ser del 8-15 %).
"""
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).parent
WEB = "https://www.winamax.es/apuestas-deportivas"
MADRID = ZoneInfo("Europe/Madrid")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
_ultima = [0.0]


def estado(ruta):
    espera = 2 - (time.time() - _ultima[0])
    if espera > 0:
        time.sleep(espera)
    _ultima[0] = time.time()
    req = urllib.request.Request(f"{WEB}{ruta}", headers={"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=40) as r:
        html = r.read().decode("utf-8", "replace")
    marca = "PRELOADED_STATE = "
    i = html.find(marca)
    if i < 0:
        sys.exit("Winamax no ha devuelto sus datos (¿bloqueo o cambio de web?). Usa webs de cuotas o estima la cuota.")
    return json.JSONDecoder().raw_decode(html[i + len(marca):])[0]


def hora(ts):
    return datetime.fromtimestamp(ts, MADRID)


def partidos(texto=""):
    st = estado("/sports/1")
    hoy = datetime.now(MADRID).date()
    t = texto.lower()
    filas = []
    for m in st.get("matches", {}).values():
        if m.get("sportId") != 1 or not m.get("matchStart") or not m.get("competitor2Name"):
            continue
        if hora(m["matchStart"]).date() != hoy or (t and t not in m.get("title", "").lower()):
            continue
        torneo = st.get("tournaments", {}).get(str(m.get("tournamentId")), {}).get("tournamentName", "")
        filas.append((m["matchStart"], m["matchId"], m["title"], torneo, m.get("moreBets")))
    for ts, mid, titulo, torneo, n in sorted(filas):
        print(f"{hora(ts):%H:%M}  id {mid}  {titulo}  ·  {torneo}  ·  {n or '?'} mercados")
    if not filas:
        print("No hay partidos de hoy con ese texto en la portada de fútbol de Winamax.")
        print("Si el partido existe, busca su id en la web de Winamax (sale en la dirección: /match/<id>).")


def mercados(mid, textos):
    st = estado(f"/match/{mid}")
    m = st.get("matches", {}).get(str(mid))
    if not m:
        sys.exit(f"Winamax no tiene el partido {mid}.")
    bets = [b for b in st.get("bets", {}).values() if b.get("matchId") == int(mid) and b.get("available", True)]
    print(f"== {m['title']} · {hora(m['matchStart']):%d/%m %H:%M} · {len(bets)} mercados · "
          f"alineaciones oficiales: {'sí' if m.get('officialLineups') else 'aún no'}")
    if not textos:
        vistos = {}
        for b in bets:
            vistos[b["betTitle"]] = vistos.get(b["betTitle"], 0) + 1
        for titulo, n in vistos.items():
            print(f"  {titulo}" + (f"  ({n} líneas)" if n > 1 else ""))
        return
    guardar = {}
    for b in bets:
        titulo = b["betTitle"]
        if not any(x.lower() in titulo.lower() for x in textos):
            continue
        filas = []
        for o in b.get("outcomes", []):
            out, cuota = st.get("outcomes", {}).get(str(o), {}), st.get("odds", {}).get(str(o))
            if not cuota or not out.get("available", True):
                continue
            equipo = {1: m.get("competitor1Name"), 2: m.get("competitor2Name")}.get(out.get("team"), "")
            filas.append({"opcion": out.get("label", ""), "equipo": equipo, "cuota": cuota})
        if not filas:
            continue
        guardar.setdefault(titulo, []).extend(filas)
        print(f"  [{titulo}]")
        for f in sorted(filas, key=lambda f: f["cuota"]):
            print(f"     {f['opcion']}{' (' + f['equipo'] + ')' if f['equipo'] else ''}: {f['cuota']}  (Winamax dice {1 / f['cuota']:.0%} con margen)")
    if not guardar:
        print("Ningún mercado contiene ese texto. Ejecuta sin texto para ver la lista de títulos.")
        return
    hoy = datetime.now(MADRID).date().isoformat()
    archivo = BASE / "data" / "cuotas" / f"{hoy}-winamax.json"
    datos = json.loads(archivo.read_text(encoding="utf-8")) if archivo.exists() else {"fecha": hoy, "partidos": {}}
    p = datos["partidos"].setdefault(str(mid), {"partido": m["title"], "mercados": {}})
    p["pedido"] = datetime.now(MADRID).strftime("%H:%M")
    p["mercados"].update(guardar)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nGuardado en {archivo.relative_to(BASE)}")


CLAVE = {"Realiza 1 o más remates a puerta", "Realiza 2 o más remates a puerta", "Realiza 1 o más remates",
         "Realiza 2 o más remates", "Realiza 3 o más remates", "Goleador", "El jugador recibe una o más tarjetas",
         "Número total córneres", "Número total de tarjetas", "Córneres - Resultado", "Hándicap asiático córner",
         "Tiros a puerta - Resultado", "Tiros - Resultado"}


def clave(titulo):
    t = titulo.strip()
    return t in CLAVE or t.startswith("Número de tiros") or t.startswith("Número total córneres ")


def volcar(maximo=25):
    """Para el PC del usuario: guarda los mercados clave de los partidos grandes de hoy en data/cuotas/AAAA-MM-DD-winamax.json."""
    st = estado("/sports/1")
    hoy = datetime.now(MADRID).date()
    ahora = datetime.now(MADRID).timestamp()
    lista = [m for m in st.get("matches", {}).values()
             if m.get("sportId") == 1 and m.get("competitor2Name") and m.get("matchStart", 0) > ahora
             and hora(m["matchStart"]).date() == hoy and (m.get("moreBets") or 0) >= 150]
    lista = sorted(lista, key=lambda m: -(m.get("moreBets") or 0))[:maximo]
    datos = {"fecha": hoy.isoformat(), "generado": datetime.now(MADRID).strftime("%H:%M"), "partidos": {}}
    for m in sorted(lista, key=lambda m: m["matchStart"]):
        try:
            sm = estado(f"/match/{m['matchId']}")
        except OSError as e:
            print(f"{m['title']}: error {e}")
            continue
        torneo = st.get("tournaments", {}).get(str(m.get("tournamentId")), {}).get("tournamentName", "")
        p = {"partido": m["title"], "torneo": torneo, "hora": f"{hora(m['matchStart']):%H:%M}", "mercados": {}}
        for b in sm.get("bets", {}).values():
            if b.get("matchId") != m["matchId"] or not b.get("available", True) or not clave(b["betTitle"]):
                continue
            for o in b.get("outcomes", []):
                out, cuota = sm.get("outcomes", {}).get(str(o), {}), sm.get("odds", {}).get(str(o))
                if cuota and out.get("available", True):
                    eq = {1: m.get("competitor1Name"), 2: m.get("competitor2Name")}.get(out.get("team"))
                    p["mercados"].setdefault(b["betTitle"].strip(), []).append(
                        [out.get("label", "").strip() + (f" ({eq})" if eq else ""), cuota])
        datos["partidos"][str(m["matchId"])] = p
        print(f"{p['hora']} {p['partido']} · {torneo} · {len(p['mercados'])} mercados guardados")
    archivo = BASE / "data" / "cuotas" / f"{hoy.isoformat()}-winamax.json"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Guardado en {archivo.relative_to(BASE)} ({archivo.stat().st_size // 1024} KB)")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("partidos", "mercados", "volcar"):
        sys.exit(__doc__)
    try:
        if sys.argv[1] == "volcar":
            volcar()
        elif sys.argv[1] == "partidos":
            partidos(" ".join(sys.argv[2:]))
        else:
            if len(sys.argv) < 3:
                sys.exit(__doc__)
            mercados(sys.argv[2], sys.argv[3:])
    except OSError as e:
        sys.exit(f"No se pudo leer Winamax ({e}). Usa webs de cuotas o estima la cuota, y dilo en la nota.")


if __name__ == "__main__":
    main()
