let allResorts = [];
let fuse;
let map;
let markersLayer;

async function init() {
  // Initialize Leaflet Map
  map = L.map('map').setView([25, -40], 2);
  L.tileLayer('https://{s}://{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 18
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);

  // Load JSON data
  const response = await fetch('hotels.json');
  allResorts = await response.json();

  // Setup Fuse.js fuzzy search
  fuse = new Fuse(allResorts, {
    keys: ['name', 'brand', 'city', 'state', 'country'],
    threshold: 0.35
  });

  populateFilters();
  render(allResorts);

  // Event Listeners
  document.getElementById('searchInput').addEventListener('input', applyFilters);
  document.getElementById('brandFilter').addEventListener('change', applyFilters);
  document.getElementById('countryFilter').addEventListener('change', applyFilters);
  document.getElementById('resetBtn').addEventListener('click', () => {
    document.getElementById('searchInput').value = '';
    document.getElementById('brandFilter').value = 'ALL';
    document.getElementById('countryFilter').value = 'ALL';
    render(allResorts);
    map.setView([25, -40], 2);
  });
}

function populateFilters() {
  const brands = [...new Set(allResorts.map(r => r.brand))].sort();
  const countries = [...new Set(allResorts.map(r => r.country).filter(Boolean))].sort();

  const brandSelect = document.getElementById('brandFilter');
  brands.forEach(b => {
    const opt = document.createElement('option');
    opt.value = b;
    opt.textContent = b;
    brandSelect.appendChild(opt);
  });

  const countrySelect = document.getElementById('countryFilter');
  countries.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    countrySelect.appendChild(opt);
  });
}

function applyFilters() {
  const query = document.getElementById('searchInput').value.trim();
  const brand = document.getElementById('brandFilter').value;
  const country = document.getElementById('countryFilter').value;

  let filtered = query ? fuse.search(query).map(res => res.item) : [...allResorts];

  if (brand !== 'ALL') {
    filtered = filtered.filter(r => r.brand === brand);
  }
  if (country !== 'ALL') {
    filtered = filtered.filter(r => r.country === country);
  }

  render(filtered);
}

function render(resorts) {
  const listEl = document.getElementById('resortList');
  const countEl = document.getElementById('resultCount');
  countEl.textContent = `Showing ${resorts.length} of ${allResorts.length} eligible resorts`;

  listEl.innerHTML = '';
  markersLayer.clearLayers();

  const bounds = [];

  resorts.forEach(resort => {
    const locationText = [resort.city, resort.state, resort.country].filter(Boolean).join(', ');
    const hiltonSearchUrl = `https://hilton.com{encodeURIComponent(resort.name)}`;

    // Build List Card
    const card = document.createElement('div');
    card.className = 'bg-white p-4 rounded-xl border border-slate-200 hover:border-blue-500 shadow-sm transition cursor-pointer';
    card.innerHTML = `
      <div class="flex justify-between items-start gap-3">
        <div>
          <span class="inline-block text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-800 mb-1.5">
            ${resort.brand}
          </span>
          <h2 class="font-bold text-slate-900 text-base leading-snug">${resort.name}</h2>
          <p class="text-slate-500 text-xs mt-1">${locationText || 'Location pending geocoding'}</p>
        </div>
        <a href="${hiltonSearchUrl}" target="_blank" rel="noopener" onclick="event.stopPropagation()"
           class="shrink-0 text-xs font-semibold bg-blue-900 hover:bg-blue-800 text-white px-3 py-1.5 rounded-lg transition">
          Hilton &rarr;
        </a>
      </div>
    `;

    // Add Map Marker if coordinates exist
    if (resort.lat && resort.lng) {
      const marker = L.marker([resort.lat, resort.lng])
        .bindPopup(`<strong>${resort.name}</strong><br><span style="font-size:12px;color:#555">${resort.brand}</span><br><a href="${hiltonSearchUrl}" target="_blank">View on Hilton.com</a>`);
      markersLayer.addLayer(marker);
      bounds.push([resort.lat, resort.lng]);

      card.addEventListener('click', () => {
        map.flyTo([resort.lat, resort.lng], 13, { duration: 1 });
        marker.openPopup();
      });
    }

    listEl.appendChild(card);
  });

  if (bounds.length > 0 && resorts.length < allResorts.length) {
    map.fitBounds(bounds, { padding:, maxZoom: 12 });
  }
}

init();
