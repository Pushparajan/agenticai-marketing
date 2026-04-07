# Klaviyo API Setup Guide

## Step 1: Create a Free Account

1. Go to [klaviyo.com](https://www.klaviyo.com) and sign up
2. Free tier supports up to 250 contacts

## Step 2: Generate an API Key

1. **Settings → API Keys**
2. Create a **Private API Key** with scopes:
   - Profiles (read/write)
   - Flows (read/write)
   - Campaigns (read/write)
   - Metrics (read)
   - Lists (read/write)

## Step 3: Add to .env

```bash
KLAVIYO_API_KEY=pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KLAVIYO_LIST_ID_CONSIDERATION=abc123
KLAVIYO_LIST_ID_ONBOARDING=def456
```

## Step 4: Create Test Lists

1. **Audience → Lists & Segments**
2. Create: `Consideration Nurture` and `Onboarding Welcome`
3. Add the list IDs to your `.env`

## Stages Using Klaviyo

- Stage 1: Awareness (nurture enrolment)
- Stage 2: Consideration (flow creation, contact enrolment)
- Stage 3: Decision (close offer emails, urgency campaigns)
- Capstone: All via MCP email server
