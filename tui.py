"""TUI interactiva para el laboratorio Link-State (Dijkstra).

Modo de uso (no altera el modo clásico del laboratorio):
    python LinkState.py --tui            # abre el selector de topologías
    python LinkState.py --tui test/topo1.txt   # abre directo en esa topología

Solo usa la librería estándar (curses + ANSI), sin dependencias.
Si curses no está disponible (o no hay TTY), cae a un menú de texto.
"""

import os
import sys

import dijkstra
import read

TOPOS = [
    ("test/topo1.txt", "Topo 1 · Ejemplo 1", "u,v,w,x — inicialización con ∞"),
    ("test/topo2.txt", "Topo 2 · Ejemplo 2", "f,g,h,i — caso de empate D(h)=min(6,6)→p=g"),
    ("test/topo3.txt", "Topo 3 · Ejemplo 3", "a,b,c,d — referencia del lab"),
    ("test/topo4.txt", "Topo 4 · Ejercicio 1", "Hoja de topologías (a–f)"),
    ("test/topo5.txt", "Topo 5 · Ejercicio 2", "Hoja de topologías (a–f)"),
    ("test/topo6.txt", "Topo 6 · Ejercicio 3", "Hoja de topologías (a–h)"),
    ("test/topo7.txt", "Topo 7", "13 nodos desde h"),
]

# Códigos ANSI (solo para el fallback de texto, curses usa sus colores)
_B = "\033[1m"
_D = "\033[2m"
_C = "\033[36m"
_G = "\033[32m"
_Y = "\033[33m"
_R = "\033[0m"


def build_path(init_node, pred, target):
    """Reconstruye la ruta init_node → target siguiendo p(v)."""
    if target == init_node:
        return [init_node]
    path = [target]
    seen = {target}
    while path[-1] != init_node:
        prev = pred.get(path[-1])
        if prev is None or prev in seen:
            return path[::-1]  # incompleta (no conexo)
        seen.add(prev)
        path.append(prev)
    return path[::-1]


def load(path):
    """Lee el TXT y corre Dijkstra. Retorna dict con todo lo necesario."""
    init_node, route = read.routingFile(path)
    dist, pred, steps, order, nodes = dijkstra.compute(init_node, route)
    return {
        "path": path,
        "init": init_node,
        "route": route,
        "dist": dist,
        "pred": pred,
        "steps": steps,
        "order": order,
        "nodes": nodes,
    }


# ---------------------------------------------------------------- renderers
def render_cost_matrix(init_node, route, nodes):
    cols = nodes
    w = max(3, max(len(n) for n in nodes) + 1, 3)
    top = "┌" + "┬".join("─" * (w + 2) for _ in cols) + "┐"
    hdr = "│" + "".join(f" {n:^{w}} │" for n in cols)
    sep = "├" + "┼".join("─" * (w + 2) for _ in cols) + "┤"
    bot = "└" + "┴".join("─" * (w + 2) for _ in cols) + "┘"
    lines = [top, hdr, sep]
    for r in cols:
        cells = []
        for c_ in cols:
            if r == c_:
                v = "·"
            else:
                v = route.get(r, {}).get(c_, "∞")
            mark = "◉" if r == init_node else " "
            cells.append(f"{mark}{v:^{w}} │")
        lines.append("│" + "".join(cells))
    lines.append(bot)
    return lines


def render_steps(init_node, nodes, steps):
    cols = [n for n in nodes if n != init_node]
    widths = [max(9, len(f"D({n}),p({n})")) for n in cols]
    # encabezado
    head_cells = [f"D({n}),p({n})".center(w_) for n, w_ in zip(cols, widths)]
    top = "┌──────┬" + "┬".join("─" * (w_ + 2) for w_ in widths) + "┬────┐"
    hdr = "│ Paso │" + "".join(f" {c} │" for c in head_cells) + " N' │"
    sep = "├──────┼" + "┼".join("─" * (w_ + 2) for w_ in widths) + "┼────┤"
    bot = "└──────┴" + "┴".join("─" * (w_ + 2) for w_ in widths) + "┴────┘"
    lines = [top, hdr, sep]
    for row in steps:
        paso, *cells, nprima = row
        parts = [f" {str(paso):^4} │"]
        for cell, w_ in zip(cells, widths):
            parts.append(f" {cell:^{w_}} │")
        parts.append(f" {str(nprima):^2} │")
        lines.append("│" + "".join(parts))
    lines.append(bot)
    return lines


