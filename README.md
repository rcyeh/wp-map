# wp-map: Wikipedia x Map

Show the most-popular Wikipedia articles with coordinates near a neighborhood,
to facilitate exploration and discovery.

URL: https://rcyeh.github.io/wp-map/

## Repo organization

- `docs` Website
  - `t` Protobuf files with geo-located Wikipedia article titles
- `process` Protobuf-generation process

## Micro-optimizations

### Show labels on the points of interest, so I know what each map marker is.



### Instead of showing all articles, prioritize popular articles.

I want to explore a neighborhood, I am likely to want to learn about
more-popular pages before less-popular pages. This will tend to reinforce
the Matthew effect.

### Use 14-kB packets.

Data files up to 14 kB will be sent all at once, without needing to await a
TCP ack.

### Try to minimize network calls.

Compress the data transmitted over the wire with protobuf encoding.
Provide points of interest at the lowest zoom level possible, and don't
provide unnecessarily-high resolution data.



## Comparison to Alternatives

This site:

- Shows only a few points. Does not suggest where there might be more points.
- Provides labels on the (user-selectable) N most popular drawn points.
- Extremely fast.
- leaflet + OpenStreetMap

https://wikimap.wiki/

- Shows all points - gives an idea of the global distribution of all articles.
- Many points get labels as you zoom in.
- Some points do not get labels and you still have to click, which is a slow load.
- Clicking will search a small-radius lat,lon
- Only supports discrete zoom levels.
- Multilingual
- OpenStreetMap

https://wikimapped.mukul-mehta.in/

- Starts with heatmap of articles, becoming points-of-interest as you zoom in.
- Points within a perceptually tight lat/lon (radius varies by zoom) are rendered on the same dialog box.
- No labels on points-of-interest, must tap each individually to discover what it is about.
- Loads quickly.
- React and minified JS.
- Stadia Maps, OpenMapTiles, OpenStreetMap

https://wikiexplore.org/

- No labels on points-of-interest, must tap each individually to discover what it is about.
- Only loads points-of-interest at high-enough zoom.
- Loads quickly.
- Multilingual
- Mapbox + OpenStreetMap

https://wiki-map.com/

- Coalesces points into clusters.
- Distinct article points-of-interest drop onto the map as you zoom in.
- No labels on points-of-interest, must tap each individually to discover what it is about.
- Loads quickly.
- Google

https://wikimaps.vercel.app/

- Based on https://www.mediawiki.org/wiki/API:Nearby_places_viewer
- Colors points-of-interest by category.
- Used to be very slow. Now faster but still poky.
- leaflet + OpenStreetMap
