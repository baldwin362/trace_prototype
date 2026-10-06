# Trace prototype

## Introduction

**What we are building.** Trace finds out which third-party technologies a company uses, only from what is publicly visible about its domain. You give it `gymshark.com`, and it answers: Shopify, Cloudflare, Microsoft 365, Proofpoint, and so on.

**Our approach.** A company cannot use a vendor's product without leaving a trace somewhere public:

- it had to **change its DNS** to point at the vendor, or to prove to the vendor that it owns the domain;
- the vendor's servers **answer the HTTP request** and leave their mark in the headers and cookies;
- the vendor's code is **loaded by the homepage HTML**;
- the platform leaves its mark in **well-known files** like `robots.txt`.

Trace looks in these four places at the same time, and compares what it finds with a list of detection rules stored in JSON files.
Every detection comes with **the exact text that proves it**, so anyone can check why we think a company uses a technology:

```
gymshark.com
  Microsoft 365                dns:TXT                  MS=ms54108504
  Proofpoint                   dns:MX                   10 mx07-005a6901.pphosted.com.
  Shopify                      http:header_value        powered-by: Shopify
  Shopify                      robots:disallow          Disallow: /checkouts/
  ...
```

## Installation

### Recommended: the official Docker image

The image is published on Docker Hub, so there is nothing to install except Docker.

**1. Get the image.** Download it from Docker Hub:

```
docker pull edward2968/trace_prototype:latest
```

Or, if you cloned the repository, build it yourself from the project folder:

```
docker build -t edward2968/trace_prototype .
```

**2. Run it.**

```
docker run -it --rm --name trace_prototype_container edward2968/trace_prototype:latest
```

This opens a prompt. Type one or more domains, then `exit` when you are done:

```
Type one or more domains separated by spaces, or exit to quit.
trace> gymshark.com
...
trace> qonto.com figma.com
...
trace> exit
```

To scan once without the prompt, put the domain at the end:

```
docker run --rm edward2968/trace_prototype:latest gymshark.com
```

Tip: add `--log-level WARNING` at the end of either command to hide the live logs and only see the results.

### Alternative: run it with Python

**1. Clone the repository.**

```
git clone git@github.com:baldwin362/trace_prototype.git
cd trace_prototype
```

If you have no SSH key set up on GitHub, use `git clone https://github.com/baldwin362/trace_prototype.git` instead.

**2. Check your Python version.** The Docker image uses Python 3.11, so you need Python 3.11 or newer:

```
python --version
```

**3. Create a virtual environment and install the dependencies.**

```
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

On macOS or Linux, activate it with `source .venv/bin/activate` instead.

**4. Run it from the project root**, with the domain at the end:

```
python main.py gymshark.com
```

Other ways to run it:

| Command | What it does |
|---|---|
| `python main.py` | opens the same prompt as the Docker image |
| `python main.py gymshark.com qonto.com` | scans several domains at once |
| `python main.py --file domains.txt` | scans the 19 test domains, one per line in the file |
| `python main.py gymshark.com --json` | prints the result as JSON instead of a table |
| `python main.py gymshark.com --log-level DEBUG` | also shows every network call and every value that matched no rule |
| `python -m pytest backend/tests` | runs the tests (no network needed) |

## Architecture

### The big picture

```
                                  python main.py gymshark.com
                                              │
                                              ▼
                                         scanner.py
                       runs the 4 engines at the same time on the domain
                                              │
             ┌───────────────────┬────────────┴──────┬───────────────────┐
             ▼                   ▼                   ▼                   ▼
         dns engine          http engine         html engine        robots engine
       DNS records        homepage headers,     homepage HTML       robots.txt, ads.txt,
                          cookies, redirects                         security.txt...
             │                   │                   │                   │
             └───────────────────┴─────────┬─────────┴───────────────────┘
                                           ▼
                        one result: every detection, with its evidence
