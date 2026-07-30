#!/usr/bin/env python3
"""
generate_subclass_graphviz.py

Creates Graphviz visualization (DOT file & PNG/SVG) of the top Wikidata POI subclass hierarchy.
Nodes are labeled with English class names, Q-IDs, and POI declaration counts.
Edges represent P279 (subclass of) and P31 (instance of) relationships.
"""

import ast
import gzip
import os
import sys
import time
import orjson
from collections import Counter, defaultdict

POI_FILE = "/home/r/github/wp-map/process/q_title_latlon.jsonl.gz"
GRAPH_FILE = "/home/r/github/wp-map/process/subclass_graph.jsonl.gz"
DOT_OUTPUT_FILE = "/home/r/github/wp-map/process/poi_subclass_taxonomy.dot"


def parse_poi_line(line_bytes):
    line_bytes = line_bytes.strip()
    if line_bytes.startswith(b"b'") or line_bytes.startswith(b'b"'):
        raw_str = ast.literal_eval(line_bytes.decode("utf-8"))
        return orjson.loads(raw_str)
    return orjson.loads(line_bytes)


def load_graph_and_poi_counts(min_poi_threshold=2500):
    print(f"[*] Counting direct POI subclass declarations in {POI_FILE}...")
    start = time.time()
    poi_counts = Counter()
    total_pois = 0
    total_declarations = 0

    with gzip.open(POI_FILE, "rb") as f:
        for line in f:
            total_pois += 1
            item = parse_poi_line(line)
            classes = item.get("c", [])
            for c in classes:
                cid = c if isinstance(c, int) else (c.get("numeric-id") if isinstance(c, dict) else None)
                if cid:
                    poi_counts[cid] += 1
                    total_declarations += 1

    print(f"[+] Parsed {total_pois:,} POIs ({total_declarations:,} total subclass declarations).")
    print(f"[+] Found {len(poi_counts):,} unique direct classes in POIs.")

    # Select top classes meeting threshold
    selected_class_ids = {cid for cid, count in poi_counts.items() if count >= min_poi_threshold}
    print(f"[*] Filtered {len(selected_class_ids):,} top classes with >= {min_poi_threshold:,} POIs...")

    # Load graph nodes & metadata
    print(f"[*] Loading graph structure from {GRAPH_FILE}...")
    graph = {}
    with gzip.open(GRAPH_FILE, "rb") as f:
        while True:
            try:
                line = f.readline()
                if not line:
                    break
                item = orjson.loads(line)
                qid = item.pop("id")
                # Store node if selected or relevant
                graph[qid] = item
            except EOFError:
                break
            except Exception:
                continue

    return poi_counts, selected_class_ids, graph


def generate_graphviz():
    min_threshold = 2500
    poi_counts, selected_ids, graph = load_graph_and_poi_counts(min_poi_threshold=min_threshold)

    # Collect edges between selected nodes and their parent nodes
    # We include parents if they exist in graph to build the DAG
    relevant_nodes = set(selected_ids)
    edges = set()

    for cid in list(selected_ids):
        node = graph.get(cid, {})
        parents = node.get("p279", []) + node.get("p31", [])
        for p in parents:
            # Connect if parent is in graph
            if p in selected_ids or p in graph:
                relevant_nodes.add(p)
                edges.add((cid, p)) # directed edge: child -> parent (subclass of)

    print(f"[*] Building Graphviz DOT with {len(relevant_nodes):,} nodes and {len(edges):,} edges...")

    dot_lines = []
    dot_lines.append("digraph POI_Subclass_Taxonomy {")
    dot_lines.append('  graph [rankdir="BT", layout=dot, labelloc="t", label="Wikidata POI Subclass-Of Hierarchy (P279 / P31)\\nNodes labeled with [Class Name (QID)] and direct POI count", fontname="Helvetica", fontsize=16];')
    dot_lines.append('  node [shape=box, style="filled,rounded", fillcolor="#E8F0FE", color="#1A73E8", fontname="Helvetica", fontsize=10];')
    dot_lines.append('  edge [color="#5F6368", arrowhead="normal", fontname="Helvetica", fontsize=8];')
    dot_lines.append("")

    for qid in relevant_nodes:
        node_info = graph.get(qid, {})
        lbl = node_info.get("lbl", f"Q{qid}")
        # Escape quotes for Graphviz
        lbl = lbl.replace('"', '\\"')
        cnt = poi_counts.get(qid, 0)

        # Style top nodes or high count nodes
        if cnt >= 20000:
            style = 'fillcolor="#CEEAD6", color="#137333", penwidth=2.0'
        elif cnt >= 5000:
            style = 'fillcolor="#E8F0FE", color="#1A73E8"'
        else:
            style = 'fillcolor="#F1F3F4", color="#5F6368"'

        node_label = f"{lbl}\\n(Q{qid})\\nPOI Count: {cnt:,}"
        dot_lines.append(f'  "Q{qid}" [label="{node_label}", {style}];')

    dot_lines.append("")
    for child, parent in edges:
        dot_lines.append(f'  "Q{child}" -> "Q{parent}" [label="subclass of"];')

    dot_lines.append("}")

    with open(DOT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(dot_lines))

    print(f"[+] Graphviz DOT file written to {DOT_OUTPUT_FILE}")

    # Attempt to render SVG/PNG using system dot if installed
    os.system(f"dot -Tsvg {DOT_OUTPUT_FILE} -o /home/r/github/wp-map/process/poi_subclass_taxonomy.svg")
    print("[+] Rendered SVG to /home/r/github/wp-map/process/poi_subclass_taxonomy.svg")


if __name__ == "__main__":
    generate_graphviz()
