//  <script
//    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
//    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
//    crossorigin=""
//  ></script>

// 1. Initialize the map and set its center and zoom level
var map = L.map("map").setView([51.505, -0.09], 13);

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
    const url = `http://localhost:8000/tiles/${coords.z}/${coords.x}/${coords.y}.pbf`;

    fetch(url)
      .then((response) => response.arrayBuffer())
      .then((buffer) => {
        const data = decodePBF(buffer); // Using a library like pbf or your custom parser

        // 1. Sort by popularity (if not already done server-side)
        const sortedPois = data.sort((a, b) => b.rank - a.rank);

        // 2. Filter by user-selected category (e.g., 'museum')
        const activeCategory = document.getElementById("filter").value;
        const filtered = sortedPois.filter(
          (poi) => activeCategory === "all" || poi.category === activeCategory,
        );

        // 3. Render top 10 with labels, others as dots
        filtered.forEach((poi, index) => {
          this.renderPoint(tile, poi, index < 10);
        });
      });

    return tile;
  },

  renderPoint: function (tile, poi, showLabel) {
    // Logic to place the point on the tile relative to coords
    // showLabel ? createTextLabel(poi.title) : createSmallDot();
  },
});

// 3. Add your marker with a permanent label (as discussed before)
// Your data points
const locations = [
  {
    name: "London",
    lat: 51.505,
    lon: -0.09,
    url: "https://en.wikipedia.org/wiki/London",
  },
  {
    name: "Paris",
    lat: 48.856,
    lon: 2.352,
    url: "https://en.wikipedia.org/wiki/Paris",
  },
  {
    name: "Berlin",
    lat: 52.52,
    lon: 13.404,
    url: "https://en.wikipedia.org/wiki/Berlin",
  },
];

// Loop through the data to create markers
locations.forEach((loc) => {
  const customIcon = L.divIcon({
    // We wrap the icon AND the label in the same anchor tag
    html: `
      <a href="${loc.url}" target="_blank" class="marker-link-container" aria-label="Wikipedia: ${loc.name}">
        <img src="https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png" class="marker-img">
        <span class="marker-label">${loc.name}</span>
      </a>`,
    className: "custom-div-icon", // Use this to remove default Leaflet styles
    iconSize: null,
    iconAnchor: [0, 41],
  });
  const marker = L.marker([loc.lat, loc.lon], { icon: customIcon }).addTo(map);

  // Bind a popup with an HTML hyperlink
  // marker.bindPopup(`
  // <a href="${loc.url}" target="_blank" rel="noopener noreferrer">
  // ${loc.name}
  // </a>
  // `, {
  // autoClose: false,
  // closeButton: false,
  // closeOnClick: false,
  // closeOnEscapeKey: false,
  // closePopupOnClick: false,
  // //closeOnMouseout: false
  // }).openPopup();
  // marker.bindTooltip(`
  // <a href="${loc.url}" target="_blank" rel="noopener noreferrer">
  //   ${loc.name}
  // </a>
  // `, {
  //   permanent: true,
  //   interactive: true,
  //   // autoClose: false,
  //   // closeButton: false,
  //   // closeOnClick: false,
  //   // closeOnEscapeKey: false,
  //   // closePopupOnClick: false,
  //   // //closeOnMouseout: false
  // });
  // marker.on('click', function() {
  //   window.open(`${loc.url}`, "_blank");
  // });
});
