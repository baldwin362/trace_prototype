# Trace

Trace takes a company domain and lists the third-party technologies it uses, such as Shopify, Google Workspace, HubSpot or Cloudflare.
It only looks at public data: DNS records, the HTTP response of the homepage, the homepage HTML, and well-known files like `robots.txt`.
Every detection comes with the exact raw string that proves it, so any result can be audited ("why do you think we use this?").
All detection rules live in JSON files; adding a technology never requires touching Python.

```
$ python main.py gymshark.com
gymshark.com
  AWS Route 53                 dns:NS                   ns-947.awsdns-54.net.
  Cloudflare                   http:header_value        server: cloudflare
  Microsoft 365                dns:TXT                  MS=ms54108504
  Proofpoint                   dns:MX                   10 mx07-005a6901.pphosted.com.
  Shopify                      http:header_value        powered-by: Shopify
  Shopify                      http:cookie              cookie: cart_currency
  Shopify                      robots:disallow          Disallow: /checkouts/
  ...
```

## Running it

### With Docker

```
docker build -t trace .
docker run --rm trace gymshark.com
docker run --rm trace --file domains.txt          # the 19 test domains
docker run --rm -p 8000:8000 --entrypoint uvicorn trace backend.api.main:app --host 0.0.0.0
```

### Without Docker (Python 3.11+)

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt         # Windows: .venv\Scripts\pip
.venv/bin/python main.py gymshark.com
```

Useful options:

| Command | What it does |
|---|---|
| `python main.py a.com b.com` | scan several domains at once; each prints as soon as it finishes |
| `python main.py --file domains.txt` | scan one domain per line (`domains.txt` holds the 19 test domains) |
| `python main.py a.com --json > out.json` | one JSON result per line on stdout; logs stay on stderr |
| `python main.py a.com --log-level DEBUG` | also show every network call, unknown key and suppressed key |
| `python main.py a.com --resolver 8.8.8.8` | use another DNS resolver (default `1.1.1.1`) |
| `python main.py a.com --save-artifacts --artifacts-dir ./artifacts` | also write raw fetched data and results to disk |

The API has two endpoints: `POST /scan` with `{"domain": "gymshark.com"}`, and `GET /health`. Interactive docs are at `/docs`.

Tests run against saved real responses and use no network:

```
python -m pytest backend/tests
```

## Architecture

```
main.py                    command line: reads domains, prints results as they finish
backend/
  api/                     FastAPI: POST /scan, GET /health, its own request/response schemas
  domain/
    scanner.py             runs the 4 engines concurrently on one domain and merges their results
    dns/  http/  html/  robots/     the 4 engines, same shape each (see below)
    rules/                 shared matching: mapping loader + exact / prefix / suffix / substring lookups
    models/                the typed objects passed between layers (pydantic)
    errors/                one exception module per engine, all inheriting ScanError
    persistence/           optional: writes raw artifacts and results to disk
  tests/                   pytest, with saved real responses in tests/fixtures/
```

Every engine has the same four layers, so you learn one and you know all four:

```
client  ─────────►  extractors / normalizers  ─────────►  detector  ─────────►  list[Detection]
(network only)      (pure functions:                       (looks each key up
                     raw data → list[ExtractedKey])         in its mapping files)
