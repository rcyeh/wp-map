# wp-map: Wikipedia x Map

Show Wikipedia articles with coordinates near a neighborhood, to facilitate
local discovery.

URL: https://rcyeh.github.io/wp-map/

## Repo organization

* `docs` Website
  * `t` Protobuf files with geo-located Wikipedia article titles
* `process` Protobuf-generation process

## Comparison to Alternatives

This site:

- Shows only a few points. Does not suggest where there might be more points.
- With labels on every drawn point.
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

