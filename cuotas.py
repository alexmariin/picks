"""Cuotas reales desde The Odds API (necesita la variable de entorno ODDS_API_KEY).

Uso (desde la raíz del repo):
    python3 cuotas.py ligas                      -> lista las ligas de fútbol activas (gratis, no gasta consultas)
    python3 cuotas.py soccer_spain_la_liga ...   -> cuotas de los partidos de HOY (hora de España) de esas ligas

Cada liga pedida gasta 2 consultas (mercados 1X2 y goles, región eu). El plan gratis tiene 500 al mes:
no pidas más de 4-5 ligas al día. Si quedan menos de 60, el script no gasta más.

Para cada partido saca:
- Winamax (winamax_fr; si no, winamax_de): 1X2 y más/menos 2,5 si lo ofrece.
- Pinnacle: la casa más afinada del mundo. Quitándole su margen da la PROBABILIDAD JUSTA de cada resultado.
- La mejor cuota de todas las casas y la mediana.
- VALOR = prob_justa(Pinnacle) x cuota_Winamax - 1. Si es positivo, Winamax paga más de lo que vale de verdad.
Guarda todo en data/cuotas/AAAA-MM-DD.json (no lo lee la web; es para el analista y para medir después).

MERCADOS EXTRA DE UN PARTIDO (córners, tarjetas, ambos marcan, doble oportunidad...):
    python3 cuotas.py partido <liga> <texto de un equipo> [mercados]
    ej.: python3 cuotas.py partido soccer_spain_la_liga betis
         python3 cuotas.py partido soccer_epl arsenal alternate_totals_corners,alternate_totals_cards
Mercados por defecto: alternate_totals_corners,alternate_team_totals_corners.
Otros: corners_1x2, alternate_spreads_corners, alternate_totals_cards, btts, double_chance, draw_no_bet, team_totals.
Gasta 1 consulta por cada mercado QUE DEVUELVA (región eu). Úsalo como mucho en 3 partidos al día.
Si quedan menos de 150 consultas no lo hace (las guarda para el 1X2 y los goles).
Los mercados de jugador (remates, goleador) solo los dan casas de EE. UU.: no están aquí.
"""
import json
import os
import statistics
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).parent
API = "https://api.the-odds-api.com/v4"
MADRID = ZoneInfo("Europe/Madrid")
MINIMO = 60


def pedir(url):
    clave = os.environ.get("ODDS_API_KEY")
    if not clave:
        sys.exit("Falta ODDS_API_KEY en el entorno.")
    sep = "&" if "?" in url else "?"
    with urllib.request.urlopen(f"{API}{url}{sep}apiKey={clave}", timeout=30) as r:
        return json.load(r), r.headers.get("x-requests-remaining")


def justas(precios):
    """Quita el margen de una casa: probabilidades que suman 1."""
    inv = {k: 1 / v for k, v in precios.items() if v and v > 1}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()} if s else {}


def mercado(casa, clave, punto=None):
    for m in casa.get("markets", []):
        if m["key"] == clave:
            return {o["name"]: o["price"] for o in m["outcomes"] if punto is None or o.get("point") == punto}
    return {}


def resumen(partido):
    casas = {c["key"]: c for c in partido.get("bookmakers", [])}
    wina = casas.get("winamax_fr") or casas.get("winamax_de") or {}
    pinn = casas.get("pinnacle") or {}
    loc, vis = partido["home_team"], partido["away_team"]
    nombres = {loc: "1", "Draw": "X", vis: "2", "Over": "mas_2.5", "Under": "menos_2.5"}
    out = {"local": loc, "visitante": vis,
           "hora": datetime.fromisoformat(partido["commence_time"].replace("Z", "+00:00")).astimezone(MADRID).strftime("%H:%M"),
           "winamax": {}, "pinnacle_justa": {}, "mejor": {}, "mediana": {}, "valor_winamax": {}}
    for clave, punto in (("h2h", None), ("totals", 2.5)):
        w = mercado(wina, clave, punto)
        p = justas(mercado(pinn, clave, punto))
        todas = {}
        for c in casas.values():
            for k, v in mercado(c, clave, punto).items():
                todas.setdefault(k, []).append(v)
        for k in set(w) | set(p) | set(todas):
            n = nombres.get(k, k)
            if k in w: out["winamax"][n] = w[k]
            if k in p: out["pinnacle_justa"][n] = round(p[k], 3)
            if k in todas:
                out["mejor"][n] = max(todas[k]); out["mediana"][n] = round(statistics.median(todas[k]), 2)
            if k in w and k in p:
                out["valor_winamax"][n] = round(p[k] * w[k] - 1, 3)
    return out


MINIMO_EXTRA = 150
EXTRA_DEF = "alternate_totals_corners,alternate_team_totals_corners"


