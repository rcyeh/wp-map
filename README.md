# wp-map: Wikipedia x Map

Show the most-popular Wikipedia articles with coordinates near a neighborhood,
to facilitate exploration and discovery.

URL: https://rcyeh.github.io/wp-map/

When traveling to new places, I'd like to know: what are the most well-known
facts about each place? Wikipedia provides a wealth of crowd-sourced
information, and this app helps browse those pages on a map.

I've placed special consideration on making this mobile-friendly, reducing
number of network calls and the amount of data transferred.

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

When I am exploring a neighborhood, I am likely to want to learn about
more-popular pages before less-popular pages. By showing the most popular
pages, this app will tend to reinforce the Matthew effect (where more-popular
pages will receive more traffic; and less-popular pages will receive less).

Maybe I should enable the user to control a random-selection facility. Or to hide or favorite specific markers.

### Limit files to 14 kB when possible.

Data files up to 14 kB will be sent all at once, without needing to await a
TCP ack. (Dukkipati et al (2010) and RFC 3390)

At zoom level 15 (where each tile at the equator is 2^-15 x 2^-15 of the
earth's surface: about 1.2 km x 1.2 km or 0.75 mi x 0.75 mi), over a million
of the points-of-interest would be the only point in its tile. Each
point-of-interest is a few integers and a short title. It would be a
waste to transmit those one-by-one, so I don't make those tiles available.
If the map view wants to request that, then I'll instead request the nearest
enclosing tile (at lower zoom) that has collected at least 20 points, up to
300 points. 20 points is really a waste:

Each point has:

- A 32-bit unsigned integer identifier (takes 5 bytes (29-30 bits))
- A 32-bit signed integer longitude in 10^-5 degrees (1-meter resolution, fits in 4 bytes (28 bits))
- A 32-bit signed integer latitude in 10^-5 degrees (1-meter resolution, fits in 4 bytes (28 bits))
- A 32-bit unsigned integer log ranking (takes 2-3 bytes (14-15 bits))
- Page title string

or some 30-50 bytes. I'm finding that 300 points will typically fit in 12 kB.

### Minimize network calls.

Compress the data transmitted over the wire with protobuf encoding.
Provide points of interest at the lowest zoom level possible, and don't
provide unnecessarily-high resolution data.

## Comparison to Alternatives

I'm not the first to want to see Wikipedia pages on a map. I want a thin, fast
interface that gets out of my way, enabling me to go directly to Wikipedia,
without having to navigate another user interface paradigm.

The first problem is: with 1.3 MM geo-tagged pages, how do you present the
forest of points-of-interest?

Clustering and heat-map approaches help visualize the concentration of pages
at the expense of direct navigation to a page. It's annoying to click on a
cluster only to find that it breaks into multiple unrelated clusters. More
generally, it's annoying to have to click at all --- the default markers in
many popular map libraries don't even show a label, and you must click before
you can see a tooltip or bubble showing what you clicked on.

Instead of presenting all pages, I imagined that I'm likely to want to read
what others have read, and decided to rely on Wikipedia's own crowd-sourced
popularity estimates, to present only the top N most-popular pages in any view.

The next problem is: how to make this fast? Show labels. Show fewer
points-of-interest. Cache the geo-tagged page references on the same tiles as
the slippy maps. Compress and filter to make each tile's data under 14 kB.
Use fewer network calls and minimal Javascript overall.

This site:

- Shows only a few points. Unlike the comprehensive offerings below, this does not suggest where there might be more points.
- Provides labels on the (user-selectable) N most popular drawn points.
- Static site, no database needed.
- leaflet + OpenStreetMap
- starts at 14 MB JS heap size, grows as more points are loaded / 72 MB Chrome tab footprint.

https://wikimap.wiki/

- Shows all points - gives an idea of the global distribution of all articles.
- Many points get labels as you zoom in.
- Some points do not get labels and you still have to click, which is a slow load.
- Clicking will search a small-radius near the click point, which incurs latency.
- Only supports discrete zoom levels.
- Multilingual.
- OpenStreetMap
- starts at 30 MB JS heap size / 72 MB Chrome tab footprint.

https://wikimapped.nikamma.in/

- Starts with heatmap of articles, becoming points-of-interest as you zoom in.
- Points within a perceptually tight lat/lon (radius varies by zoom) are
  rendered on the same dialog box. This can be useful for multiple articles
  relating to the same location.
- No labels on points-of-interest, must tap each individually to discover what
  it is about.
- Loads quickly.
- React and minified JS.
- Stadia Maps, OpenMapTiles, OpenStreetMap
- 60 MB JS heap size / 120 MB Chrome tab footprint.
- This is very close to what I would have liked to build. The only thing
  missing is the point labels.

https://wikiexplore.org/

- No labels on points-of-interest, must tap each individually to discover what it is about.
- Only loads points-of-interest at high-enough zoom.
- Loads quickly.
- Multilingual.
- Mapbox + OpenStreetMap
- Starts at 60-70 MB JS heap size / 94 MB Chrome tab footprint.

https://wiki-map.com/

- Coalesces points into clusters.
- Distinct article points-of-interest drop onto the map as you zoom in.
- No labels on points-of-interest, must tap each individually to discover what it is about.
- Loads quickly.
- Multilingual.
- Google
- Starts at 40 MB JS heap size / 90 MB Chrome tab footprint.

https://wikimaps.vercel.app/

- Based on https://www.mediawiki.org/wiki/API:Nearby_places_viewer
- Colors points-of-interest by category.
- Labels are separated from the markers. Must tap each marker individually to
  discover what it is about.
- Very slow, due to querying Wikipedia's local places API.
  Encounters 429 (Too Many Requests) errors.
- leaflet + OpenStreetMap
- Starts at 31-50 MB JS heap size / 98 MB Chrome tab footprint.
