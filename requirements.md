# De Kievit Harmelen — Website Requirements

## 1. Background

**Stichting de Kievit** manages a unique nature area west of Harmelen (Utrecht, Netherlands). The site is used for nature and environmental education (NME) for primary schools, and is also rented out for trainings, meetings, and children's parties.

### Current Online Presence

| Channel | Pros | Cons |
|---------|------|------|
| **Website** (dekievitharmelen.nl) | Publicly accessible; SEO-indexed; has calendar, contact form, 360° tour | Static photo collection; dated WordPress theme (2016); limited interactivity; hard to update for non-technical volunteers |
| **Facebook page** | Dynamic feed; community engagement (posts, likes, comments, sharing); easy photo/video uploads | Walled garden (requires Facebook account to interact); content not indexable by search engines; no control over layout/design; algorithm controls visibility |

### Current Website Structure (for reference)

The existing WordPress site contains these sections:
- **Home** — slider with nature photos, intro text, quick links
- **Nieuws** — blog-style news posts (37+ pages)
- **Foto's** — photo gallery page
- **Kalender** — events calendar (The Events Calendar plugin)
- **Wie zijn wij?** — about pages (location, 25th anniversary)
- **Dit doen wij** — NME, beekeepers, site maintenance
- **Activiteiten** — children's parties, venue rental, Kievit wines
- **Help mee!** — become a donor, become a volunteer
- **Contact** — contact details, links

---

## 2. Vision & Goals

Build a custom website that combines the **public accessibility and informational depth** of the current website with the **dynamic, community-driven engagement** of the Facebook page.

### Primary Goals

1. **Public & discoverable** — fully accessible without login, SEO-friendly
2. **Easy content updates** — volunteers (non-technical) can post news, photos, and events without developer involvement
3. **Dynamic photo/media sharing** — move beyond a static gallery; support frequent photo uploads, albums per activity/event, and possibly short videos
4. **Community engagement** — visitors can interact with content (reactions, comments, sharing) without needing a Facebook account
5. **Modern & mobile-friendly** — responsive design that works well on phones (parents, teachers browsing on the go)
6. **Low maintenance** — minimal hosting/ops burden; the foundation should run with volunteer effort

### Secondary Goals

- Preserve existing content/SEO value during migration
- Fediverse-first: publish to Mastodon/Pixelfed as the primary social channel alongside the website
- No Meta platform integration without explicit project owner approval
- **Dutch (nl-NL) as default language** — all UI, content, and navigation in Dutch
- **NL/EN language switch** — simple toggle allowing visitors to switch to English for international audiences (e.g., visiting researchers, international school parents)
- Dutch-language URLs as default; English routes as secondary (e.g., `/fotos` primary, `/photos` as alias or translated path)

---

## 3. Functional Requirements

### 3.1 Content Management

- [ ] **Simple admin interface** for authorized volunteers to create/edit posts, upload photos, and manage events
- [ ] **Rich text editor** for news posts with embedded images
- [ ] **Draft/publish workflow** — posts can be saved as drafts before publishing
- [ ] **Multiple author support** — different volunteers can post under their own name

### 3.2 News / Blog

- [ ] Chronological news feed on the homepage or dedicated news page
- [ ] Individual news post pages with full content
- [ ] Categories or tags for organizing posts (e.g., NME, events, maintenance, general)
- [ ] Pagination or infinite scroll for older posts

### 3.3 Photo Gallery — ⭐ PoC Focus Area

> The photo section is the primary focus of the proof of concept, covering both **gathering** (submission) and **sharing** (distribution) of community photos.

#### 3.3.1 Gallery Display

- [ ] **Album-based gallery** — organize photos by event, date, or theme
- [ ] **Lightbox viewing** — click to enlarge with navigation between photos
- [ ] **Recent photos** section on the homepage showing latest uploads
- [ ] Optional captions and descriptions per photo
- [ ] **Multi-image posts** — when a Fediverse post or upload contains multiple photos, each image is displayed as its own gallery card (data model preserves the submission grouping for potential future carousel view)

#### 3.3.2 Photo Submission (Gathering)

