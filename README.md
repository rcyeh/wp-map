# wp-map: Wikipedia x Map

Lightweight static site showing the most popular Wikipedia articles in a
geographic area, to facilitate exploration and discovery.

URL: https://rcyeh.github.io/wp-map/

When traveling to new places, I'd like to know: what are the most well-known
facts about each place? Wikipedia already provides a wealth of information;
this app just shows those pages on a map.

I've placed special consideration on making this mobile-friendly, minimizing
the number of network calls and the amount of data transferred --- because
bandwidth is always limited, especially when traveling.

## Repo organization

- `docs` Website
  - `t` tile-oriented protobuf files with geo-located Wikipedia page titles
- `process` Protobuf-generation process

## Design decisions / micro-optimizations

### Show labels on the points of interest.

This provides a hint on what each map marker represents, without forcing me to
click or hover on each. The default marker for many map libraries do not
provide a label.

### Instead of showing all articles, prioritize popular articles.

When I am exploring a neighborhood, if the future is like the past, then I am
likely to want to learn about more-popular pages before less-popular pages. By
surfacing the most popular pages, this app will tend to reinforce the Matthew
effect (where more-popular pages will receive more traffic; and less-popular
pages will receive less).

### Limit files to 14 kB when possible.

Data files up to 14 kB are sent all at once, without needing to await a TCP ack.
(Dukkipati et al (2010) and RFC 3390)  Limiting the data files to 14 kB helps
lower the latency of data loads.

At zoom level 15 (where each tile at the equator is 2^-15 x 2^-15 of the
earth's surface: about 1.2 km x 1.2 km or 0.75 mi x 0.75 mi), over a million
of the points-of-interest would be the only point in its tile. Each
point-of-interest is a few integers and a short title. It would be a
waste to transmit those one-by-one, so I don't make those tiles available.
If the map view wants to request that, the app instead requests the nearest
enclosing tile (at lower zoom) that has collected at least 20 points, up to
300 points.

Each point has:

- A 32-bit unsigned integer identifier (takes 5 bytes (29-30 bits))
- A 32-bit signed integer longitude in 10^-5 degrees (1-meter resolution, fits in 4 bytes (28 bits))
- A 32-bit signed integer latitude in 10^-5 degrees (1-meter resolution, fits in 4 bytes (28 bits))
- A 32-bit unsigned integer log ranking (takes 2-3 bytes (14-15 bits))
- Page title string

or some 30-50 bytes. I'm finding that 300 points will typically fit in 12 kB.

This approach will cause some less-popular pages (alone in a tile, and not in
the top 300 most-popular pages when combined with neighboring tiles) to be
excluded.

### Minimize network calls.

Pack the data transmitted over the wire with protobuf encoding.
Provide points of interest at the lowest zoom level possible, and don't
provide unnecessarily-high resolution data.
