import { tileTree } from "./t/tile-tree.js";

let map;
let markerLayer;
// List of unique points
const pointRegistry = new Map();
const markersOnMap = new Map(); // Key: point.id, Value: Leaflet Marker instance
const downloadedTiles = new Set(); // Tracks fileKeys already fetched

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

function updateMapDisplay() {
  const bounds = map.getBounds();
  // const userLimit = parseInt(document.getElementById("limit-slider").value);
  const userLimit = 5;

  // 1. Get all points currently in view
  let inView = Array.from(pointRegistry.values()).filter((p) =>
    bounds.contains([p.lat, p.lon]),
  );

  // 2. Sort by popularity
  // inView.sort((a, b) => a.name - b.name);

  // 3. Render the top X
  const pointsToDisplay = inView.slice(0, userLimit);
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
}

function fetchDataFile(fileKey) {
  if (downloadedTiles.has(fileKey)) return;
  downloadedTiles.add(fileKey);

  // fetch(`/data/${fileKey}.json`)
  fetch("t/locations.json")
    .then((res) => (res.ok ? res.json() : []))
    .then((points) => {
      console.log(`Fetched ${points}`);
      points.forEach((p) => {
        // Use point ID to ensure unique entry in global registry
        if (!pointRegistry.has(p.name)) {
          console.log(`Saving ${JSON.stringify(p)}`);
          pointRegistry.set(p.name, p);
        }
      });
      console.log(`updateMapDisplay`);
      updateMapDisplay(); // Trigger your 5-100 point filter
    })
    .catch((e) => {
      // Handle missing tiles (e.g., ocean or empty areas)
      console.error(e);
      console.log(`No data for ${fileKey}`);
      downloadedTiles.delete(fileKey);
    });
}

function fetchDataFor(coords) {
  // This logic to move to tileTree.
  // Map (coords.z, coords.x, coords.y) -> fetchKey
  // Coarsen: e.g., always fetch at 3 zoom levels higher (larger area)
  const fetchZoom = Math.max(0, coords.z - 3);
  const fetchX = Math.floor(coords.x / Math.pow(2, 3));
  const fetchY = Math.floor(coords.y / Math.pow(2, 3));

  const fetchKey = `${fetchZoom}/${fetchX}/${fetchY}`;

  console.log(
    `${coords} (${JSON.stringify(coords)}) -> fetchKey = ${fetchKey}`,
  );

  const debugFetchKey = "locations.json";

  fetchDataFile(debugFetchKey);

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
