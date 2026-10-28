export async function fetchParkingLots(signal) {
  const response = await fetch("/api/parking", { signal });
  if (!response.ok) {
    const details = await response.text();
    throw new Error(
      `Could not load Birmingham parking data (${response.status}): ${details}`,
    );
  }

  const data = await response.json();
  if (!Array.isArray(data.lots)) {
    throw new Error("Parking API returned an invalid list of locations.");
  }

  return data.lots.map((lot) => ({
    id: lot.id,
    name: lot.name,
    lat: lot.lat,
    lng: lot.lng,
    totalSlots: lot.capacity,
    freeSlots: lot.free_slots,
    currentOccupancy: lot.current_occupancy,
    predictedFree: lot.predicted_available,
    predictedOccupied: lot.predicted_occupied,
    detectedAt: lot.detected_at,
    detectionStatus: lot.detection_status,
  }));
}