- [ ] **Community upload form** ("Deel je foto's") — simple form accessible from gallery pages and event/album pages:
  - Multi-select file picker (max ~10 photos per submission)
  - Submitter name and email (required, no account/verification needed)
  - Short description (optional)
  - Link to event/album (pre-filled when submitted from an event page)
  - GDPR consent checkbox: *"Ik bevestig dat de gefotografeerde personen toestemming hebben gegeven"*
  - Friendly confirmation: *"Bedankt! Je foto's verschijnen na goedkeuring."*
- [ ] **Bulk upload** for admin/volunteers — upload multiple photos at once (bypasses moderation)
- [ ] **Auto-resize/compress** on upload — serve optimized versions, store originals
- [ ] **Spam prevention** — honeypot field, rate limiting (max N submissions per IP/hour), file type validation (jpg/png/webp only), max file size (~15MB per photo)
- [ ] **Fediverse hashtag ingestion** ⭐ PoC — poll `#DeKievitHarmelen` on Mastodon/Pixelfed via public API (`GET /api/v1/timelines/tag/...`), feed matching posts into the moderation queue automatically
  - ⚠️ **Pixelfed limitation**: Pixelfed's hashtag timeline API requires authentication (302 → /login); removed from default poll list. Pixelfed posts *may* appear via federation to Mastodon instances, but this is unreliable.
  - ⚠️ **Cross-instance deduplication**: the same federated post appears on multiple Mastodon instances; dedup uses canonical `source_url` to prevent duplicates.
- [ ] **Future channel: email** — submit photos by emailing a dedicated address *(deferred to WordPress phase — WordPress handles inbound email natively via plugins like Postie)*
- [ ] **Future channel: Signal** — explore Signal integration for photo submission when APIs allow. Not in PoC scope.

#### 3.3.3 Moderation Queue

- [ ] **Unified moderation queue** — all submitted photos (from any channel) land here
- [ ] **Email notification** to moderators when new submissions arrive *(deferred to WordPress phase)*
- [ ] **Approve / reject** per photo or batch-approve all in a submission
- [ ] Approved photos appear in the linked album immediately
- [ ] **Photo removal process** — clear way for anyone to request removal of a photo (GDPR compliance)

#### 3.3.4 Photo Distribution (Sharing)

- [ ] **Website gallery** — primary channel, publicly accessible, SEO-indexed
- [ ] **RSS/Atom feed** — photo/album feed that anyone can subscribe to in a feed reader
- [ ] **Fediverse auto-post** — approved photos automatically posted to De Kievit's own Mastodon/Pixelfed account
- [ ] **Share buttons** on photos and albums: Signal, email, copy link
- [ ] ⚠️ **No WhatsApp/Meta integration** without explicit approval from the project owner

#### 3.3.5 Privacy & GDPR

- [ ] Consent checkbox on submission form
- [ ] Photo policy page explaining how photos are used and how to request removal
- [ ] Easy removal request process (contact form or dedicated button)

### 3.4 Events / Calendar

- [ ] Event listing with date, time, location, and description
- [ ] Calendar view and/or list view
- [ ] Upcoming events highlighted on the homepage
- [ ] Past events archive
- [ ] Optional: iCal feed for subscribing to the calendar

### 3.5 Community Interaction

- [ ] **Reactions** on posts/photos (simple likes or emoji reactions — low friction, no login required or very lightweight login)
- [ ] **Comments** on news posts (with moderation to prevent spam)
- [ ] **Social sharing** buttons — Signal, email, copy link (no Meta-owned platforms without explicit project owner approval)
- [ ] **Newsletter / notifications** — optional email subscription for new posts or upcoming events
- [ ] Consider: a simple "guestbook" or "wall" where visitors can leave messages

### 3.6 Static / Informational Pages

- [ ] About page (who we are, history, 25th anniversary)
- [ ] Location page with map, 360° tour embed, and directions
- [ ] NME (nature education) program information
- [ ] Activities: children's parties, venue rental, wines
- [ ] Become a donor / volunteer pages with calls to action
- [ ] Contact page with form and details
- [ ] Privacy statement
- [ ] Links to partner organizations

### 3.7 Search & Navigation

- [ ] Clear, intuitive navigation menu (mobile hamburger + desktop horizontal)
- [ ] Site search functionality
- [ ] Breadcrumbs for deeper pages

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Fast page loads (target < 2s on mobile)
- Optimized images (automatic resizing/compression on upload)
- Static generation or caching where possible

