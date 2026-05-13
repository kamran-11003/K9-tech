# Selected Work — K9 Technologies

> Production systems, SaaS platforms, and growth engines built end-to-end. Every product below solves a real business problem and generates measurable output. No demos, no college work.

---

## 01 · AI Agents & Conversational Products

---

### Aria — Inbound & Outbound AI Sales Agent
**Your best sales rep. Never sleeps, never misses a follow-up.**

A business embeds Aria on their website. Visitors can type or speak directly to her. She understands the business, qualifies the lead through a natural conversation, handles objections using a live knowledge base, and books a discovery call — all without a human touching it. When a lead comes in via form, Aria triggers an outbound call back within 5 minutes, personalised with whatever the lead already told you.

**What it does:**
- Real-time voice call in the browser (VAD → Whisper STT → Gemini → TTS, sub-2 s round-trip)
- Text chat with full session memory, topic-restricted, prompt-injection resistant
- RAG grounded on the client's own documents — never hallucinates pricing or features
- Books, cancels, reschedules discovery calls conversationally via live calendar tools
- Captures structured lead data (name, company, budget, timeline, service interest) → MongoDB
- Outbound call pipeline: inbound lead → scored → Aria calls back → transcript summarised → CRM

**Built with:** FastAPI · MongoDB · Gemini 2.5 Flash (RAG + TTS) · Whisper · n8n · GSAP frontend

**Why it matters for a client:** Replaces the cost of a full-time SDR for first-touch qualification. Every lead gets a response in minutes, 24 hours a day.

---

### WhatsApp AI Business Bot *(white-label SaaS)*
**The number your customers already have. Now it answers instantly.**

Multi-tenant platform where each business signs up, uploads their knowledge base, sets their persona and opening hours, and gets a live WhatsApp number within the hour. The bot handles product questions, order status, appointment booking, and payment links. When it can't help, it routes to a human agent via a shared inbox with full context.

**What it does:**
- Multi-tenant: isolated knowledge base, persona, rules and escalation per client
- Appointment booking with slot availability check, reminders, and reschedule
- Payment link generation and order-status lookup via webhooks
- Human handover with context pass-through (no repeat explanations)
- Analytics per business: conversation volume, handled vs escalated, booking conversion
- Stripe-billed subscriptions; clients self-serve from onboarding to live in under 1 hour

**Built with:** Python · WhatsApp Cloud API · Gemini · Postgres · Next.js admin panel · Stripe

---

### DocuChat — RAG Chatbot Builder *(SaaS)*
**Any company, any docs, live chatbot in 3 minutes.**

Self-serve platform: upload PDFs, paste URLs, connect Notion — DocuChat chunks, indexes, and wraps it in a chatbot with citation footnotes. Clients embed the widget on their site or use the REST API. Usage is metered; billing is automatic.

**What it does:**
- Drag-and-drop ingestion: PDF, DOCX, TXT, URLs, Notion, Google Drive
- Hybrid retrieval (TF-IDF + semantic re-rank) with chunk-level citations shown to the user
- Embeddable JS widget (2-line script) + REST API for headless integrations
- Per-workspace API keys, usage metering, soft/hard request quotas
- Self-serve signup, workspace creation, chatbot deploy — no code, no support ticket needed
- White-label option: custom domain, colours, remove branding

**Built with:** FastAPI · Qdrant · OpenAI embeddings · Next.js · Clerk · Stripe metered billing

---

## 02 · Web Products & SaaS Platforms

---

### K9 Technologies — Agency Website
**A marketing site that is itself the product demo.**

Not a template. A hand-built conversion machine that shows off every skill while actively selling services. The AI agent on the site is live — clients can talk to it right now, and it books real calls.

**What it does:**
- Animated hero (particle canvas, Pexels video background, GSAP ScrollTrigger sequences)
- Services, case-study projects, metrics, testimonials, tech-stack carousel — all scroll-animated
- Live booking calendar: slots from MongoDB, book / cancel / reschedule without logging in
- Bottom-right chat dock: text chat, push-to-talk, and full real-time voice call mode
- Dark / light themes persisted to localStorage; fully responsive to 320 px
- Contact form → instant lead capture → MongoDB

**Built with:** FastAPI · vanilla JS · GSAP 3 · MongoDB · Uvicorn static files

---

### BookFlow — Multi-Tenant Scheduling SaaS
**Calendly for service businesses that need more control.**

Agencies, coaches, salons, and consultancies each get a branded booking micro-site. They configure their own slot rules, pricing, buffer times, and reminders. Clients book and pay in one flow. Operators manage everything from a clean dashboard.

