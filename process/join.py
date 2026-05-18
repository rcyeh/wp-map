# python3 extract.py

import dataclasses
import datetime
import gzip
import json

import constants

@dataclasses.dataclass(slots=True)
class WPRecord:
  i: int | None = None  # page_id
  y: float | None = None  # gt_lat
  x: float | None = None  # gt_lon
  c: str | None = None  # gt_type
  t: str | None = None  # page_title
  r: float | None = None  # page_random
  w: str | None = None  # page_touched
  q: str | None = None  # wikibase_item_id
  k: int | None = None  # qrank

page_wpr_map: dict[int | str, WPRecord] = {}
entity_page_map: dict[str, int] = {}


def read_gzip_mysqldump(filename: str, process: Callable):
  print(f"reading {filename} ...")
  with gzip.open(filename, 'rt', encoding='utf-8', errors='replace') as f:
    for line in f:
      if not line.startswith('INSERT INTO'):
        continue
      vidx = line.find('VALUES')
      line = line[(vidx + 8):]  # drop opening paren
      process(line.split('),('))


def read_geo_tags():
  records_added = 0
  def process_geo_tags(csv_records: list[str]):
    nonlocal records_added
    for entry in csv_records:
      record = entry.split(',')
      if len(record) < 13:
        print(f'Failed to extract from {record}')
        continue
      gt_id, gt_page_id, gt_globe, gt_primary, gt_lat, gt_lon, gt_dim, gt_type, gt_name, gt_country, gt_region, gt_lat_int, gt_lon_int = record[0:13]
      gt_page_id = int(gt_page_id)
      if gt_page_id not in page_wpr_map:
        wpr = WPRecord()
        wpr.i = gt_page_id
        wpr.y = float(gt_lat)
        wpr.x = float(gt_lon)
        wpr.c = gt_type
        page_wpr_map[gt_page_id] = wpr
        records_added += 1
  read_gzip_mysqldump(constants.GEO_TAGS_DUMP_FILE, process_geo_tags)
  print(f'Saved {records_added} geo_tags records')

def read_page_props():
  records_seen = 0
  records_matched = 0
  def process_page_props(csv_records: list[str]):
    nonlocal records_seen
    nonlocal records_matched
    for entry in csv_records:
      record = entry.split(',')
      if len(record) != 4:
        continue
      pp_page, pp_propname, pp_value, pp_sortkey = record
      records_seen += 1
      if pp_propname != 'wikibase_item':
        continue
      pp_page = int(pp_page)
      if pp_page in page_wpr_map:
        page_wpr_map[pp_page].q = pp_value
        entity_page_map[pp_value] = pp.page
        records_matched += 1
  read_gzip_mysqldump(constants.PAGE_PROPS_DUMP_FILE, process_page_props)
  print(f'Saved {records_matched} wikibase_item IDs out of {records_seen} seen')

def read_page():
  records_matched = 0
  records_seen = 0
  def process_page(csv_records: list[str]):
    nonlocal records_seen
    nonlocal records_matched
    for entry in csv_records:
      record = entry.split(',')
      if len(record) != 12:
        continue
      page_id, page_namespace, page_title, page_is_redirect, page_is_new, page_random, page_touched, page_links_updated, page_latest, page_len, page_content_model, page_lang = record
      page_id = int(page_id)
      records_seen += 1
      if (page_namespace, page_title) in page_wpr_map:
        wpr = page_wpr_map[(page_namespace, page_title)]
        del page_wpr_map[(page_namespace, page_title)]
        wpr.i = page_id
        wpr.r = float(page_random)
        wpr.w = page_touched
        page_wpr_map[page_id] = wpr
        records_matched += 1
  read_gzip_mysqldump(constants.PAGE_DUMP_FILE, process_page)
  print(f'Saved {records_matched} page data out of {records_seen} seen')

def read_qrank():
  records_matched = 0
  def process_qrank_line(entry: str):
    nonlocal records_matched
    record = entry.split(',')
    if len(record) != 2:
      return
    wikibase_item_id, qrank = record
    if wikibase_item_id in entity_page_map:
      page_id = entity_page_map[wikibase_item_id]
      page_wpr_map[page_id].k = int(qrank)
      records_matched += 1
  with gzip.open(constants.QRANK_CSV_FILE, 'rt', encoding='utf-8') as f:
    for line in f:
      process_qrank_line(line)
  print(f'Saved {records_matched} qrank')

def read_redirect():
  records_matched = 0
  records_seen = 0
  def process_redirect(csv_records: list[str]):
    nonlocal records_seen
    nonlocal records_matched
    for entry in csv_records:
      record = entry.split(',')
      if len(record) != 5:
        continue
      rd_from, rd_namespace, rd_title, rd_interwiki, rd_fragment = record
      page_id = int(rd_from)
      records_seen += 1
      if page_id in page_wpr_map:
        wpr = page_wpr_map[page_id]
        del page_wpr_map[page_id]
        wpr.t = rd_title
        wpr.i = 0
        page_wpr_map[(rd_namespace, rd_title)] = wpr
        records_matched += 1
  read_gzip_mysqldump(constants.REDIRECT_DUMP_FILE, process_redirect)
  print(f'Saved {records_matched} redirect data out of {records_seen} seen')

def read_wikidata():
  records_added = 0
  def process_geo_tags(csv_records: list[str]):
    nonlocal records_added
    for entry in csv_records:
      record = entry.split(',')
      if len(record) < 3:
        print(f'Failed to extract from {record}')
        continue
      wikibase_item_id, page_title, p625 = record[0:3]
      if wikibase_item_id not in page_wpr_map:
        wpr = WPRecord()
        wpr.q = wikibase_item_id
        wpr.y = float(gt_lat)
        wpr.x = float(gt_lon)
        wpr.t = page_title
        page_wpr_map[wikibase_item_id] = wpr
        records_added += 1
  with gzip.open(constants.WIKIDATA_EXTRACT_CSV_FILE, 'rt', encoding='utf-8') as f:
    for line in f:
      process_wikidata_extract(line)
  print(f'Saved {records_added} wikidata records')


if __name__ == "__main__":
  # print(f'{datetime.datetime.now().isoformat()} - read_geo_tags')
  # read_geo_tags()
  # print(f'{datetime.datetime.now().isoformat()} - read_redirect')
  # read_redirect()
  # print(f'{datetime.datetime.now().isoformat()} - read_page')
  # read_page()
  # print(f'{datetime.datetime.now().isoformat()} - read_page_props')
  # read_page_props()
  print(f'{datetime.datetime.now().isoformat()} - read_qrank')
  read_qrank()
  print(f'{datetime.datetime.now().isoformat()} - sort')
  page_wpr_list = [dataclasses.asdict(wpr) for wpr in sorted(page_wpr_map.values(), key=lambda wpr: -wpr.k if wpr.k is not None else 0)]
  del page_wpr_map
  print(f'{datetime.datetime.now().isoformat()} - write joined')
  with gzip.open('joined.jsonlines.gz', 'wt') as f:
    json.dump(page_wpr_list, f)