```

**Why it is split this way.** There is **one engine per place where information is found**: DNS, HTTP, HTML and robots. Each engine fetches its own data and reads it on its own, and no engine knows the others exist. This gives us:

- **speed**: the four engines run at the same time;
- **robustness**: if one fails (for example a site blocks bots), the other three still report, and the failure is written in the result;
- **simplicity**: to understand or change how DNS is read, you only open the `dns/` folder.

### Inside an engine

Every engine is built the same way, so once you have read one, you know all four:

```
   client  ──────────►  extractors  ──────────►  detector  ──────────►  detections
 fetches data         clean each value        checks each value       "Shopify, proved by
 from the internet    so it looks like        against the JSON        powered-by: Shopify"
                      the rules               rule files
```

For example, in the DNS engine:

```
 "10 aspmx.l.google.com."  ───►  "aspmx.l.google.com"  ───►  mx.json says  ───►  Google Workspace,
   (the raw MX record)            (cleaned value)            "Google Workspace"     proved by "10 aspmx.l.google.com."
```

Only the client touches the network. Everything after it works on data already downloaded, which is why all the tests run without internet.

### What each folder contains

```
main.py                    the command line: reads the domains, prints the results
backend/
  domain/
    scanner.py             runs the 4 engines at the same time and puts their results together
    dns/                   the DNS engine
    http/                  the HTTP engine
    html/                  the HTML engine
    robots/                the robots engine
    rules/                 the shared matching code used by every engine
    models/                the data passed between the layers
    errors/                the errors each engine can report
    persistence/           saves raw data and results to disk (with --save-artifacts)
  tests/                   the tests, with real saved responses in tests/fixtures/
```

**`dns/`** asks a public DNS server for the domain's records:
- **MX** records show the email provider (Google Workspace, Microsoft 365, Proofpoint...);
- **NS** records show who hosts the DNS (Cloudflare, AWS Route 53...);
- **TXT** records hold the proofs of ownership companies give their vendors (`docusign=...`, `atlassian-domain-verification=...`) and the list of services allowed to send their emails (SPF);
- **CNAME** records of common subdomains show which vendor serves them (`shop.` pointing to Shopify, `help.` pointing to Zendesk...).

**`http/`** requests the homepage and reads everything except the page itself:
- the **headers** (`server: cloudflare`, `powered-by: Shopify`);
- the **cookies** the site sets (`_shopify_y`, `__hstc` for HubSpot);
- the **redirects** it went through (a redirect to `*.myshopify.com` means Shopify).

**`html/`** downloads the homepage and reads its HTML:
- the **URLs of the scripts, images and frames** it loads (`static.hotjar.com` means Hotjar);
- the **generator tag**, where site builders write their own name (`WordPress`, `Webflow`);
- the **code written inside the page**, where tracking snippets live (`fbq('init'` means Meta Pixel);
- **framework markers** (`/_next/static/` means Next.js).

It also flags pages built by JavaScript, because a plain download sees less of them.

**`robots/`** downloads a few standard files every site may have:
- **robots.txt**: platforms ship their own default paths (`/checkouts/` means Shopify);
- **security.txt**: shows the bug bounty platform (HackerOne, Bugcrowd...);
- **ads.txt**: lists the ad networks selling the site's ad space;
- the presence of **app files** (`apple-app-site-association`) shows the company has an iOS or Android app.

**`rules/`** holds the matching code that all four engines share, so no engine reimplements it:
- `mapping_loader.py` reads the JSON rule files and stops the program if one is broken;
- four ways of comparing a value with the rules, each JSON file says which one it uses:

| Lookup | It matches when... | Example |
|---|---|---|
| exact | the value is equal to the rule | `docusign` matches `docusign` |
| prefix | the value starts with the rule | `intercom-session-abc123` matches `intercom-session` |
| suffix | the hostname ends with the rule | `kate.ns.cloudflare.com` matches `ns.cloudflare.com` |
| substring | the rule appears anywhere in the text | a script containing `fbq('init'` matches `fbq('init'` |

- `mapping_matcher.py` runs the right lookup for a file and turns every match into a detection.

**The rules themselves** are JSON files in each engine's `mappings/` folder. Adding a technology means adding one line to one of them, with no Python change:

```json
"pipedrive-verification": "Pipedrive"
```

A rule set to `null` means "we recognize this, and on purpose we do not report it". For example, loading a library from `cdnjs.cloudflare.com` does not make a site a Cloudflare customer.
