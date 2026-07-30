#!/usr/bin/env python3
"""
extract_subclass_graph.py

Extracts the Wikidata subclass and instance-of graph directly into a line-delimited
`subclass_graph.jsonl.gz` format (one JSON object per line: `{"id": QID, "p279": [...], "p31": [...], "lbl": "...", "desc": "..."}`).
"""

import gzip
import os
import sys
import time
import orjson

INPUT_SUBCLASS_FILE = "/home/r/github/wp-map/process/q_subclass.jsonl.gz"
OUTPUT_GRAPH_FILE = "/home/r/github/wp-map/process/subclass_graph.jsonl.gz"
OUTPUT_SUMMARY_FILE = "/home/r/github/wp-map/process/subclass_graph_summary.json"


def parse_numeric_q(q_str):
    if isinstance(q_str, str) and q_str.startswith("Q") and q_str[1:].isdigit():
        return int(q_str[1:])
    return None


def extract_claim_targets(claim_list):
    targets = []
    if not isinstance(claim_list, list):
        claim_list = [claim_list]
    for statement in claim_list:
        if not isinstance(statement, dict):
            continue
        mainsnak = statement.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        val = datavalue.get("value", {})
        if isinstance(val, dict):
            num_id = val.get("numeric-id")
            if num_id is not None:
                targets.append(int(num_id))
            else:
                qid = val.get("id")
                q_num = parse_numeric_q(qid)
                if q_num is not None:
                    targets.append(q_num)
    return targets


def extract_graph(input_path=INPUT_SUBCLASS_FILE):
    start_time = time.time()
    print(f"[*] Extracting Wikidata subclass definitions line-by-line to {OUTPUT_GRAPH_FILE}...")

    total_lines = 0
    total_nodes = 0
    total_p279_edges = 0
    total_p31_edges = 0

    with gzip.open(input_path, "rb") as fin, gzip.open(OUTPUT_GRAPH_FILE, "wb") as fout:
        for line in fin:
            total_lines += 1
            if total_lines % 500000 == 0:
                elapsed = time.time() - start_time
                print(f"    Processed {total_lines:,} lines ({elapsed:.1f}s)...")

            try:
                item = orjson.loads(line)
            except Exception:
                continue

            q_str = item.get("id")
            q_num = parse_numeric_q(q_str)
            if q_num is None:
                continue

            claims = item.get("claims", {})
            p279_targets = extract_claim_targets(claims.get("P279", []))
            p31_targets = extract_claim_targets(claims.get("P31", []))

            labels = item.get("labels", {})
            en_label = labels.get("en", {}).get("value") if isinstance(labels, dict) else None

            descriptions = item.get("descriptions", {})
            en_desc = descriptions.get("en", {}).get("value") if isinstance(descriptions, dict) else None

            node_data = {"id": q_num}
            if p279_targets:
                node_data["p279"] = p279_targets
                total_p279_edges += len(p279_targets)
            if p31_targets:
                node_data["p31"] = p31_targets
                total_p31_edges += len(p31_targets)
            if en_label:
                node_data["lbl"] = en_label
            if en_desc:
                node_data["desc"] = en_desc

            if len(node_data) > 1:
                fout.write(orjson.dumps(node_data) + b"\n")
                total_nodes += 1

    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(OUTPUT_GRAPH_FILE) / (1024 * 1024)
    print(f"[+] Extraction complete in {elapsed:.1f}s!")
    print(f"    Total items parsed: {total_lines:,}")
    print(f"    Graph nodes written: {total_nodes:,}")
    print(f"    P279 edges: {total_p279_edges:,}, P31 edges: {total_p31_edges:,}")
    print(f"    Output size: {file_size_mb:.2f} MB")

    summary = {
        "input_file": input_path,
        "total_subclass_entries": total_lines,
        "unique_nodes": total_nodes,
        "total_p279_edges": total_p279_edges,
        "total_p31_edges": total_p31_edges,
        "graph_file": OUTPUT_GRAPH_FILE,
        "graph_file_size_mb": round(file_size_mb, 2),
        "extraction_time_sec": round(elapsed, 2)
    }

    with open(OUTPUT_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(orjson.dumps(summary, option=orjson.OPT_INDENT_2).decode("utf-8"))
    print(f"[+] Summary written to {OUTPUT_SUMMARY_FILE}")


if __name__ == "__main__":
    extract_graph()
