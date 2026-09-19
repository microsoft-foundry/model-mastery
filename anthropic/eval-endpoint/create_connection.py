"""Instructor step: create the project connection Foundry uses to call the
eval endpoint. Run once per workshop project, after the endpoint is deployed.

Uses one ARM REST call with your az login, so no management SDK is needed.
This body was validated against a Foundry project on 2026-09-01 with
api-version 2025-06-01; it now uses 2026-05-01, the current stable version.
Run:  az login && python create_connection.py
"""

import json
import os
import urllib.request

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

subscription = os.environ["AZURE_SUBSCRIPTION_ID"]
resource_group = os.environ["AZURE_RESOURCE_GROUP"]
account = os.environ["FOUNDRY_ACCOUNT_NAME"]          # the Foundry resource name
project = os.environ["FOUNDRY_PROJECT_NAME"]
connection_name = os.environ.get("EVAL_ENDPOINT_CONNECTION", "mm-eval-endpoint")
endpoint_url = os.environ["EVAL_ENDPOINT_URL"]          # https://<host>/evaluate
endpoint_key = os.environ["EVAL_ENDPOINT_API_KEY"]      # Foundry sends it as the api-key header

url = (f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{resource_group}"
       f"/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}"
       f"/connections/{connection_name}?api-version=2026-05-01")
body = {"properties": {"category": "ApiKey", "target": endpoint_url,
                       "authType": "ApiKey", "credentials": {"key": endpoint_key}}}

token = DefaultAzureCredential().get_token("https://management.azure.com/.default").token
req = urllib.request.Request(url, data=json.dumps(body).encode(), method="PUT",
                             headers={"Authorization": f"Bearer {token}",
                                      "Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    out = json.loads(resp.read())
print(f"Created connection '{out['name']}' -> {out['properties']['target']}")