### 4.2 Accessibility
- WCAG 2.1 AA compliance as a target
- Semantic HTML, proper heading hierarchy, alt text on images
- Keyboard navigable

### 4.3 Security
- HTTPS everywhere
- Spam protection on forms and comments (e.g., honeypot, rate limiting)
- Secure admin authentication
- Regular backups

### 4.4 SEO
- Proper meta tags, Open Graph tags, structured data
- Sitemap.xml and robots.txt
- Clean, readable URLs (Dutch-friendly slugs)
- Preserve/redirect existing URLs where possible during migration

### 4.5 Hosting & Operations
- Low-cost or free-tier hosting suitable for a non-profit / stichting
- Minimal server management (prefer managed/serverless solutions)
- Easy deployment process

---

## 5. Design Direction

### Look & Feel
- **Nature-inspired** color palette (greens, earth tones — aligned with current branding)
- Clean, modern layout with generous whitespace
- Photography-forward: large, beautiful nature images as a core visual element
- Warm and welcoming tone — this is a community place, not a corporate site

### Branding
- Retain the De Kievit logo and identity
- Consistent with existing print materials where applicable

### Inspiration
- Brand color palette and usage:
  - `#B5C1B4` — sage green → **header**
  - `#3A3B3D` — dark charcoal → **footer**
  - `#DCD9C6` — beige → **top nav**
  - `#FFFFFF` — white → **body/content area**
- Consider a more modern typography pairing than the current Droid Serif / Century Gothic

---

## 6. Open Questions & Decisions

> These need to be discussed and decided before implementation begins.

1. **Tech stack** — ✅ Decided for PoC: Python (FastAPI) + SQLite + Jinja2. Standalone app with API-first design. Potential WordPress integration later via JS embed widget.

2. **Authentication model** — How do visitors interact?
   - PoC: no login for gallery browsing; simple auth (basic auth / token) for admin moderation queue
   - Future: lightweight login (magic link) for comments

3. **Photo storage** — ✅ Decided: local storage. Download and store images from Fediverse locally (respect source servers, survive deletions). Auto-resize/compress on upload.

4. **Facebook / Meta integration** — What level of integration?
   - ⚠️ No Meta-owned platform integration without explicit project owner approval
   - Website and Fediverse are the primary channels
   - Signal preferred over WhatsApp for messaging share buttons
   - Future: evaluate additional open channels as they emerge

5. **Domain & hosting** — Keep dekievitharmelen.nl? What hosting provider?

6. **Content migration** — How much existing content to migrate?
   - All 37+ pages of news posts?
   - Just key static pages?
   - Fresh start with archival link to old site?

7. **Budget** — What are the constraints for hosting, domain, and any paid services?

8. **Who maintains it?** — Which volunteers will be responsible for content updates? What is their technical comfort level?

---

## 8. PoC Scope — Photo Gathering & Sharing

> The proof of concept focuses narrowly on the **photo submission and distribution pipeline**: getting community photos onto the website and out to open channels.

### In scope (PoC)

1. **Community photo upload form** — public submission form with name/email, multi-photo upload, GDPR consent
2. **Moderation queue** — admin interface to approve/reject submitted photos
3. **Album-based gallery** — display approved photos organized by event/theme, with lightbox viewing
4. **Distribution pipeline**:
   - RSS/Atom feed for new photos/albums
   - Fediverse auto-post (Mastodon/Pixelfed)
   - Share buttons: Signal, email, copy link
5. **Image processing** — auto-resize/compress on upload
6. **Spam prevention** — honeypot, rate limiting, file validation

### Out of scope (PoC) — to be built later

- News/blog system
- Events calendar
- Comments and reactions
- Newsletter/notifications
- Static informational pages
- Full admin CMS
- Content migration from existing WordPress site
- WordPress embed widget (API-first design keeps this option open for later)

---

## 9. Success Criteria

- Volunteers can independently publish a news post with photos within 10 minutes
- The website loads in under 2 seconds on a mobile connection
- Photo galleries are visually engaging and easy to browse
- Visitors can find upcoming events and contact information within 2 clicks from the homepage
- The site appears in top search results for "de kievit harmelen" and related nature education queries
- Community engagement metrics (comments, reactions, shares) show activity beyond just the maintainers