```

The engine file (`dns_engine.py`, `http_engine.py`...) just wires these together and turns its own errors into an `EngineError`.

**Why the four engines are independent.** Each one looks at a different place where a company leaves a public trace: the DNS records it had to change, the HTTP responses its vendors serve, the code its pages load, and the files at its well-known paths. They don't need each other's data, so no engine imports from another. They run at the same time, each with its own timeout. If one fails (say a site blocks bots) the other three still report, and the failure is recorded in the result.

**Why matching is separate from fetching.** The only code that touches the network is the client of each engine. Everything after it is a pure function from raw data to keys, then from keys to detections. That's why every matching test runs offline against `tests/fixtures/`. It also means raw data saved with `--save-artifacts` could be re-run through new rules without fetching again.

**The contract between layers.** Extractors return `ExtractedKey(key, raw_value, source)`:
- `key` is the normalized lookup key, e.g. `aspmx.l.google.com`.
- `raw_value` is the untouched original, e.g. `10 aspmx.l.google.com.`.

Detectors return `Detection(technology, evidence, source, confidence)`, where `evidence` is that untouched original. Detections are never deduplicated, so three independent pieces of evidence for Shopify stay three lines. The one exception is HTML, where each URL hostname is kept once. Otherwise a page with 120 images on a CMS's CDN would produce 120 identical detections.

## Adding a technology

Edit one JSON file in the mappings folder of the engine where the signal lives. For example, to detect Pipedrive from its domain verification TXT record, add one line to `backend/domain/dns/mappings/txt_token.json`:

```json
"pipedrive-verification": "Pipedrive"
```

Every mapping file declares how it is matched and how much a match is worth:

```json
{
  "lookup_strategy": "suffix",
  "confidence": "high",
  "entries": { "myshopify.com": "Shopify", "cdnjs.cloudflare.com": null }
}
```

Files are validated when the program starts. A typo such as an unknown strategy, or an entry that isn't a string or null, stops the program with `MappingFileMalformed`. It never silently scans with a rule missing.

## Why each engine uses the key type it uses

| Signal | Key | Lookup | Why |
|---|---|---|---|
| MX, NS, CNAME, SPF include | clean hostname | **suffix**, label by label | A record is already a hostname, so after removing the priority and trailing dot it is a lookup key. The vendor owns a zone, not one name: `kate.ns.cloudflare.com` and `adi.ns.cloudflare.com` both end in `ns.cloudflare.com`. A tree of reversed labels finds the longest matching suffix in one step per label, and `evilcloudflare.com` never matches `cloudflare.com`. |
| Verification TXT | token name (`docusign=abc` → `docusign`) | **exact** | The token name is fixed by the vendor, so it is one dictionary lookup. |
| HTTP header name, header value, cookie | `cf-ray`, `server\|nginx/1.18`, `_shopify_y` | exact for names; **prefix** for values and cookies | Header values carry versions (`nginx/1.18.0`) and some cookies carry IDs (`intercom-session-<id>`). |
| Script / link / img / iframe URL | hostname, and hostname\|path | suffix, then prefix | Usually the hostname names the vendor. Sometimes only the path does: `www.facebook.com/tr` is the Meta Pixel, while `www.facebook.com/acme` is just a link. |
| Inline `<script>` text, whole document | none: the text itself | **substring** scan | An inline snippet like `fbq('init', …)` has no attribute to normalize, and the vendor's name can sit anywhere in free text. So these two are scanned: each pattern is searched in the text. That is a loop over the patterns, not a constant-time lookup. It is fine for a few dozen patterns; at thousands, an Aho-Corasick automaton would do it in one pass. |
| robots.txt path, security.txt contact, ads.txt seller | path, hostname, seller domain | prefix, suffix, exact | Platforms ship default robots.txt paths (`/checkouts/` is Shopify). Bug bounty platforms appear in security.txt. Ad networks appear in ads.txt. |

Confidence is set per file: **high** for anything the company had to configure itself (DNS records, generator tags, framework markers, first-party headers and cookies), **medium** for code loaded in the browser (it can be a leftover from a trial) and for `server` headers that a proxy can rewrite.

## What is deliberately not detected

A mapping entry whose value is `null` means "recognized, and on purpose not a detection". These entries keep the decision visible in the data, instead of leaving a gap nobody can explain. At `DEBUG` log level, every suppressed key is logged as such.

- **Public CDNs**: loading jQuery from `cdnjs.cloudflare.com` does not make a site a Cloudflare customer. The same goes for `cdn.jsdelivr.net`, `unpkg.com`, `ajax.googleapis.com` and Google Fonts. Treating these as customers is the kind of false positive that discredits a whole dataset.
- **Social links and embeds**: `www.youtube.com`, `www.linkedin.com`, `twitter.com`, `x.com`, `www.instagram.com` and `github.com` show a profile link, not a vendor relationship. Facebook is matched only on the pixel path `/tr`.
- **Generic infrastructure**: `JSESSIONID`, `PHPSESSID`, `x-request-id`, `server: nginx`, and robots paths like `/api/` and `/search`.
- **Noise TXT tokens**: `yandex-verification`, `globalsign-domain-verification` and others.

`tests/test_false_positives.py` checks these cases.

## Results on the 19 test domains

All 19 domains scan in about 15 seconds, with no engine error. To reproduce the full output with evidence: `python main.py --file domains.txt`.

| Domain | # | Technologies detected |
|---|---|---|
| alan.com | 14 | Android App, Apple Business, Cloudflare, Google Search Console, Google Workspace, HubSpot, iOS App, Mailchimp, Mandrill, Meta, Microsoft 365, SendGrid, Slack, Stripe |
| allbirds.com | 12 | Android App, Apple Business, Cloudflare, DocuSign, Google Search Console, Google Tag Manager, iOS App, Microsoft 365, Microsoft Clarity, Miro, OneTrust, Shopify |
| brooklinen.com | 17 | Android App, Apple Business, AWS CloudFront, Cloudflare, Dynamic Yield, GoDaddy, Google Analytics 4, Google Search Console, Heap, Heroku, iOS App, Meta, Microsoft 365, Mimecast, OneTrust, Sentry, Shopify |
| chorus.ai \* | 16 | Apple Business, AWS CloudFront, AWS Route 53, AWS S3, Google Search Console, Google Workspace, HubSpot, Mailchimp, Mandrill, Marketo, Microsoft 365, Postman, Proofpoint, SendGrid, Unbounce, Zendesk |
| contentsquare.com | 24 | Adobe, Amazon SES, Apple Business, Atlassian, AWS CloudFront, Cloudflare, Contentful, Contentsquare, Docker, DocuSign, Google Search Console, Google Tag Manager, Google Workspace, HubSpot, Jamf, Marketo, Microsoft 365, Mixpanel, Next.js, OneTrust, Salesforce, Stripe, Vercel, Zendesk |
| criteo.com \* | 19 | Adobe, Apple Business, Atlassian, Atlassian Statuspage, Docker, DocuSign, Fastly, Figma, Google Search Console, HackerOne, HubSpot, Microsoft 365, Miro, OpenAI, Qualtrics, Salesforce Pardot, Segment, Stripe, Varnish |
| decathlon.com | 21 | Adobe, Android App, Apple Business, Atlassian, AWS CloudFront, Canva, Cisco, Cloudflare, DocuSign, Google Search Console, Google Workspace, Gorgias, Heroku, iOS App, Klaviyo, Microsoft 365, Microsoft Clarity, Miro, MongoDB, Shopify, Zendesk |
| doctolib.fr \* | 11 | Android App, Atlassian, Brevo, Cloudflare, Cloudflare Bot Management, Google Search Console, Google Workspace, iOS App, Meta, Microsoft 365, Salesforce |
| drift.com | 18 | Amazon SES, Apple Business, Atlassian, Atlassian Statuspage, AWS CloudFront, AWS Elastic Load Balancing, AWS Route 53, Cloudflare, DocuSign, Fastly, Google Search Console, Google Tag Manager, Google Workspace, Miro, Next.js, SendGrid, Varnish, Zoom |
| figma.com | 28 | 1Password, Adobe, Android App, Apple Business, Atlassian, AWS CloudFront, AWS Route 53, DocuSign, Dropbox, Figma, Google Search Console, Google Workspace, HackerOne, iOS App, Jamf, Microsoft 365, MongoDB, Netlify, Next.js, Notion, OpenAI, Postman, Sanity, Segment, Shopify, Stripe, Vimeo, Zendesk |
| g2.com \* | 15 | Adobe, Apple Business, Atlassian, Cloudflare, Cloudflare Bot Management, DataDome, DocuSign, Google Search Console, Google Workspace, HackerOne, HubSpot, Meta, Microsoft 365, OpenAI, Segment |
| gymshark.com \* | 20 | Adobe, Adobe Sign, Android App, Apple Business, Atlassian, AWS Route 53, Cloudflare, Figma, Google Search Console, HackerOne, iOS App, Jamf, Meta, Microsoft 365, Mixpanel, OneTrust, OpenAI, Proofpoint, Shopify, Wrike |
| hotjar.com | 26 | 1Password, Adobe, Amazon SES, Apple Business, Atlassian, Atlassian Statuspage, AWS CloudFront, AWS Route 53, AWS S3, Contentful, Contentsquare, Docker, DocuSign, Google Search Console, Google Tag Manager, Google Workspace, HubSpot, Loom, Microsoft 365, Mixpanel, MongoDB, Next.js, OneTrust, Stripe, Vercel, Zendesk |
| payfit.com | 21 | Apple Business, Astro, Atlassian, AWS CloudFront, AWS Route 53, Axeptio, DatoCMS, Detectify, Docker, Figma, Google Search Console, Google Workspace, HubSpot, Jamf, Mailgun, Meta, Miro, MongoDB, OpenAI, Salesforce, Teamtailor |
| pennylane.com | 25 | 1Password, Apple Business, Atlassian, AWS CloudFront, AWS Route 53, AWS S3, Contentful, Didomi, DocuSign, Figma, Google Search Console, Google Workspace, Heroku, Jamf, Mailgun, Microsoft 365, Miro, Netlify, Notion, Nuxt, OpenAI, Salesforce, SendGrid, Slack, Stripe |
| qonto.com | 24 | Amazon SES, Apple Business, Atlassian, AWS CloudFront, AWS Elastic Load Balancing, AWS Route 53, Cisco, Cloudflare, Didomi, Google Search Console, Google Workspace, Jamf, Meta, Microsoft 365, MongoDB, Notion, OpenAI, Salesforce, Segment, SendGrid, Sentry, Stripe, Vercel, Zendesk |
| sentry.io | 23 | Apple Business, Astro, Atlassian, Cisco, Docker, DocuSign, Dropbox, Google Cloud DNS, Google Cloud Load Balancing, Google Search Console, Google Workspace, HackerOne, Marketo, Microsoft 365, Miro, Notion, OpenAI, Plausible, SendGrid, Sentry, Stripe, Vercel, Zendesk |
| swile.co | 22 | 1Password, Apple Business, Atlassian, AWS Route 53, DocuSign, Figma, Google Search Console, Google Workspace, Jamf, Mailchimp, Meta, Microsoft 365, Next.js, Notion, OneTrust, Postman, Salesforce Pardot, SendGrid, Slack, Vercel, Vimeo, Zendesk |
| zapier.com | 27 | Airtable, Apple Business, Atlassian, AWS CloudFront, AWS Elastic Load Balancing, AWS Route 53, Canva, Contentful, Docker, DocuSign, Google Search Console, Google Tag Manager, Google Workspace, HackerOne, HubSpot, Jamf, Mailgun, Meta, Microsoft 365, Next.js, OneTrust, OpenAI, Optimizely, Qualtrics, Stripe, Vercel, Zendesk |

\* Homepage flagged as client-side rendered, so its HTML analysis is limited (see below).

DNS carries most of the signal. Verification TXT records reveal internal SaaS tools (Jamf, 1Password, Miro, Notion, DocuSign, Figma) that no web page shows. MX and SPF records reveal the email stack.

## Known limitations

- **Client-side rendered pages are under-analyzed.** The HTML is fetched with a plain GET, so tools injected by JavaScript are not seen. That covers anything Google Tag Manager loads, which is most marketing pixels. gymshark.com, g2.com, criteo.com, chorus.ai and doctolib.fr are flagged in the output for this reason.
- **Bot protection.** Sites behind DataDome or Cloudflare bot management (g2.com, doctolib.fr) may answer with a challenge page instead of the real homepage. Their DNS results are unaffected.
- **Verification records with random data in the name.** Some vendors embed a random ID in the token name instead of the value: `ZOOM_verify_<id>`, `anthropic-domain-verification-<id>=…`. These need a second, prefix-matched token map. I left them out to keep the TXT lookup a single exact lookup.
- **robots.txt is low yield.** It mostly confirms what other engines find (Shopify, Cloudflare). It costs almost nothing and occasionally reveals a platform the homepage hides.
- **Only the homepage is read.** Careers, help and pricing pages often load different tools (ATS widgets, support chat, payment).
- **DNS for subdomains is limited to CNAME on a fixed list** of 24 common subdomains in `subdomains.json`.

## Taking it to production

- **Fetch once, match many times.** The HTTP and HTML engines both GET the homepage today. A shared fetch cache per domain would retrieve each URL once. Persisting raw artifacts (already possible with `--save-artifacts`) lets a new or fixed rule be replayed over every past scan without refetching. The domain-first folder layout exists for exactly that access pattern.
- **Rule versioning.** Store the version (git hash) of the mapping files with each result, so "why did this detection appear/disappear" has an answer, and old results can be recomputed.
- **Orchestration.** A durable workflow engine such as Temporal, with one workflow per domain and one activity per engine. Activity-level retry policies would replace the ad-hoc retry in the HTTP client, and a crashed worker would resume instead of restarting the batch.
- **Politeness and scale.** Per-host and per-resolver rate limiting, a pool of resolvers, a headless browser only for pages flagged as client-side rendered, and rotating egress for bot-protected sites.
- **Better evidence scoring.** Combine detections of the same technology from independent sources into one confidence score. A Shopify verdict backed by DNS, headers, HTML and robots.txt is near-certain, while one inline match is a hint.
- **More signals.** DKIM selectors (`google._domainkey`, `selector1._domainkey` for Microsoft 365, `k1._domainkey` for Mailchimp), `_dmarc` reporting addresses (which reveal DMARC vendors), certificate transparency logs to discover subdomains, the IP/ASN of A records to identify hosting, and the JavaScript bundles themselves.
