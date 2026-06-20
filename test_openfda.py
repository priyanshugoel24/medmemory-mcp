import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('OPENFDA_API_KEY')

response = httpx.get("https://api.fda.gov/drug/label.json", params = {
    "search" : "openfda.generic_name:metformin",
    "limit" : 1,
    "api_key" : API_KEY
}, timeout = 10.0)


data= response.json()
result = data["results"][0]

interactions = result.get("drug_interactions", ["No interaction data found"])
print("DRUG INTERACTION FIELD :")
print(interactions[0][:500])


print("\nGENERIC NAME : ")
print(result.get("openfda", {}).get("generic_name", ["unkown"]))