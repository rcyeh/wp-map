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
const markersOnMap = new Map(); // Key: point.id, Value: Leaflet Marker instance
const downloadedTiles = new Set(); // Tracks fileKeys already fetched

async function initTileRegistry(url = "t/tile_set_list.pbf") {
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

function waitForGlobal(variableName, callback, nextCheckMs = 100) {
  if (window[variableName]) {
    callback();
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
waitForGlobal("L", initMap);

function initMap() {
  // 1. Initialize the map and set its center and zoom level
  map = L.map("map").setView([51.505, -0.09], 13);
  // 1. The Global Marker Layer
  markerLayer = L.layerGroup().addTo(map);

  let moveTimeout;
  map.on("moveend", () => {
    clearTimeout(moveTimeout);
    moveTimeout = setTimeout(updateMapDisplay, 500);
  });

  // 2. Add the OpenStreetMap tiles
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  // Example: Loading and filtering Wikipedia POIs from your custom tile server
  const poiLayer = L.GridLayer.extend({
    createTile: function (coords) {
      const tile = document.createElement("div");
      fetchDataFor(coords);
      return tile;
    },
  });

  new poiLayer().addTo(map);
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
  const marker = L.marker([loc.lat, loc.lon], { icon: customIcon });
  return marker;
}

function createCustomDot(loc) {
  const minorPoi = L.circleMarker([loc.lat, loc.lon], {
    radius: 4,
    fillColor: "#0078ff",
    color: "#fff",
    weight: 1,
    fillOpacity: 0.3,
  });
  minorPoi.on("click", () => {
    window.open(loc.url, "_blank", "nooopener,noreferrer");
  });
  return minorPoi;
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

  for (const [name, marker] of markersOnMap.entries()) {
    if (!nextIds.has(name)) {
      markerLayer.removeLayer(marker);
      markersOnMap.delete(name);
    }
  }
  pointsToDisplay.forEach((p) => {
    if (!markersOnMap.has(p.name)) {
      const marker = createCustomMarker(p);
      markerLayer.addLayer(marker);
      markersOnMap.set(p.name, marker);
    }
  });
  inView.slice(maxPointsOfInterest, maxPointsOfInterest * 4).forEach((p) => {
    if (!markersOnMap.has(p.name)) {
      const marker = createCustomDot(p);
      markerLayer.addLayer(marker);
      // markersOnMap.set(p.name, marker);
    }
  });
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

function getBestAvailableTile(z, x, y) {
  let currentZ = z;
  let currentX = x;
  let currentY = y;
  // Walk up the tree until we find a tile that actually exists in our index
  while (currentZ >= 0) {
    if (
      binarySearch(tileSetCache[currentZ], ((currentX << 15) | currentY) >>> 0)
    ) {
      // Found it! Return the coordinates of the file we need to fetch
      return { z: currentZ, x: currentX, y: currentY };
    }
    // Target next lower zoom level using floor division math
    currentZ = currentZ - 1;
    currentX = currentX >> 1; // Bitwise equivalent of Math.floor(x / 2)
    currentY = currentY >> 1; // Bitwise equivalent of Math.floor(y / 2)
  }
  return null; // Truly empty part of the world (e.g., mid-ocean)
}

async function fetchDataFile(fileKey) {
  if (downloadedTiles.has(fileKey)) return;
  downloadedTiles.add(fileKey);

  try {
    // console.log(`fetching t/${fileKey}.pbf`);
    const response = await fetch(`t/${fileKey}.pbf`);
    const buffer = await response.arrayBuffer();
    const wikiGeoDataList = WikiGeoDataList.fromBinary(new Uint8Array(buffer));
    // console.log(`Fetched ${JSON.stringify(wikiGeoDataList)}`);
    wikiGeoDataList.items.forEach((wgd) => {
      // Use point ID to ensure unique entry in global registry
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

        // console.log(`Saving ${JSON.stringify(p)}`);
        pointRegistry.set(p.name, p);
      }
    });
    // console.log(`updateMapDisplay`);
    updateMapDisplay(); // Trigger your 5-100 point filter
  } catch (error) {
    // Handle missing tiles (e.g., ocean or empty areas)
    console.error(error);
    console.log(`No data for ${fileKey}`);
    downloadedTiles.delete(fileKey);
  }
}

function fetchDataFor(coords) {
  // This logic to move to tileTree.
  // Map (coords.z, coords.x, coords.y) -> fetchKey

  const availableZ = Math.max(0, Math.min(15, coords.z));
  const zoomFactor = Math.pow(2, availableZ - coords.z);
  const currentX = Math.floor(coords.x * zoomFactor);
  const currentY = Math.floor(coords.y * zoomFactor);

  const tile = getBestAvailableTile(availableZ, currentX, currentY);
  if (!tile) {
    return;
  }
  const fetchKey = `${tile.z}/${tile.x}/${tile.y}`;

  console.log(
    `${coords} (${JSON.stringify(coords)}) -> fetchKey = ${fetchKey}`,
  );

  fetchDataFile(fetchKey);

  // const url = `http://localhost:8000/tiles/${coords.z}/${coords.x}/${coords.y}.pbf`;

  // .then((response) => response.arrayBuffer())
  // .then((buffer) => {
  //   const data = decodePBF(buffer); // Using a library like pbf or your custom parser

  //   // 2. Filter by user-selected category (e.g., 'museum')
  //   const activeCategory = document.getElementById("filter").value;
  //   const filtered = sortedPois.filter(
  //     (poi) => activeCategory === "all" || poi.category === activeCategory,
  //   );

  // // 3. Render top 10 with labels, others as dots
  // filtered.forEach((poi, index) => {
  //   this.renderPoint(tile, poi, index < 10);
  // });
}
