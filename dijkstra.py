##############################
# Las funciones de este archivo 
# son una sugerenica de implementación 
# para el algoritmo dijkstra. 
#####

'''
Función de costo desde w a v, donde w y v son vecinos.
Retorna  c(w, v) el calculo de resultante de los vecinos w a v
'''
_routeDict = {}
_D = {}
_p = {}


def c(w, v):
    return _routeDict[w][v]


'''
Función de Menor costo desde el nodo de origen hasta el destino v.
Retorna  D(v) su costo actual de v
'''
def D(v):
    return _D[v]


'''
Función de Nodo anterior vecino de v
Retorna  p(v)  el nombre del nodo anterior vecino de v
'''
def p(v):
    return _p[v]


'''
Función donde Inicia la Ejecución del Algoritmo de Dijkstra
Retorna una Estructura
'''
def compute(initNode, routeDict):
    """Versión rica: retorna (D, p, stepsCalcs, orden_N_prima, nodes).

    D/p son dicts finales, stepsCalcs el historial compatible con
    show.stepsCalculatingRoute, orden_N_prima el orden en que los
    nodos entraron a N'.
    """
    global _routeDict, _D, _p
    _routeDict = routeDict
    INF = float('inf')

    nodes = sorted(routeDict.keys())

    # Inicialización: N' = {u}
    _D = {}
    _p = {}
    for v in nodes:
        if v == initNode:
            continue
        if v in routeDict.get(initNode, {}):
            _D[v] = routeDict[initNode][v]
            _p[v] = initNode
        else:
            _D[v] = INF
            _p[v] = initNode

    N_prime = [initNode]
    stepsCalcs = []

    def snapshot(paso):
        row = [paso]
        for v in nodes:
            if v == initNode:
                continue
            d = _D[v]
            d_str = "∞" if d == INF else str(d)
            row.append(f"{d_str}, {_p[v]}")
        row.append(N_prime[-1])
        return tuple(row)

    stepsCalcs.append(snapshot(0))

    paso = 0
    while len(N_prime) < len(nodes):
        candidates = [v for v in nodes if v not in N_prime]
        w = min(candidates, key=lambda v: (_D[v], v))
        N_prime.append(w)
        paso += 1
        if _D[w] != INF:
            for v in routeDict.get(w, {}):
                if v in N_prime:
                    continue
                if v == initNode:
                    continue
                alt = _D[w] + c(w, v)
                if alt <= _D[v]:
                    _D[v] = alt
                    _p[v] = w
        stepsCalcs.append(snapshot(paso))

    return dict(_D), dict(_p), stepsCalcs, list(N_prime), list(nodes)


def init(initNode, routeDict):
    _, _, stepsCalcs, _, _ = compute(initNode, routeDict)
    return stepsCalcs

