**What it does:**
- Per-business configuration: slot duration, buffers, max advance booking, blackout dates
- Stripe deposit or full payment at booking; Stripe Connect for marketplace payouts
- Two-way Google Calendar sync; iCal feed for other tools
- Email + WhatsApp + SMS reminders (24 h before, 1 h before, follow-up after)
- Branded public booking page + embeddable iframe widget
- Operator dashboard: calendar view, upcoming bookings, revenue, no-show rate

**Built with:** Next.js · Postgres · Prisma · Stripe Connect · Google Calendar API · Twilio

---

### PropDesk — Real-Estate Lead & CRM Platform
**Listings site + agent pipeline. One product.**

Agencies waste money on separate listing software, CRM, and marketing tools. PropDesk is all three. Public visitors search, save, and enquire. Agents manage every lead from first touch to signed contract inside the same platform.

**What it does:**
- Public listings: map search (Mapbox), filters, saved-search email alerts, mortgage calculator
- AI listing copy: agent uploads photos + bullet points → full listing description generated
- Agent CRM: leads auto-created from enquiry forms, pipeline stages, activity timeline
- Automated WhatsApp drip sequences per lead stage (viewings booked, offers submitted)
- Document vault per deal: offers, contracts, ID docs; e-sign via DocuSign integration
- Role-based access: admin / senior agent / junior agent

**Built with:** Next.js · Postgres · Mapbox · Gemini Vision · DocuSign API · WhatsApp Cloud API

---

### StoreFront — Headless E-Commerce Platform
**Own your store. No Shopify tax.**

A fully custom alternative to Shopify for brands that have outgrown template stores or want to own their tech. Built headless — the storefront is a fast Next.js site, the backend is a clean API, and everything integrates directly.

**What it does:**
- Catalog: unlimited products, variants, options, digital + physical, bundles
- One-page checkout: Stripe, Apple Pay, Google Pay, cash-on-delivery
- Admin: order management, fulfilment workflow, refunds, discount codes, gift cards
- Abandoned-cart recovery (email + WhatsApp sequence)
- Blog/CMS, SEO meta engine, auto-sitemap, schema.org Product/BreadcrumbList markup
- Inventory management: stock alerts, multi-warehouse support, supplier POs

**Built with:** Next.js · Medusa.js · Postgres · Stripe · Algolia · Resend email

---

## 03 · Automation & Workflow Systems

---

### LeadFlow — Full-Funnel Sales Automation
**Form submit to booked call with no human involvement.**

When a lead hits a website form, LeadFlow scores it, enriches it, routes it, triggers the right outreach sequence, and reports on pipeline health — all automatically. Built on n8n with custom nodes for the pieces n8n can't do natively.

**What it does:**
- Webhook intake from any form tool → instant BANT-style scoring via AI
- Hot leads → outbound AI call within 5 minutes; warm leads → 3-step email sequence
- Cold leads → nurture drip with Slack notification to sales if they re-engage
- CRM sync (HubSpot / Pipedrive): contact created, deal opened, activities logged automatically
- Daily pipeline digest email: new leads, conversion rates, sequence performance
- Failure alerts with replay: if a step fails, ops gets a Slack message with a one-click retry link

**Built with:** n8n self-hosted · Postgres · Gemini enrichment · HubSpot API · Twilio · SMTP

---

### ContentOS — AI Content Production Pipeline
**One brief in. Blog, LinkedIn, Twitter, newsletter, YouTube script — all out.**

A full content operation run by one person (or zero). A brief goes into Notion, a workflow picks it up, AI produces a full draft with brand voice, a human optionally edits, and the system publishes to every channel on schedule.

**What it does:**
- Brief submitted to Notion → n8n workflow triggered automatically
- AI generates: SEO blog post, LinkedIn carousel copy, Twitter/X thread, YouTube short script, newsletter section, Instagram caption — each formatted per platform
- Human-in-the-loop: Notion page updated with all drafts; editor approves or edits before publish
- Scheduled publishing to Buffer / Ayrshare for social; CMS API for blog
- Performance loop: engagement data pulled weekly → top topics fed back into brief template

**Built with:** n8n · Gemini · ElevenLabs · Notion API · Cloudinary · Buffer / Ayrshare APIs

---

### InvoiceBot — OCR to Accounting in 8 Seconds
**Email a receipt. It posts itself to your books.**

Suppliers email invoices to a dedicated inbox. InvoiceBot reads every line item, validates against open purchase orders, routes for approval if there's a mismatch, and posts the journal entry to QuickBooks or Xero — without anyone touching a keyboard.

**What it does:**
- Email intake (IMAP watch) or manual PDF/image upload via web interface
- Gemini Vision extracts: vendor, invoice number, line items, tax, totals, due date
- PO matching: auto-approve if within tolerance; flag + Slack alert if discrepancy
- Approval workflow: one-click approve/reject from Slack or email
- Posts to QuickBooks / Xero with vendor matching (creates vendor if new)
- Audit trail: every document stored with extracted data, match result, approver, post timestamp

