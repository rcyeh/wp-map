# python3 extract.py

import datetime
import gzip
import json

import constants

page_wpr_map: dict[str, dict[str, float | str]] = {}


def read_qrank():
  records_matched = 0
  with gzip.open(constants.QRANK_CSV_FILE, 'rt', encoding='utf-8') as f:
    for line in f:
      record = line.split(',')
      if len(record) != 2:
        continue
      wikibase_item_id, qrank = record
      if wikibase_item_id in page_wpr_map:
        page_wpr_map[wikibase_item_id]['k'] = int(qrank)
        records_matched += 1
  print(f'Saved {records_matched} qrank')


def read_wikidata():
  records_added = 0
  with gzip.open(
    constants.WIKIDATA_COORDS_EXTRACT_FILE, 'rt', encoding='utf-8'
  ) as f:
    for line in f:
      wde = json.loads(line.strip())
      wpr = {
        'q': wde['q'],
        't': wde['t'],
        'y': wde['latitude'],
        'x': wde['longitude'],
      }
      page_wpr_map[wpr['q']] = wpr
      records_added += 1
  print(f'Read {records_added} wikidata records')


if __name__ == '__main__':
  print(f'{datetime.datetime.now().isoformat()} - read_wikidata')
  read_wikidata()
  print(f'{datetime.datetime.now().isoformat()} - read_qrank')
  read_qrank()
  print(f'{datetime.datetime.now().isoformat()} - sort')
  page_wpr_list = [
    wpr
    for wpr in sorted(page_wpr_map.values(), key=lambda wpr: -wpr.get('k', 0))
  ]
  del page_wpr_map
  print(f'{datetime.datetime.now().isoformat()} - write joined')
  with gzip.open(constants.JOINED_FILE, 'wt') as f:
    for wpr in page_wpr_list:
      f.write(f'{json.dumps(wpr)}\n')
