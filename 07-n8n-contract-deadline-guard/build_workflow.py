"""Builds workflow.json from extract.js, so the n8n Code node and the tested code are the same."""
import json, pathlib

here = pathlib.Path(__file__).parent
code = (here / "extract.js").read_text().split("if (typeof module")[0].rstrip()
code += '''

const item = $input.first().json;
const body = item.body || item;
return [{ json: analyse(String(body.text || ""), body.today) }];
'''

workflow = {
    "name": "Contract Deadline Guard",
    "nodes": [
        {"parameters": {"content": "## Contract Deadline Guard\nPOST a contract text to this webhook:\n`{\"text\": \"...\"}`\n\nThe flow finds the notice period and end date, works out the last day to cancel and returns it together with a calendar file (.ics) that reminds you 14 days before.\n\nNo account or key needed. General information, not legal advice.", "height": 260, "width": 420},
         "id": "note", "name": "Read me", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, -40]},
        {"parameters": {"httpMethod": "POST", "path": "contract-deadlines", "responseMode": "responseNode", "options": {}},
         "id": "webhook", "name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
         "webhookId": "contract-deadline-guard"},
        {"parameters": {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": code},
         "id": "extract", "name": "Find deadlines and build calendar file", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [260, 300]},
        {"parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
         "id": "respond", "name": "Respond", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [520, 300]},
    ],
    "connections": {
        "Webhook": {"main": [[{"node": "Find deadlines and build calendar file", "type": "main", "index": 0}]]},
        "Find deadlines and build calendar file": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
    },
    "active": False,
    "settings": {"executionOrder": "v1"},
}
(here / "workflow.json").write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n")
print("workflow.json written")
