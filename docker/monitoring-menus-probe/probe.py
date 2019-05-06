import networkx as nx
import requests
import time


class Timeit:
    """Register the time it takes to run a section of code."""
    def __init__(self, name, metrics):
        self.name = name
        self.metrics = metrics

    def __enter__(self):
        self.t = time.time()

    def __exit__(self, *what, **ever):
        self.metrics.add(self.name, 'gauge', time.time() - self.t)


def probe(url, metrics, inject_get_json=None):
    """Measure the size and sanity of the menu at `url`; report with `metrics`."""
    metrics.add_labels({'url': url})

    with Timeit('epfl_menu_request_time_seconds', metrics):
        if inject_get_json:
            json = inject_get_json(url)
        else:
            json = requests.get(url).json()

    menu = json['items']
    menu_count = len(menu)
    metrics.add('epfl_menu_count', 'gauge', menu_count)

    ids = set(m['ID'] for m in menu)
    unique_menu_count = len(ids)
    metrics.add('epfl_menu_unique_count', 'gauge', unique_menu_count)

    orphan_count = 0
    G = nx.Graph()
    for m in menu:
        id = m['ID']
        G.add_node(id)
        parent = int(m.get('menu_item_parent', 0))
        if parent != 0:
            G.add_edge(id, parent)
            if parent not in ids:
                orphan_count += 1

    metrics.add('epfl_menu_orphan_count', 'gauge', orphan_count)
    metrics.add('epfl_menu_cycle_count', 'gauge', len(nx.cycle_basis(G)))
