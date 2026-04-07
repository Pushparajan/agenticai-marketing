# HubSpot API Setup Guide

## Step 1: Create a Developer Account

1. Go to [developers.hubspot.com](https://developers.hubspot.com)
2. Sign up for a free developer account
3. Create a test portal (sandbox)

## Step 2: Create a Private App

1. **Settings → Integrations → Private Apps**
2. Click **Create a private app**, name it `AgenticAI Journey`
3. Enable scopes:
   - `crm.objects.contacts.read` / `.write`
   - `crm.objects.deals.read` / `.write`
   - `crm.objects.companies.read`
   - `automation`
4. Copy the access token

## Step 3: Add to .env

```bash
HUBSPOT_API_KEY=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HUBSPOT_PORTAL_ID=12345678
```

## Step 4: Configure Webhooks (Optional)

For the Stage 1 webhook receiver (`stage1_awareness/project_demand_gen/webhook_receiver.py`):

1. **Settings → Integrations → Webhooks**
2. Set target URL to your FastAPI endpoint
3. Subscribe to `contact.creation` and `contact.propertyChange`
4. Set your HMAC secret in `.env` as `WEBHOOK_SECRET`

## Stages Using HubSpot

- Stage 1: Awareness (create contacts, score intent)
- Stage 2: Consideration (lifecycle stage updates)
- Stage 3: Decision (deal management, task creation)
- Stage 4: Onboarding (onboarding tasks)
- Stage 5: Retention (contract data, expansion tracking)
- Stage 6: Advocacy (advocate identification)
- Capstone: All of the above via MCP CRM server