def extra(liga, texto, mercados, guardado):
    """Mercados extra de UN partido de hoy. La lista de partidos (/events) no gasta consultas."""
    eventos, quedan = pedir(f"/sports/{liga}/events/")
    if quedan is not None and int(quedan) < MINIMO_EXTRA:
        print(f"Quedan {quedan} consultas: no pido mercados extra (reserva para 1X2 y goles).")
        return
    hoy = datetime.now(MADRID).date()
    t = texto.lower()
    ev = [e for e in eventos if datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")).astimezone(MADRID).date() == hoy
          and (t in e["home_team"].lower() or t in e["away_team"].lower())]
    if not ev:
        print(f"No encuentro hoy un partido de {liga} con '{texto}'. Partidos de hoy:")
        for e in eventos:
            print("  ", e["home_team"], "-", e["away_team"], e["commence_time"])
        return
    e = ev[0]
    datos, quedan = pedir(f"/sports/{liga}/events/{e['id']}/odds/?regions=eu&markets={mercados}&oddsFormat=decimal")
    casas = {c["key"]: c for c in datos.get("bookmakers", [])}
    wina = casas.get("winamax_fr") or casas.get("winamax_de") or {}
    pinn = casas.get("pinnacle") or {}
    res = {"local": e["home_team"], "visitante": e["away_team"], "mercados": {}}
    print(f"\n== {e['home_team']} - {e['away_team']} · casas: {len(casas)} · consultas que quedan: {quedan}")

    def grupos(casa, clave):
        g = {}
        for m in casa.get("markets", []):
            if m["key"] == clave:
                for o in m["outcomes"]:
                    g.setdefault((o.get("description", ""), o.get("point")), {})[o["name"]] = o["price"]
        return g

    claves = sorted({m["key"] for c in casas.values() for m in c.get("markets", [])})
    for clave in claves:
        filas = []
        todas = {}
        for c in casas.values():
            for gk, precios in grupos(c, clave).items():
                for n, v in precios.items():
                    todas.setdefault((gk, n), []).append(v)
        w, p = grupos(wina, clave), grupos(pinn, clave)
        for (gk, n), lista in sorted(todas.items(), key=lambda x: (str(x[0][0][0]), x[0][0][1] or 0, x[0][1])):
            just = justas(p.get(gk, {})).get(n)
            wv = w.get(gk, {}).get(n)
            filas.append({"equipo": gk[0], "linea": gk[1], "opcion": n, "winamax": wv, "mediana": round(statistics.median(lista), 2),
                          "mejor": max(lista), "pinnacle_justa": round(just, 3) if just else None,
                          "valor_winamax": round(just * wv - 1, 3) if just and wv else None, "casas": len(lista)})
        res["mercados"][clave] = filas
        print(f"  [{clave}]")
        for f in filas:
            print(f"   {(f['equipo'] + ' ') if f['equipo'] else ''}{f['opcion']} {f['linea'] if f['linea'] is not None else ''}: "
                  f"Winamax {f['winamax'] or '—'} | mediana {f['mediana']} ({f['casas']} casas) | prob justa {f['pinnacle_justa'] or '—'}"
                  f" | valor Winamax {f['valor_winamax'] if f['valor_winamax'] is not None else '—'}")
    if not claves:
        print("  Ninguna casa ofrece esos mercados para este partido (no gasta consultas).")
    guardado.setdefault("extra", []).append(res)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "partido":
        if len(sys.argv) < 4:
            sys.exit(__doc__)
        hoy = datetime.now(MADRID).date()
        archivo = BASE / "data" / "cuotas" / f"{hoy.isoformat()}.json"
        guardado = json.loads(archivo.read_text(encoding="utf-8")) if archivo.exists() else {"fecha": hoy.isoformat(), "ligas": {}}
        try:
            extra(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else EXTRA_DEF, guardado)
        except Exception as e:  # noqa: BLE001
            print(f"error {e}")
            return
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(json.dumps(guardado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nGuardado en {archivo.relative_to(BASE)}")
        return
    if sys.argv[1] == "ligas":
        datos, _ = pedir("/sports/")
        for s in datos:
            if s["key"].startswith("soccer_") and s["active"]:
                print(s["key"], "-", s["title"])
        return
    hoy = datetime.now(MADRID).date()
    archivo = BASE / "data" / "cuotas" / f"{hoy.isoformat()}.json"
    guardado = json.loads(archivo.read_text(encoding="utf-8")) if archivo.exists() else {"fecha": hoy.isoformat(), "ligas": {}}
    for liga in sys.argv[1:]:
        try:
            datos, quedan = pedir(f"/sports/{liga}/odds/?regions=eu&markets=h2h,totals&oddsFormat=decimal")
        except Exception as e:  # noqa: BLE001
            print(f"{liga}: error {e}")
            continue
        partidos = [resumen(p) for p in datos
                    if datetime.fromisoformat(p["commence_time"].replace("Z", "+00:00")).astimezone(MADRID).date() == hoy]
        guardado["ligas"][liga] = {"pedido": datetime.now(MADRID).strftime("%H:%M"), "partidos": partidos}
        print(f"\n== {liga}: {len(partidos)} partidos hoy · consultas que quedan este mes: {quedan}")
        for p in partidos:
            print(f"{p['hora']} {p['local']} - {p['visitante']}")
            for n in ("1", "X", "2", "mas_2.5", "menos_2.5"):
                if n in p["mediana"]:
                    print(f"   {n:10} Winamax {p['winamax'].get(n, '—'):>5} | mejor {p['mejor'][n]:>5} | mediana {p['mediana'][n]:>5}"
                          f" | prob justa {p['pinnacle_justa'].get(n, '—')} | valor Winamax {p['valor_winamax'].get(n, '—')}")
        if quedan is not None and int(quedan) < MINIMO:
            print(f"AVISO: solo quedan {quedan} consultas este mes. No pido más ligas.")
            break
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(guardado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nGuardado en {archivo.relative_to(BASE)}")


if __name__ == "__main__":
    main()
