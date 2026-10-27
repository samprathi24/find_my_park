import "./App.css";
import MapView from "./components/MapView";
import { parkingLots } from "./data/mockParking";

export default function App() {
  return (
    <div className="map-wrapper">
      <MapView lots={parkingLots} />
    </div>
  );
}
