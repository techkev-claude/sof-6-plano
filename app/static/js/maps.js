function initMap(containerId, tripData) {
  const map = L.map(containerId, {
    center: [48.2082, 16.3738],
    zoom: 12,
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map);

  const bounds = [];
  const colors = {};

  if (tripData && tripData.legs) {
    tripData.legs.forEach(leg => {
      if (!leg.time_blocks) return;
      const legPoints = [];

      leg.time_blocks.forEach(block => {
        if (!block.lat || !block.lng) return;
        const latlng = [block.lat, block.lng];
        bounds.push(latlng);
        legPoints.push(latlng);

        const icon = {
          sightseeing: '🏛️', food: '🍽️', transport: '🚇',
          accommodation: '🏨', break: '☕', other: '📍'
        }[block.block_type] || '📍';

        L.marker(latlng, {
          icon: L.divIcon({
            html: `<div class="text-lg">${icon}</div>`,
            className: '',
            iconSize: [24, 24],
          })
        }).bindPopup(`<strong>${block.title}</strong><br>${block.start_datetime}`).addTo(map);
      });

      if (legPoints.length > 1) {
        L.polyline(legPoints, { color: leg.color || '#6366f1', weight: 3, opacity: 0.8 }).addTo(map);
      }
    });
  }

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [40, 40] });
  }
}