def render_paths(data):
    init_node = data["init"]
    dist = data["dist"]
    pred = data["pred"]
    others = [n for n in data["nodes"] if n != init_node]
    lines = []
    for v in others:
        d = dist[v]
        d_str = "∞" if d == float("inf") else str(d)
        path = build_path(init_node, pred, v)
        arrow = " → ".join(path)
        lines.append(f"  {init_node} ⇢ {v}   costo {d_str:<4}  vía {pred.get(v)}   │ {arrow}")
    return lines


def detail_lines(data):
    """Ensambla la vista completa de una topología (texto plano)."""
    init_node = data["init"]
    L = []
    L.append(f"Topología  {data['path']}   ·   nodo inicial {init_node}")
    L.append(f"N = {{{', '.join(data['nodes'])}}}   ·   orden N': {' → '.join(data['order'])}")
    L.append("")
    L.append("▸ Matriz de costos (◉ = fila del nodo inicial, ∞ = sin enlace)")
    L.extend(render_cost_matrix(init_node, data["route"], data["nodes"]))
    L.append("")
    L.append("▸ Pasos de Dijkstra  —  empate w: alfabético · empate D(v): gana el nuevo w (<=)")
    L.extend(render_steps(init_node, data["nodes"], data["steps"]))
    L.append("")
    L.append("▸ Rutas más cortas finales")
    L.extend(render_paths(data))
    return L


# ------------------------------------------------------- fallback de texto
def _print_detail_text(data, color=True):
    B, D_, C, G, Y, R = (_B, _D, _C, _G, _Y, _R) if color else ("", "", "", "", "", "")
    print(f"\n{B}{C}╔═ Link-State · Dijkstra ═══════════════════════════════{R}")
    print(f"{B}  {data['path']}  ·  inicio {Y}{data['init']}{R}{B}  ·  N = {{{', '.join(data['nodes'])}}}{R}")
    print(f"{D_}  Orden N': {' → '.join(data['order'])}{R}")
    print(f"\n{B}▸ Matriz de costos{R} {D_}(◉ fila inicial){R}")
    for ln in render_cost_matrix(data["init"], data["route"], data["nodes"]):
        print("  " + ln)
    print(f"\n{B}▸ Pasos de Dijkstra{R}")
    for ln in render_steps(data["init"], data["nodes"], data["steps"]):
        print("  " + ln)
    print(f"\n{B}▸ Rutas finales{R}")
    for ln in render_paths(data):
        print(f"  {G}{ln}{R}")
    print()


