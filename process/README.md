## Process

Pages do not change that frequently. Also, the process of:

1. getting the dumps (minutes),
2. loading to database (12 hours),
3. generating extracts, writing as mvt (???)

can take a day.

Decisions:

- Bypass the database. Instead:

1. Slurp the `geo_tags` dump records into memory.
   Keep `gt_page_id`, `gt_lat`, `gt_lon`, `gt_type`
   Filter to keep only `gt_globe = 'earth'`

   dict[int, tuple]
2. Use the `gt_page_id` to extract: `page_title`, `page_random`, `page_touched` from the page dump.
   dict[int, tuple]
   Filter to keep only `page_namespace` = 0
3. Use the `gt_page_id` to extract the Q#### entity ID from `page_props` (`pp_page`, `pp_propname`, `pp_value`, `pp_sortkey`)
   `pp_page = gt_page_id`
   `pp_propname = 'wikibase_item'`
   `pp_value = 'Q#######'`
   dict[int, str]
   set[str]
4. Use the extracted entity ID to obtain qrank. Final data set:
   dict<str, int>

## Getting the dumps

https://dumps.wikimedia.org/other/pageviews/readme.html

### Page names and ids

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

### Page props

https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page_props.sql.gz (432 MB)

### Geo coordinates

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

### Popularity

https://qrank.toolforge.org/download/qrank.csv.gz (101 MB)

Lines: `Q####,rank`

## Loading to database

`sudo mariadb -D wp < dump.sql`

## Generating extracts
