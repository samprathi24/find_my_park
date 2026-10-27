import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

function getColor(lot) {
  const ratio = lot.freeSlots / lot.totalSlots;
  if (ratio > 0.3) return "#22c55e"; // green
  if (ratio > 0.1) return "#f59e0b"; // orange
  return "#ef4444"; // red
}

function makeIcon(lot) {
  return L.divIcon({
    className: "",
    html: `<div class="pin" style="background:${getColor(lot)}"></div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

export default function MapView({ lots, center = [13.3379, 77.1173] }) {
  return (
    <MapContainer
      center={center}
      zoom={14}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {lots.map((lot) => (
        <Marker key={lot.id} position={[lot.lat, lot.lng]} icon={makeIcon(lot)}>
          <Popup>
            <strong>{lot.name}</strong>
            <br />
            Free: {lot.freeSlots} / {lot.totalSlots}
            <br />
            Predicted free: {lot.predictedFree}
            <br />
            Distance: {lot.distanceKm} km
            <br />
            Traffic: {lot.traffic}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
