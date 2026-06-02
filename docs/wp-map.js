import {
  TileSet,
  TileSetList,
  WikiGeoData,
  WikiGeoDataList,
} from "./wpmaps.js";

let map;
let markerLayer;
let tileSetCache = null; // zoom-level-indexed list of sorted tile indices
// List of unique points
const pointRegistry = new Map();
const labeledMarkers = new Map(); // Key: point.id, Value: Leaflet Marker instance
const dotMarkers = new Map(); // Key: point.id, Value: Leaflet Marker instance
const downloadedTiles = new Set(); // Tracks fileKeys already fetched
const MAX_JITTER_DEGREES = 0.00015;
const markerLimit = document.getElementById("marker-limit");

async function initTileRegistry(url = "t/tile_set_list.pbf") {
  // 80 kB delta-encoded integer arrays enumerating available tiles
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to get tile set list");
    const buffer = await response.arrayBuffer();
    const tileSetList = TileSetList.fromBinary(new Uint8Array(buffer));
    tileSetCache = tileSetList.tilesets.map((tileSet) => {
      const deltas = tileSet.deltas;
      if (deltas.length === 0) return new Int32Array(0);
      const tidx = new Int32Array(deltas.length);
      tidx[0] = deltas[0];
      for (let i = 1; i < deltas.length; ++i) {
        tidx[i] = tidx[i - 1] + deltas[i];
      }
      return tidx;
    });
  } catch (error) {
    console.error("Failed initTileRegistry:", error);
  }
}
await initTileRegistry();

async function waitForGlobal(variableName, callback, nextCheckMs = 100) {
  if (window[variableName]) {
    await callback();
  } else {
    setTimeout(
      () => waitForGlobal(variableName, callback, nextCheckMs * 1.5),
      nextCheckMs,
    );
  }
}
//  <script
//    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
//    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
//    crossorigin=""
//  ></script>
await waitForGlobal("L", initMap);

async function initMap() {
  const startLL = await getInitialLatLon();
  // 1. Initialize the map and set its center and zoom level
  map = L.map("map").setView([startLL.lat, startLL.lon], startLL.zoom);
  // 1. The Global Marker Layer
  markerLayer = L.layerGroup().addTo(map);

  let moveTimeout;
  map.on("moveend", () => {
    clearTimeout(moveTimeout);
    moveTimeout = setTimeout(updateMapDisplay, 500);
  });

  markerLimit.addEventListener("change", (event) => {
    updateMapDisplay();
  });

  // 2. Add the OpenStreetMap tiles
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  // Example: Loading and filtering Wikipedia POIs from your custom tile server
  const poiLayer = L.GridLayer.extend({
    createTile: function (tile_idx) {
      const tile = document.createElement("div");
      fetchDataFor(tile_idx);
      return tile;
    },
  });

  new poiLayer().addTo(map);
}

async function getInitialLatLon() {
  // TODO - use an IP geolocation database for an initial guess.
  return { lat: 11.1, lon: 34.2, zoom: 3 };
}

function updateMapDisplay() {
  const bounds = map.getBounds();
  const maxPointsOfInterest = parseInt(
    document.getElementById("marker-limit").value,
  );

  // 1. Get all points currently in view
  let inView = Array.from(pointRegistry.values()).filter((p) =>
    bounds.contains([p.lat, p.lon]),
  );

  // 2. Sort by popularity
  inView.sort((a, b) => b.logrank - a.logrank);

  // 3. Render the top X
  const pointsToDisplay = inView.slice(0, maxPointsOfInterest);
  const nextIds = new Set(pointsToDisplay.map((p) => p.name));

  labeledMarkers.forEach((marker, name) => {
    if (!nextIds.has(name)) {
      markerLayer.removeLayer(marker);
      labeledMarkers.delete(name);
      if (!dotMarkers.has(name) && pointRegistry.has(name)) {
        const dot = createCustomDot(pointRegistry.get(name));
        if (dot) markerLayer.addLayer(dot);
      }
    }
  })
  pointsToDisplay.forEach((p) => {
    if (!labeledMarkers.has(p.name)) {
      const marker = createCustomMarker(p);
      markerLayer.addLayer(marker);
    }
  });
  inView.slice(maxPointsOfInterest, maxPointsOfInterest * 4).forEach((p) => {
    if (!dotMarkers.has(p.name)) {
      const dot = createCustomDot(p);
      if (dot) markerLayer.addLayer(dot);
    }
  });
}

