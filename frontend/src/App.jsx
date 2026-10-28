import { useEffect, useState } from "react";
import "./App.css";
import { fetchParkingLots } from "./api/parking";
import MapView from "./components/MapView";

const forecastDisclaimer =
  "60-minute forecasts use the latest YOLO occupancy counts and Birmingham parking history.";

function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true">
        P
      </span>
      <span>FindMyPark</span>
    </span>
  );
}

function App() {
  const [showMap, setShowMap] = useState(false);
  const [parkingLots, setParkingLots] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [forecastError, setForecastError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function refreshParkingLots() {
      try {
        const latestLots = await fetchParkingLots(controller.signal);
        setParkingLots(latestLots);
        setForecastError("");
      } catch (error) {
        if (!controller.signal.aborted) {
          setForecastError(error.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    refreshParkingLots();
    const refreshInterval = window.setInterval(refreshParkingLots, 5000);

    return () => {
      controller.abort();
      window.clearInterval(refreshInterval);
    };
  }, []);

  const liveLots = parkingLots.filter(
    (lot) => lot.detectionStatus === "live",
  );
  const hasDetectionData = parkingLots.some(
    (lot) => lot.detectionStatus !== "waiting_for_yolo",
  );
  const predictedAvailableSlots = liveLots.reduce(
    (total, lot) => total + lot.predictedFree,
    0,
  );
  const featuredLot = liveLots[0] ?? parkingLots[0];

  if (showMap) {
    return (
      <main className="map-screen">
        <header className="map-header">
          <Brand />
          <span className="map-heading">Birmingham city centre parking</span>
          <button
            className="button button-secondary map-back"
            onClick={() => setShowMap(false)}
            type="button"
          >
            Back to home
          </button>
        </header>
        <div className="forecast-notice" role="note">
          {forecastDisclaimer}
        </div>
        <p className="forecast-source">
          Grey markers are awaiting YOLO data. Counts older than five minutes
          are marked stale.
        </p>
        {isLoading && (
          <p className="forecast-status" role="status">
            Loading demo forecasts…
          </p>
        )}
        {forecastError && (
          <p className="forecast-error" role="alert">
            Could not load parking forecasts: {forecastError}
          </p>
        )}
        <div className="map-wrapper">
          <MapView lots={parkingLots} />
        </div>
      </main>
    );
  }

  return (
    <main className="landing-page">
      <header className="landing-header">
        <a className="brand-link" href="#home" aria-label="FindMyPark home">
          <Brand />
        </a>
        <nav className="landing-nav" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#why-findmypark">Why FindMyPark</a>
        </nav>
        <button
          className="button button-primary header-cta"
          onClick={() => setShowMap(true)}
          type="button"
        >
          Explore map <span aria-hidden="true">→</span>
        </button>
      </header>

      <section className="hero-section" id="home">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="status-dot" aria-hidden="true" />
            SMARTER PARKING STARTS HERE
          </p>
          <h1>
            Less time searching.
            <br />
            <span>More time moving.</span>
          </h1>
          <p className="hero-description">
            Find Birmingham parking locations and see 60-minute availability
            forecasts based on the latest occupancy detected by YOLO.
          </p>
          <div className="hero-actions">
            <button
              className="button button-primary hero-cta"
              onClick={() => setShowMap(true)}
              type="button"
            >
              Find parking <span aria-hidden="true">→</span>
            </button>
            <a className="text-link" href="#how-it-works">
              See how it works <span aria-hidden="true">↓</span>
            </a>
          </div>
          <div className="availability-note">
            <span className="availability-icon" aria-hidden="true">i</span>
            <span>
              {isLoading
                ? "Loading Birmingham parking locations…"
                : forecastError
                  ? "Parking data is unavailable."
                  : liveLots.length === 0
                    ? hasDetectionData
                      ? "YOLO readings are stale; waiting for fresh detections."
                      : "Waiting for YOLO occupancy detections."
                    : (
                      <>
                        <strong>{predictedAvailableSlots} spaces</strong>{" "}
                        predicted free in 60 minutes across {liveLots.length}{" "}
                        locations with live detections
                      </>
                    )}
            </span>
          </div>
          <p className="forecast-disclaimer">{forecastDisclaimer}</p>
          {forecastError && (
            <p className="forecast-error" role="alert">
              Could not load parking forecasts: {forecastError}
            </p>
          )}
        </div>

        <div
          className="hero-visual"
          role="img"
          aria-label="Preview of Birmingham parking locations and YOLO availability"
        >
          <div className="visual-topline">
            <span className="visual-label">BIRMINGHAM CITY CENTRE</span>
            <span className="live-badge">
              <span className="status-dot" aria-hidden="true" />
              {liveLots.length > 0
                ? "YOLO LIVE"
                : hasDetectionData
                  ? "YOLO DATA STALE"
                  : "WAITING FOR YOLO"}
            </span>
          </div>
          <div className="preview-map" aria-hidden="true">
            <div className="map-grid" />
            <svg className="map-route" viewBox="0 0 520 320" fill="none">
              <path
                d="M66 248C117 247 113 188 175 190C233 192 219 113 280 126C341 140 319 211 382 207C431 204 423 116 482 78"
                stroke="#ffffff"
                strokeWidth="20"
                strokeLinecap="round"
              />
              <path
                d="M66 248C117 247 113 188 175 190C233 192 219 113 280 126C341 140 319 211 382 207C431 204 423 116 482 78"
                stroke="#567765"
                strokeWidth="3"
                strokeDasharray="7 9"
                strokeLinecap="round"
              />
            </svg>
            <span className="road road-one" />
            <span className="road road-two" />
            <span className="road road-three" />
            <span className="map-place place-one">Bull Ring</span>
            <span className="map-place place-two">Arena Birmingham</span>
            <span className="map-place place-three">Broad Street</span>
            <span className="map-pin pin-one"><i /></span>
            <span className="map-pin pin-two"><i /></span>
            <span className="map-pin pin-three"><i /></span>
            <span className="you-are-here">
              <span /> BIRMINGHAM
            </span>
          </div>
          <div className="lot-preview">
            <span className="lot-icon" aria-hidden="true">P</span>
            <span className="lot-details">
              <strong>{featuredLot?.name ?? "Birmingham parking"}</strong>
              <span>
                {featuredLot
                  ? featuredLot.detectionStatus === "live"
                    ? `${featuredLot.currentOccupancy} occupied · YOLO live`
                    : "Waiting for YOLO occupancy data"
                  : "Loading Birmingham parking locations…"}
              </span>
            </span>
            <span className="lot-spaces">
              <strong>
                {featuredLot?.detectionStatus === "live"
                  ? featuredLot.predictedFree
                  : "—"}
              </strong>
              <span>predicted free</span>
            </span>
          </div>
        </div>
      </section>

      <section className="how-section" id="how-it-works">
        <div className="section-heading">
          <p className="eyebrow">A BETTER WAY TO PARK</p>
          <h2>Make every stop simpler</h2>
          <p>From finding a spot to getting on with your day.</p>
        </div>
        <div className="steps-grid">
          <article className="step-card">
            <span className="step-number">01</span>
            <h3>Explore nearby lots</h3>
            <p>See parking locations around you on one easy-to-read map.</p>
          </article>
          <article className="step-card">
            <span className="step-number">02</span>
            <h3>Check availability</h3>
            <p>Compare listed open spaces before you head to a location.</p>
          </article>
          <article className="step-card">
            <span className="step-number">03</span>
            <h3>Choose your next stop</h3>
            <p>Pick a convenient option and spend less time circling around.</p>
          </article>
        </div>
      </section>

      <section className="closing-section" id="why-findmypark">
        <div>
          <p className="eyebrow">YOUR NEXT SPACE IS CLOSER</p>
          <h2>Ready to find a spot?</h2>
          <p>Explore Birmingham parking and the latest YOLO-based forecasts.</p>
        </div>
        <button
          className="button button-light"
          onClick={() => setShowMap(true)}
          type="button"
        >
          Open parking map <span aria-hidden="true">→</span>
        </button>
      </section>

      <footer className="landing-footer">
        <Brand />
        <span>Parking made simpler in Birmingham.</span>
      </footer>
    </main>
  );
}

export default App;