**Built with:** n8n · Gemini Vision · Postgres · QuickBooks API · Xero API · Slack

---

### OutreachEngine — AI Cold Email at Scale
**Hyper-personalised outbound. Deliverability-safe. Runs itself.**

Scrapes a target list, enriches each contact from their website and LinkedIn, writes a genuinely personalised first line per recipient, and sends through a warmed multi-inbox rotation. Replies are detected and handed to the sales team as live opportunities.

**What it does:**
- List building: Apollo export or Apify scraper → auto-dedup and clean
- Enrichment: website scrape + LinkedIn headline → AI-written personalised opening line
- Sending: Smartlead multi-inbox rotation, throttled per inbox, warm-up maintained
- Reply handling: positive replies → CRM deal opened + Slack alert; auto-unsubscribe on opt-outs
- Reporting: sent, open rate, reply rate, positive reply rate per campaign per day

**Built with:** Python · Apify · Smartlead API · Gemini · Postgres · n8n orchestration

---

## 04 · SEO Products

---

### PageFactory — Programmatic SEO Engine
**Turn a spreadsheet into 10,000 indexed, ranking pages.**

Niche directories, job boards, location-based service pages, comparison tools — any site that needs mass pages at a quality level Google won't penalise. PageFactory takes a structured data source and generates unique, contextually relevant copy for every page, with technical SEO baked in from the start.

**What it does:**
- Data source: CSV, Airtable, Google Sheets, or API → Next.js ISR page per row
- AI copy generation per page: unique intro, body, FAQs — not just token substitution
- Technical SEO: auto-canonical, hreflang, breadcrumb schema, FAQ schema, sitemap generation
- Internal linking graph: auto cross-links related pages by topic cluster
- Google + Bing Indexing API push on deploy; re-push on update
- Monitoring: rank tracking per page group, coverage report weekly

**Built with:** Next.js (ISR) · Airtable CMS · Gemini · Google Indexing API · DataForSEO rank tracker

**Real result:** Niche directory went from 0 to 5,400+ indexed pages in 3 weeks, ranking for long-tail terms with zero link building.

---

### AuditDesk — SEO Audit & Reporting SaaS
**Sell audits at scale. White-label, automated, recurring.**

Designed for SEO agencies that want to deliver client reports without doing them manually. AuditDesk crawls a site, checks everything that matters, and produces a branded PDF report — weekly, monthly, or on demand.

**What it does:**
- Full site crawl: broken links, redirect chains, orphan pages, page depth, crawl budget issues
- On-page: missing/duplicate meta, thin content detection, heading structure, image alt
- Performance: Core Web Vitals (CrUX API), TTFB, render-blocking resources
- Keyword rank tracker: SERP positions over time, SERP feature presence (featured snippet, PAA)
- Backlink health: lost/new links, toxic anchor ratio (DataForSEO)
- White-label PDF export: agency logo, colours, client name — ready to email to client
- Stripe-billed: agencies pay per domain monitored; resell at any margin

**Built with:** Python · Scrapy · Puppeteer · Next.js · Postgres · DataForSEO API · Stripe

---

### LocalRank — Google Business Profile Automation
**Rank in the local pack. Automatically.**

Multi-location businesses (franchises, chains, service businesses) lose local rankings because their GBP profiles go stale. LocalRank keeps every profile fresh, responds to reviews, fixes citation inconsistencies, and reports ranking positions — without anyone logging into Google.

**What it does:**
- GBP post scheduler: weekly offers, updates, events per location — written by AI, posted automatically
- Review monitoring: new reviews alerted in Slack; AI drafts a personalised reply for human approval (or full-auto)
- Citation audit: checks NAP consistency across 50+ directories; flags mismatches; submits corrections
- Local rank heatmap: tracks visibility per postcode / zip across the service area grid
- Competitor intel: tracks rival GBP activity, review velocity, new posts

**Built with:** n8n · Google Business Profile API · Gemini · BrightLocal API · Postgres

---

## 05 · Data & Analytics Products

---

### ChannelIQ — Marketing Attribution Dashboard
**Stop guessing which ads work. See the actual truth.**

Pulls spend from every ad platform and revenue from your payment processor into a single warehouse. Shows real ROAS, CAC, and LTV — not the platform-reported numbers that double-count everything.

**What it does:**
- Connectors: Google Ads, Meta, TikTok, LinkedIn, Snapchat, GA4, Stripe, Shopify
- De-duplicated multi-touch attribution models: first click, last click, linear, time-decay, data-driven
- ROAS breakdown by campaign → ad set → creative → audience
- Cohort LTV and CAC payback period charts
- Anomaly detection: sudden ROAS drop, budget pacing overspend → Slack alert same day
- Executive weekly email: auto-generated narrative with top insights, not just numbers