function createCustomMarker(loc) {
  const customIcon = L.divIcon({
    html: `
    <a href="${loc.url}" target="_blank" class="marker-link-container" aria-label="Wikipedia: ${loc.name}">
    <img src="https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png" class="marker-img">
    <span class="marker-label">${loc.name}</span>
    </a>`,
    className: "custom-div-icon", // Use this to remove default Leaflet styles
    iconSize: null,
    iconAnchor: [0, 41],
  });
  const jitterloc = getJitteredCoordinates(loc);
  const marker = L.marker([jitterloc.lat, jitterloc.lon], {
    icon: customIcon,
  });
  labeledMarkers.set(loc.name, marker);
  return marker;
}

function createCustomDot(loc) {
  if (!loc) return null;
  const jitterloc = getJitteredCoordinates(loc);
  const minorPoi = L.circleMarker([jitterloc.lat, jitterloc.lon], {
    radius: 3,
    fillColor: "#0078ff",
    color: "#fff",
    weight: 1,
    fillOpacity: 0.7,
  });
  minorPoi.on("click", () => {
    window.open(loc.url, "_blank", "nooopener,noreferrer");
  });
  dotMarkers.set(loc.name, minorPoi);
  return minorPoi;
}

function getJitteredCoordinates(loc) {
  const hashX = getDeterministicHash("x_" + loc.name) * MAX_JITTER_DEGREES;
  const hashY = getDeterministicHash("y_" + loc.name) * MAX_JITTER_DEGREES;
  return { lat: loc.lat + hashY, lon: loc.lon + hashX };
}

function getDeterministicHash(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  // Convert to a floating point number between -1.0 and 1.0
  return ((hash >>> 0) / 4294967295) * 2 - 1;
}

/**
 * Obtain point-of-interest data for the specified tile.
 * @param {*} tile_idx
 */
async function fetchDataFor(tile_idx) {
  // Map (tile_idx.z, tile_idx.x, tile_idx.y) -> fetchKey
  const fetchAtLowerZoom = 1; // Set to positive values to force fewer network requests
  const availableZ = Math.max(0, Math.min(15, tile_idx.z - fetchAtLowerZoom));
  const zoomLog = tile_idx.z - availableZ;
  const currentX = tile_idx.x >> zoomLog;
  const currentY = tile_idx.y >> zoomLog;
  const tile = lookupBestAvailableTile(availableZ, currentX, currentY);
  if (!tile) {
    return;
  }
  const fetchKey = `${tile.z}/${tile.x}/${tile.y}`;
  await fetchDataFile(fetchKey);
}

/**
 * Transform the requested (z, x, y) tile reference to the nearest available
 * enclosing tile (z, x, y), by looking up the value in the tileSetCache,
 * downloaded earlier.
 *
 * @param {*} z zoom level
 * @param {*} x tile index
 * @param {*} y tile index
 * @returns {z: int, x: int, y: int}
 */
function lookupBestAvailableTile(z, x, y) {
  // Walk up the tree until we find a tile that actually exists in our index
  while (z >= 0) {
    if (tileSetCache && tileSetCache[z] &&
        binarySearch(tileSetCache[z], ((x << 15) | y) >>> 0)) {
      return { z: z, x: x, y: y };
    }
    z -= 1;
    x >>= 1;
    y >>= 1;
  }
  return null; // Truly empty part of the world (e.g., mid-ocean)
}

function binarySearch(array, element) {
  let left = 0;
  let right = array.length - 1;
  while (left <= right) {
    const mid = (left + right) >> 1;
    if (element === array[mid]) {
      return true;
    }
    if (element < array[mid]) {
      right = mid - 1;
    } else {
      left = mid + 1;
    }
  }
  return element === array[left];
}

/**
 * Download the protobuf file for the requested tile.
 * Upon receipt, save each point-of-interest to the
 * pointRegistry, with necessary transformations.
 * Memoize optimistically, to avoid sending multiple requestss for the same
 * tile.
 */
async function fetchDataFile(fileKey) {
  if (downloadedTiles.has(fileKey)) return;
  downloadedTiles.add(fileKey);

  try {
    const response = await fetch(`t/${fileKey}.pbf`);
    const buffer = await response.arrayBuffer();
    const wikiGeoDataList = WikiGeoDataList.fromBinary(new Uint8Array(buffer));
    wikiGeoDataList.items.forEach((wgd) => {
      if (!pointRegistry.has(wgd.name)) {
        const p = {
          name: wgd.name,
          lat: wgd.latitude * 1e-5,
          lon: wgd.longitude * 1e-5,
          logrank: wgd.logrank,
          url: `https://en.wikipedia.org/wiki/${encodeURIComponent(
            wgd.name.replaceAll(" ", "_"),
          )}`,
        };
        pointRegistry.set(p.name, p);
      }
    });
    updateMapDisplay();
  } catch (error) {
    console.error(error);
    console.log(`No data for ${fileKey}`);
    downloadedTiles.delete(fileKey);
  }
}
