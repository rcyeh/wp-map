## Process

Pages do not change that frequently. Also, the process of:

1. getting the dumps (hour),
2. generating extracts (minutes)

can take a day.

### Protocol: refresh articles database

1. `python3 download_extract_wikidata.py`
2. `python3 download_qrank.py`
3. `python3 join.py`
4. `python3 write.py`

### Decision: Bypass the database dumps.

Instead:

1. Download the wikidata archive (100 GB) as a compressed stream.
   To save disk space, decompress stream and extract essential data in flight.
   - wikibase_item_id
   - page title
   - latitude/longitude

   In the May 2026 file, there are: 1,417,268 records with the P625
   geographical information tag. Of those, 1,412,537 (99.7%) are on Earth.

2. Use the wikibase_item_id to obtain qrank. Final data set:
   dict<str, int>

### Decision: Mercantile for saving tiles.

Cluster points to make 100- to 200-point tile files. These will be denser (and
go to higher zoom levels) at high-density places than at low-density places.
At lower density places, might need to zoom out to see.

In the Javascript, when it requests an (z, x, y) for a tile, provide a map:

- identity if in a dense place: directly request the (z, x, y) points db tile.
- redirect to request next coarser resolution if the tile doesn't exist

So the client javascript will already know what tiles exist. Maybe use this
data structure with this logic:

- If you find the (z, x, y), then request it. Otherwise, look for
  (z-1, x // 2, y // 2).
- There are 1.3 MM points. Suppose I use 100-point tile files --- there will be
  13,000 of these.
- If those are the leaf nodes in a tree, then there will be at most 13,000
  internal parent nodes.
- Total 26,000 (z, x, y) coordinates: barely 300 kB. Can do some testing to see
  if it's faster to use a flat set of tuples, or a hierarchical structure.
- Ultimately decided to save 20- to 300-point tile files.  This will exclude
  points in a sparse neighborhood (fewer than 20 points in a sq km) that are
  not among the top 300 most popular points when combined with neighboring
  tiles.

### Decision: Use protobufs.

(Moved to [../proto](../proto)

## Getting the dumps

https://dumps.wikimedia.org/other/pageviews/readme.html

### Popularity

https://qrank.toolforge.org/download/qrank.csv.gz (101 MB)

Lines: `Q####,rank`

## Things that I could not get to work

### `geo_tags`

Do not know how to join this.

https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-geo_tags.sql.gz (51 MB)

```
MariaDB [wp]> show columns from geo_tags;
+------------+------------------+------+-----+---------+----------------+
| Field      | Type             | Null | Key | Default | Extra          |
+------------+------------------+------+-----+---------+----------------+
| gt_id      | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
| gt_page_id | int(10) unsigned | NO   | MUL | NULL    |                |
| gt_globe   | varbinary(32)    | NO   |     | NULL    |                |
| gt_primary | tinyint(1)       | NO   |     | NULL    |                |
| gt_lat     | decimal(11,8)    | YES  |     | NULL    |                |
| gt_lon     | decimal(11,8)    | YES  |     | NULL    |                |
| gt_dim     | int(11)          | YES  |     | NULL    |                |
| gt_type    | varbinary(32)    | YES  |     | NULL    |                |
| gt_name    | varbinary(255)   | YES  |     | NULL    |                |
| gt_country | binary(2)        | YES  |     | NULL    |                |
| gt_region  | varbinary(3)     | YES  |     | NULL    |                |
| gt_lat_int | smallint(6)      | YES  |     | NULL    |                |
| gt_lon_int | smallint(6)      | YES  |     | NULL    |                |
+------------+------------------+------+-----+---------+----------------+
```

### Other dumps were ok

#### Page names and ids

https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page.sql.gz (2.3 GB)

```
MariaDB [wp]> show columns from page;
+--------------------+---------------------+------+-----+---------+----------------+
| Field              | Type                | Null | Key | Default | Extra          |
+--------------------+---------------------+------+-----+---------+----------------+
| page_id            | int(8) unsigned     | NO   | PRI | NULL    | auto_increment |
| page_namespace     | int(11)             | NO   | MUL | 0       |                |
| page_title         | varbinary(255)      | NO   |     |         |                |
| page_is_redirect   | tinyint(1) unsigned | NO   | MUL | 0       |                |
| page_is_new        | tinyint(1) unsigned | NO   |     | 0       |                |
| page_random        | double unsigned     | NO   | MUL | 0       |                |
| page_touched       | binary(14)          | NO   |     | NULL    |                |
| page_links_updated | binary(14)          | YES  |     | NULL    |                |
| page_latest        | int(8) unsigned     | NO   |     | 0       |                |
| page_len           | int(8) unsigned     | NO   | MUL | 0       |                |
| page_content_model | varbinary(32)       | YES  |     | NULL    |                |
| page_lang          | varbinary(35)       | YES  |     | NULL    |                |
+--------------------+---------------------+------+-----+---------+----------------+
```

#### Page props

https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page_props.sql.gz (432 MB)

### mariadb

Too slow

`sudo mariadb -D wp < dump.sql`
