# HubSpot API Setup Guide

## Step 1: Create a Developer Account

1. Go to [developers.hubspot.com](https://developers.hubspot.com)
2. Sign up for a free developer account
3. Create a test portal (sandbox) — this gives you a full HubSpot instance with no cost

## Step 2: Create a Private App

1. In your test portal, go to **Settings → Integrations → Private Apps**
2. Click **Create a private app**
3. Name it `AgenticAI Book`
4. Under **Scopes**, enable:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - `crm.objects.companies.read`
   - `automation` (for workflow access)
5. Click **Create app** and copy the access token

## Step 3: Add to .env

```bash
HUBSPOT_API_KEY=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Step 4: Seed Test Data

The sandbox comes with sample contacts, but you can add more:

```python
from hubspot import HubSpot
client = HubSpot(access_token="your-token")
client.crm.contacts.basic_api.create(
    simple_public_object_input_for_create={
        "properties": {
            "email": "test@example.com",
            "firstname": "Test",
            "lastname": "Contact",
            "company": "Acme Corp"
        }
    }
)
```

## Projects Using HubSpot

- Project 1: Customer Journey Digital Twin (read contact history)
- Project 2: SDR Outreach Agent (create tasks, update contacts)
- Project 4: Demand Gen Pipeline (activate workflows)
- Project 5: Journey Orchestrator (lifecycle stage updates)
- Project 8: Command Centre (full CRM server)
