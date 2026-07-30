#!/usr/bin/env python3
"""
analyze_poi_taxonomy.py

Analyzes POI class distributions from `q_title_latlon.jsonl.gz` using the
extracted `subclass_graph.jsonl.gz` hierarchy with streaming node loading and
robust EOF exception handling.
"""

import ast
import gzip
import os
import sys
import time
import orjson
from collections import Counter

POI_FILE = "/home/r/github/wp-map/process/q_title_latlon.jsonl.gz"
GRAPH_FILE = "/home/r/github/wp-map/process/subclass_graph.jsonl.gz"
TAXONOMY_REPORT_FILE = "/home/r/github/wp-map/process/taxonomy_analysis_report.json"

TOP_CATEGORIES = {
    # Settlements & Populated Places
    486972: "Settlement & Populated Place",  # human settlement
    15284: "Municipality / Admin Unit",      # municipality
    123705: "Neighborhood / District",       # neighborhood
    
    # Natural Features
    8502: "Mountain / Hill / Relief",        # mountain
    4022: "River / Stream / Watercourse",    # river
    14350: "Lake / Water Body",              # lake
    9826: "Island",                          # island
    15324: "Body of Water",                  # body of water

    # Buildings & Built Environment
    41176: "Building / Structure",           # building
    838948: "Architectural Structure",       # architectural structure
    16970: "Church / Place of Worship",      # church building
    83070: "Fortress / Castle",              # fortress
    1081138: "Historic Site / Monument",     # historic site

    # Historical Events & Time
    1190554: "Historical Event / Occurrence",# occurrence / event
    198: "War / Conflict",                   # war
    178561: "Battle",                        # battle

    # Transport & Infrastructure
    55488: "Railway Station",                # railway station
    1248784: "Airport / Airfield",           # airport
    928830: "Metro / Transit Station",       # metro station
    12280: "Bridge",                         # bridge
    34442: "Road / Highway",                 # road

    # Organizations / Parks / Cultural
    22673: "Park / Reserve",                 # park
    20025: "Protected Area / Reserve",       # protected area
    43229: "Organization / Institution",    # organization
    23413: "Facility / Venue",               # facility
    7075: "Library / Museum / Cultural",     # library/museum
}


def parse_poi_line(line_bytes):
    line_bytes = line_bytes.strip()
    if line_bytes.startswith(b"b'") or line_bytes.startswith(b'b"'):
        raw_str = ast.literal_eval(line_bytes.decode("utf-8"))
        return orjson.loads(raw_str)
    return orjson.loads(line_bytes)


def load_graph():
    print(f"[*] Loading line-delimited subclass graph from {GRAPH_FILE}...")
    start = time.time()
    graph = {}
    count = 0
    
    with gzip.open(GRAPH_FILE, "rb") as f:
        while True:
            try:
                line = f.readline()
                if not line:
                    break
                item = orjson.loads(line)
                qid = item.pop("id")
                graph[qid] = item
                count += 1
                if count % 1000000 == 0:
                    print(f"    Loaded {count:,} graph nodes...")
            except EOFError:
                print("    [!] End of compressed graph stream reached.")
                break
            except Exception as e:
                continue

    print(f"[+] Loaded {len(graph):,} graph nodes in {time.time() - start:.1f}s")
    return graph


def get_all_ancestors(class_id, graph, max_depth=8):
    visited = set()
    frontier = {class_id}
    
    for _ in range(max_depth):
        if not frontier:
            break
        next_frontier = set()
        for cid in frontier:
            if cid in visited:
                continue
            visited.add(cid)
            node = graph.get(cid)
            if node:
                parents = node.get("p279", []) + node.get("p31", [])
                for p in parents:
                    if p not in visited:
                        next_frontier.add(p)
        frontier = next_frontier
    return visited


def analyze_pois():
    graph = load_graph()
    
    print(f"[*] Analyzing POIs in {POI_FILE}...")
    start = time.time()
    
    total_pois = 0
    direct_class_counts = Counter()
    mapped_category_counts = Counter()
    unmapped_class_counts = Counter()
    
    with gzip.open(POI_FILE, "rb") as f:
        for line in f:
            total_pois += 1
            if total_pois % 300000 == 0:
                print(f"    Processed {total_pois:,} POIs ({time.time() - start:.1f}s)...")
                
            item = parse_poi_line(line)
            classes = item.get("c", [])
            
            matched_cats = set()
            for c in classes:
                cid = c if isinstance(c, int) else (c.get("numeric-id") if isinstance(c, dict) else None)
                if cid is None:
                    continue
                direct_class_counts[cid] += 1
                
                ancestors = get_all_ancestors(cid, graph)
                for cat_q, cat_name in TOP_CATEGORIES.items():
                    if cat_q in ancestors or cid == cat_q:
                        matched_cats.add(cat_name)
            
            if matched_cats:
                for cat_name in matched_cats:
                    mapped_category_counts[cat_name] += 1
            else:
                for c in classes:
                    cid = c if isinstance(c, int) else (c.get("numeric-id") if isinstance(c, dict) else None)
                    if cid:
                        unmapped_class_counts[cid] += 1

    elapsed = time.time() - start
    print(f"[+] POI Analysis complete in {elapsed:.1f}s across {total_pois:,} POIs!")
    
    top_unmapped = []
    for cid, count in unmapped_class_counts.most_common(30):
        node = graph.get(cid, {})
        lbl = node.get("lbl", f"Q{cid}")
        top_unmapped.append({"qid": f"Q{cid}", "label": lbl, "count": count})

    report = {
        "total_pois": total_pois,
        "unique_direct_classes": len(direct_class_counts),
        "mapped_categories_distribution": dict(mapped_category_counts.most_common()),
        "top_unmapped_classes": top_unmapped,
        "analysis_time_sec": round(elapsed, 2)
    }
    
    with open(TAXONOMY_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(orjson.dumps(report, option=orjson.OPT_INDENT_2).decode("utf-8"))
        
    print(f"[+] Taxonomy report saved to {TAXONOMY_REPORT_FILE}")
    print("\n--- MAPPED CATEGORIES DISTRIBUTION ---")
    for cat, cnt in mapped_category_counts.most_common():
        pct = (cnt / total_pois) * 100
        print(f"  {cat:35s}: {cnt:8,} ({pct:5.1f}%)")


if __name__ == "__main__":
    analyze_pois()