def text_menu(start=None):
    color = sys.stdout.isatty()
    if start and os.path.exists(start):
        try:
            _print_detail_text(load(start), color=color)
        except Exception as exc:  # noqa: BLE001
            print(f"> No se pudo cargar {start}: {exc}")
        return
    print("\n  Link-State · Dijkstra — selector de topologías\n")
    for i, (path, title, desc) in enumerate(TOPOS, 1):
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"  [{i}] {exists} {title}\n      {path} — {desc}")
    print("  [q] salir\n")
    try:
        ans = input("  Elige [1-7]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if ans in ("q", "quit", "exit"):
        return
    try:
        idx = int(ans) - 1
        path = TOPOS[idx][0]
    except (ValueError, IndexError):
        print("> Opción inválida.")
        return
    if not os.path.exists(path):
        print(f"> No existe {path}.")
        return
    _print_detail_text(load(path), color=color)


# ------------------------------------------------------------------- curses
def _curses_main(stdscr, start=None):
    import curses

    curses.curs_set(0)
    stdscr.keypad(True)
    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_GREEN, -1)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)

    sel = 0
    if start:
        for i, (p, _, _) in enumerate(TOPOS):
            if p == start:
                sel = i
                break
        return _curses_detail(stdscr, TOPOS[sel][0])

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(0, 0, " Link-State · Dijkstra  —  selector ".ljust(w - 1)[: w - 1], curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(2, 2, "↑/↓ o j/k para moverte · Enter ver · 1-7 directo · q salir", curses.A_DIM)
        for i, (path, title, desc) in enumerate(TOPOS):
            y = 4 + i * 2
            if y + 1 >= h - 2:
                break
            ok = os.path.exists(path)
            label = f" [{i + 1}] {'✓' if ok else '✗'} {title}"
            attr = curses.color_pair(5) | curses.A_BOLD if i == sel else curses.A_BOLD
            stdscr.addstr(y, 2, label[: w - 3], attr)
            sub = f"     {path} — {desc}"
            try:
                stdscr.addstr(y + 1, 2, sub[: w - 3], curses.color_pair(1) if i == sel else curses.A_DIM)
            except curses.error:
                pass
        stdscr.addstr(h - 1, 0, " Enter=abrir   q=salir ".ljust(w - 1)[: w - 1], curses.color_pair(2))
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27):
            return
        if key in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(TOPOS)
        elif key in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(TOPOS)
        elif ord("1") <= key <= ord("7"):
            sel = key - ord("1")
            if os.path.exists(TOPOS[sel][0]):
                _curses_detail(stdscr, TOPOS[sel][0])
        elif key in (curses.KEY_ENTER, 10, 13):
            if os.path.exists(TOPOS[sel][0]):
                _curses_detail(stdscr, TOPOS[sel][0])


def _curses_detail(stdscr, path):
    import curses

    try:
        data = load(path)
    except Exception as exc:  # noqa: BLE001
        stdscr.erase()
        stdscr.addstr(2, 2, f"No se pudo cargar {path}: {exc}")
        stdscr.addstr(4, 2, "Pulsa cualquier tecla…")
        stdscr.refresh()
        stdscr.getch()
        return
    lines = detail_lines(data)
    y_off, x_off = 0, 0
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        title = f" {path}  ·  inicio {data['init']}  ·  N={{{','.join(data['nodes'])}}} "
        stdscr.addstr(0, 0, title.ljust(w - 1)[: w - 1], curses.color_pair(2) | curses.A_BOLD)
        for row in range(h - 2):
            idx = y_off + row
            if idx >= len(lines):
                break
            ln = lines[idx][x_off : x_off + w - 1]
            attr = 0
            if ln.startswith("▸"):
                attr = curses.color_pair(1) | curses.A_BOLD
            stdscr.addstr(1 + row, 0, ln, attr)
        footer = " ↑↓ scroll  ←→ lateral  PgUp/PgDn  b=volver  q=salir "
        stdscr.addstr(h - 1, 0, footer.ljust(w - 1)[: w - 1], curses.color_pair(2))
        stdscr.refresh()
        key = stdscr.getch()
        max_w = max(len(ln) for ln in lines)
        if key in (ord("q"), ord("Q")):
            raise SystemExit(0)
        if key in (ord("b"), ord("B"), 27):
            return
        if key == curses.KEY_UP:
            y_off = max(0, y_off - 1)
        elif key == curses.KEY_DOWN:
            y_off = min(max(0, len(lines) - (h - 2)), y_off + 1)
        elif key == curses.KEY_LEFT:
            x_off = max(0, x_off - 4)
        elif key == curses.KEY_RIGHT:
            x_off = min(max(0, max_w - w + 1), x_off + 4)
        elif key == curses.KEY_PPAGE:
            y_off = max(0, y_off - (h - 2))
        elif key == curses.KEY_NPAGE:
            y_off = min(max(0, len(lines) - (h - 2)), y_off + (h - 2))


def run(start=None):
    """Punto de entrada: intenta curses, si falla usa menú de texto."""
    if start == "--tui":
        start = None
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import curses

            curses.wrapper(_curses_main, start)
            return
        except Exception as exc:  # noqa: BLE001
            print(f"(curses no disponible: {exc} — usando menú de texto)")
    text_menu(start)
