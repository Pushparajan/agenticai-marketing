# Klaviyo API Setup Guide

## Step 1: Create a Free Account

1. Go to [klaviyo.com](https://www.klaviyo.com) and sign up
2. The free tier supports up to 250 contacts — perfect for testing

## Step 2: Generate an API Key

1. Go to **Settings → API Keys**
2. Create a new **Private API Key**
3. Enable these scopes:
   - Profiles (read/write)
   - Flows (read/write)
   - Campaigns (read/write)
   - Metrics (read)
   - Lists (read/write)

## Step 3: Add to .env

```bash
KLAVIYO_API_KEY=pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 4: Create a Test List

1. Go to **Audience → Lists & Segments**
2. Create a list called `Book Test List`
3. Add a few test profiles manually or via the API

## Projects Using Klaviyo

- Project 4: Demand Gen Pipeline (create flows, enrol contacts)
- Project 5: Journey Orchestrator (send emails via Klaviyo)
- Project 8: Command Centre (email MCP server)
