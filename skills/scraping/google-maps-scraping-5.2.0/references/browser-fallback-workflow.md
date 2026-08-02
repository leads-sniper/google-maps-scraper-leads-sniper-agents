# Browser Fallback: Scraping Google Maps Without Leads Sniper

When the Leads Sniper API queue is stuck (extension connected but not processing jobs), scrape individual listings directly via the Hermes browser tool.

## Detection

```json
GET /v1/status
{"active_jobs": 0, "extension_connected": true, "queued_jobs": 12, "status": "online"}
```

If `queued_jobs` is growing and no recent entries appear in `/v1/logs`, the extension is stalled. The POST endpoint will hang indefinitely.

## Workflow

### 1. Navigate to search results

```
https://www.google.com/maps/search/pizza+Dubai/
```

The browser snapshot shows a feed of `article` elements, each containing:
- A link with the place name
- Star rating image
- Category text
- Address
- Hours status
- Action buttons (Order online, Reserve a table)

### 2. Extract place URLs from the feed

Use the browser console to extract direct place links:

```js
Array.from(document.querySelectorAll('a[href*="/place/"]'))
  .slice(0,10)
  .map(a => a.href)
```

Returns URLs like:
```
https://www.google.com/maps/place/Naughty+Pizza+Dubai/data=!4m7!3m6!...
```

### 3. Navigate to each place page

Each place page has a detail panel under `main` containing these fields:

| Field | Snapshot element | Notes |
|-------|-----------------|-------|
| Name | `h1` heading | Top of the panel |
| Rating | `img[alt*="stars"]` | e.g. "4.8 stars" |
| Category | Button text | e.g. "Pizza restaurant" |
| Address | Button with "Address:" prefix | Full street address |
| Hours | Button with "Open · Closes" text | Hours status |
| Website | `link` with "Website:" prefix | URL text |
| Phone | Button with "Phone:" prefix | Full phone number |
| Plus code | Button with "Plus code:" prefix | Grid reference |

### 4. Data extraction strategy

The snapshot's accessibility tree gives structured data — no need for raw HTML parsing:

```
- generic "Information for Naughty Pizza Dubai"
  - generic
    - button "Address: Vezul Residence - Business Bay - Dubai - United Arab Emirates"
  - generic
    - button "Open · Closes 12 AM · See more hours"
  - generic
    - link "Website: naughty.pizza"
  - generic
    - button "Phone: +971 4 426 9991"
```

Read the `StaticText` values from the snapshot to get field data.

### 5. Limitations

- **Limited view:** Without signing in, Google Maps shows only ~5 results per query
- **Rate limiting:** Google's bot detection may trigger CAPTCHA after several searches
- **No bulk export:** Manual extraction of each place — suitable for small lists (< 20)
- **No email scraping:** Unlike Leads Sniper's `extract_emails`, the browser view doesn't show emails

### 6. When to use this fallback

- Leads Sniper queue is stuck and won't clear
- You need only a handful of listings (≤ 20)
- You need structured detail (phone, address, website) for each place
- You're OK with the slower, manual extraction