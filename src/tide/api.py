import os
import json
import requests

from tide.utils import get_project_root


def fetch_admiralty_tides(api_key: str, station_id: str, n_days: int = 1):
    """Fetch tide data from admiralty discovery API"""
    url = (
        "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/"
        f"Stations/{station_id}/TidalEvents?duration={n_days}"
    )
    headers = {"Ocp-Apim-Subscription-Key": api_key}

    print(f"[Admiralty Discovery API] Querying station {station_id}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    print("Calling Admiralty Discovery API")

    API_KEY = os.getenv("ADMIRALTY_DISCOVERY_API_KEY")
    STATION = "0023C"  # Totnes

    # script_dir = Path(__file__).resolve().parents[2]
    project_root = get_project_root()
    cache_dir = project_root / ".cache"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"admiralty_response_{STATION}.json"

    try:
        raw_data = fetch_admiralty_tides(API_KEY, STATION)
        pretty_json = json.dumps(raw_data, indent=2)
        cache_file.write_text(pretty_json)
        print(pretty_json)
    except Exception as e:
        print(f"[ERROR] API fetch failed: {e}")
        exit(1)
