# epss_api.py
import requests
from typing import Dict, List

def fetch_epss_scores(cve_list: List[str]) -> Dict[str, float]:
    """
    Fetches EPSS scores for a list of CVE IDs from the FIRST.org API.
    
    Args:
        cve_list: A list of CVE IDs (e.g., ["CVE-2023-12345", "CVE-2024-67890"]).
        
    Returns:
        A dictionary mapping CVE IDs to their EPSS scores. 
        Returns an empty dictionary if the request fails or no data is found.
    """
    if not cve_list:
        return {}

    # The API allows multiple CVEs separated by commas.
    cves_string = ",".join(cve_list)
    api_url = f"https://api.first.org/data/v1/epss?cve={cves_string}"
    
    try:
        # It's good practice to include a descriptive User-Agent
        headers = {'User-Agent': 'Python/EPSS-Harvester'} 
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        
        epss_mapping = {}
        for item in data.get('data', []):
             # The API returns the score as a string, we need to convert it to a float
             cve_id = item.get('cve')
             score_str = item.get('epss')
             if cve_id and score_str:
                 epss_mapping[cve_id] = float(score_str)
                 
        return epss_mapping
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching EPSS data: {e}")
        return {}
    except Exception as e:
         print(f"❌ Unexpected error processing EPSS data: {e}")
         return {}

# Simple test block (only runs if the script is executed directly)
if __name__ == "__main__":
    test_cves = ["CVE-2023-38545", "CVE-2023-38546"]
    print(f"Testing EPSS API with CVEs: {test_cves}")
    scores = fetch_epss_scores(test_cves)
    print(f"Resulting mapping: {scores}")