**Built with:** Airbyte · BigQuery · dbt · Metabase · Looker Studio · Python anomaly detection

---

### StoreOps — E-Commerce Operations Dashboard
**One screen. Every number your store needs.**

D2C founders spend hours stitching together Shopify reports, Google Analytics, and spreadsheets. StoreOps does it for them — live, in one place, with alerts before problems become crises.

**What it does:**
- Live orders: fulfilment SLA tracking, late shipment alerts, carrier performance
- Revenue: daily/weekly/monthly vs target, by channel, by product, by geography
- Customer metrics: cohort retention, repeat purchase rate, AOV trends, refund rate
- Inventory: stock level per SKU, days of cover, reorder alerts
- Anomalies pushed to Slack: conversion rate drop, sudden cart abandonment spike, payment failure surge

**Built with:** Python ETL · Postgres · Next.js · Recharts · Shopify API · Slack webhooks

---

### ConversationIQ — Support Analytics Platform
**Your customers are telling you exactly what's broken. Are you listening?**

Ingests thousands of support tickets, chat logs, and call transcripts. Clusters them by topic automatically. Tracks which issues are growing, which products generate the most complaints, and which conversations signal churn — before the customer leaves.

**What it does:**
- Ingestion: Intercom, Zendesk, Freshdesk, CSV export, call transcript upload
- Topic clustering: embeddings + HDBSCAN — discovers themes without predefined labels
- Sentiment trend per topic over time: catch growing issues early
- Churn-risk tagging: conversations matching frustration + value-question patterns flagged for CS team
- Auto-generated weekly insight report: top 5 issues, trend direction, example verbatims
- Product-team dashboard: filter by product area, feature, severity, date range

**Built with:** Python · OpenAI embeddings · UMAP · HDBSCAN · Streamlit · Postgres

---

### PulseBoard — Real-Time KPI War-Room
**The big screen your sales floor deserves.**

WebSocket-powered live dashboard designed to run on a 4K TV. Revenue ticks up in real time. The leaderboard refreshes on every closed deal. Milestones trigger confetti. Teams know exactly where they stand at every moment of the day.

**What it does:**
- Live metrics: revenue today, deals closed, calls made, pipeline value — all WebSocket-pushed
- Sales leaderboard: ranked by revenue, by calls, configurable per day/week/month
- Milestone celebrations: threshold hit → confetti animation + sound + Slack message
- Multi-team support: each team sees their own board; exec sees consolidated
- Historical view: how today compares to same day last week/month/year

**Built with:** Node.js · Socket.IO · Postgres · React · designed for 4K displays

---

## 06 · Platform Infrastructure & Integrations

---

### SaaS Chassis — Multi-Tenant Auth, Billing & Admin
**The foundation every SaaS needs. Already built.**

Every SaaS product I ship starts from this. It handles all the plumbing — auth, teams, billing, usage metering, admin tools — so product work starts on day one, not week six.

**What it includes:**
- Auth: email/password, Google OAuth, magic links, MFA via TOTP
- Multi-tenancy: workspace → teams → members → roles (owner / admin / member / read-only)
- Billing: Stripe subscriptions (monthly/annual), metered usage, upgrade/downgrade, customer portal
- Admin panel: user search, plan override, impersonation, audit log, feature flags
- Developer: webhook receiver, API key management, rate-limit middleware, structured logging

**Built with:** Next.js · NextAuth · Prisma · Postgres · Stripe · Resend

---

### DataBridge — Custom CRM & Marketing Stack Connectors
**When Zapier templates don't cut it.**

Enterprises run custom CRMs, legacy ERPs, and bespoke databases that no off-the-shelf connector covers. DataBridge handles bidirectional sync between any combination, with schema mapping, conflict resolution, and a full event replay log.

**What it does:**
- Visual schema mapper: drag source field → target field; transformation rules per field
- Bidirectional sync with last-write-wins or custom conflict resolution rules
- Event replay: every sync event logged; ops can rewind and re-process any window
- Live monitoring dashboard: sync lag, error rate, record volume per connector
- Built-in connectors: HubSpot, Pipedrive, Salesforce, MongoDB, Postgres, Google Sheets, WhatsApp

**Built with:** Python · n8n · Redis Streams · Postgres · Next.js operations dashboard

---

## Let's Build Something

If a problem on this page looks like your problem, let's talk.

- **Website:** k9technologies.com
- **Email:** hello@k9technologies.com
- **Book a call:** Chat with Aria on the site — she'll find a time that works.

---

*Every product above was designed, architected, built, and deployed end-to-end. Stack choices are deliberate, not default — the right tool for each job.*
