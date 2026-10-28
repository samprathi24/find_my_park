import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

function getColor(lot) {
  if (lot.detectionStatus !== "live" || lot.freeSlots == null) return "#64748b";

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

export default function MapView({ lots, center = [52.4796, -1.9045] }) {
  return (
    <MapContainer
      center={center}
      zoom={13}
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
            Capacity: {lot.totalSlots}
            <br />
            {lot.detectionStatus === "waiting_for_yolo" ? (
              "Waiting for YOLO occupancy data"
            ) : (
              <>
                Current occupied: {lot.currentOccupancy}
                <br />
                Current free: {lot.freeSlots}
                <br />
                Predicted free in 60 min: {lot.predictedFree}
                <br />
                Detection: {lot.detectionStatus}
              </>
            )}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}