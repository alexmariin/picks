"""Rehace la parte de números de aprendizaje.md a partir de data/dias/*.json.

Uso (desde la raíz del repo):  python3 estadisticas.py
Solo cambia lo que hay entre las marcas <!-- STATS --> y <!-- /STATS -->; las lecciones escritas a mano no se tocan.
"""
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
ARCHIVO = BASE / "aprendizaje.md"
INI, FIN = "<!-- STATS -->", "<!-- /STATS -->"


def picks_cerrados():
    for f in sorted((BASE / "data" / "dias").glob("*.json")):
        dia = json.loads(f.read_text(encoding="utf-8"))
        for p in dia.get("picks", []):
            if p.get("resultado") in ("acierto", "fallo"):
                yield dia, p


def franja_cuota(c):
    return "< 1,30" if c < 1.30 else "1,30 – 1,49" if c < 1.50 else "1,50 – 1,79" if c < 1.80 else "≥ 1,80"


def franja_prob(p):
    return "< 60 %" if p < 0.60 else "60 – 69 %" if p < 0.70 else "70 – 79 %" if p < 0.80 else "≥ 80 %"


def competicion(c):
    return c.split("·")[0].strip()


def tabla(titulo, grupos, orden=None):
    filas = []
    claves = orden or sorted(grupos, key=lambda k: -len(grupos[k]))
    for k in claves:
        g = grupos.get(k)
        if not g:
            continue
        n, ok = len(g), sum(1 for p in g if p["resultado"] == "acierto")
        esperado = sum(p["prob"] for p in g) / n
        beneficio = sum((p["cuota"] - 1) if p["resultado"] == "acierto" else -1 for p in g)
        filas.append(f"| {k} | {n} | {ok} | {ok / n:.0%} | {esperado:.0%} | {beneficio:+.2f} u ({beneficio / n:+.0%}) |")
    if not filas:
        return ""
    return (f"### {titulo}\n| Grupo | Picks | Aciertos | % real | % que dije | Neto a 1 u por pick |\n"
            "|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n")


def combinadas():
    por_tipo = defaultdict(lambda: [0, 0, 0.0])  # ganadas, perdidas, neto
    for f in sorted((BASE / "data" / "dias").glob("*.json")):
        dia = json.loads(f.read_text(encoding="utf-8"))
        por_id = {p["id"]: p for p in dia.get("picks", [])}
        for cb in dia.get("combinadas", []):
            lista = [por_id[i] for i in cb.get("picks", []) if i in por_id]
            res = [p.get("resultado") for p in lista]
            tipo = cb["id"] if cb["id"] in ("segura", "equilibrada", "sonadora") else "otras"
            if "fallo" in res:
                por_tipo[tipo][1] += 1
                por_tipo[tipo][2] -= 1
            elif lista and all(r in ("acierto", "nulo") for r in res):
                cuota = 1.0
                for p in lista:
                    if p["resultado"] == "acierto":
                        cuota *= p["cuota"]
                por_tipo[tipo][0] += 1
                por_tipo[tipo][2] += cuota - 1
    if not por_tipo:
        return ""
    filas = [f"| {t} | {g} | {p} | {n:+.2f} u |" for t, (g, p, n) in sorted(por_tipo.items())]
    return "### Combinadas (1 u a cada una)\n| Tipo | Ganadas | Perdidas | Neto |\n|---|---|---|---|\n" + "\n".join(filas) + "\n"


def main():
    cerrados = list(picks_cerrados())
    ps = [p for _, p in cerrados]
    n = len(ps)
    ok = sum(1 for p in ps if p["resultado"] == "acierto")
    por = lambda f: {k: [p for p in ps if f(p) == k] for k in {f(p) for p in ps}}
    bloque = [f"_Actualizado con {n} picks cerrados (de {cerrados[0][0]['fecha'] if cerrados else '—'} a {cerrados[-1][0]['fecha'] if cerrados else '—'})._\n",
              f"**Total:** {ok} de {n} ({ok / n:.0%} real frente a {sum(p['prob'] for p in ps) / n:.0%} que dije).\n" if n else "Aún no hay picks cerrados.\n",
              tabla("Por mercado", por(lambda p: p["mercado"])),
              tabla("Por cuota", por(lambda p: franja_cuota(p["cuota"])), ["< 1,30", "1,30 – 1,49", "1,50 – 1,79", "≥ 1,80"]),
              tabla("Calibración: por probabilidad que dije", por(lambda p: franja_prob(p["prob"])), ["< 60 %", "60 – 69 %", "70 – 79 %", "≥ 80 %"]),
              tabla("Por competición", por(lambda p: competicion(p["competicion"]))),
              combinadas()]
    nuevo = INI + "\n" + "\n".join(b for b in bloque if b) + FIN
    texto = ARCHIVO.read_text(encoding="utf-8")
    i, j = texto.index(INI), texto.index(FIN) + len(FIN)
    ARCHIVO.write_text(texto[:i] + nuevo + texto[j:], encoding="utf-8")
    print(f"aprendizaje.md actualizado con {n} picks cerrados.")


if __name__ == "__main__":
    main()
