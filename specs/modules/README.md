# Module backlog

The platform, cut into modules that can each be mapped in one run. Generated route data lives in
`INVENTORY.md` (`python -m impact.app_map`); this file is the curated, prioritised list.

Per module: `/map-module <slug>` → review checkpoint → `/module-tests <slug>` → run on QA.
A module is **done** when its requirements show as `live` in `python -m impact.coverage`.

Status: `todo` · `mapped` (spec written, no tests) · `tested` · `skip`.

## Buyer (first)

| # | Slug | Prefix | Routes | Status |
|---|---|---|---|---|
| 1 | `buyer-browse` **(pilot)** | BUY-BRW | `/buyer/browse` | todo |
| 2 | `buyer-cue-card` **(pilot)** | BUY-CUE | `/buyer/cue-card/:uid`, `/buyer/view-cue-card/:uid`, `/buyer/view-pitchdeck/:uid` | todo |
| 3 | `buyer-login` | BUY-LGN | `/buyer/login`, `/buyer/sharedcard/login`, `/social-auth-login` | todo |
| 4 | `buyer-onboarding` | BUY-ONB | `/buyer/onboarding`, `/buyer/questionnarie`, `/buyer/tnc-consent` | todo |
| 5 | `buyer-deals` | BUY-DLS | `/buyer/deals`, `/buyer/deallink/:uid` | todo |
| 6 | `buyer-recommendations` | BUY-REC | `/buyer/recommendations`, `/buyer/recocardlisting/:uid?`, `/buyer/shortlisted` | todo |
| 7 | `buyer-categories` | BUY-CAT | `/buyer/categories/:uid`, `/buyer/cuecardlisting/:uid` | todo |
| 8 | `buyer-mandates` | BUY-MND | `/buyer/mandate`, `/buyer/mandate/:uid` | todo |
| 9 | `buyer-profile` | BUY-PRF | `/buyer/profile` | todo |
| 10 | `buyer-shared-card` | BUY-SHR | `/buyer/sharedcard/:uid`, `/buyer/digestlisting` | todo |

## Seller

| # | Slug | Prefix | Routes | Status |
|---|---|---|---|---|
| 11 | `seller-deals` | SEL-DLS | `/deals/:companyId?` | todo |
| 12 | `seller-data-room` | SEL-DTR | `/dataroom/:uid?` | todo |
| 13 | `seller-dashboard` | SEL-DSH | `/dashboard`, `/analytics` | todo |
| 14 | `seller-onboarding` | SEL-ONB | `/seller-onboarding`, `/valq`, `/intro` | todo |
| 15 | `seller-profile` | SEL-PRF | `/seller-profile/:companyId?`, `/profile-view/:uid`, `/cue-card/:companyId` | todo |
| 16 | `seller-mandates` | SEL-MND | `/seller-mandates` | todo |
| 17 | `seller-meetings` | SEL-MTG | `/scheduleCall`, `/dynamicMeetingLink/:uid` | todo |
| 18 | `valuation-calculator` | VAL-CLC | `/valuation`, `/valuation-calculator` | todo |

## Admin

| # | Slug | Prefix | Routes | Status |
|---|---|---|---|---|
| 19 | `admin-deals` | ADM-DLS | `/admin/deals` | todo |
| 20 | `admin-deal-notes` | ADM-DLN | `/admin/deal-notes/:uid`, `/admin/notes/:uid` | todo |
| 21 | `admin-buyers` | ADM-BYR | `/admin/buyer`, `/admin/buyer/profile-page/:uid` | todo |
| 22 | `admin-sellers` | ADM-SLR | `/admin/seller`, `/admin/cue-card/:uid` | todo |
| 23 | `admin-mandates` | ADM-MND | `/admin/mandate`, `/admin/mandate/:uid` | todo |
| 24 | `admin-leads` | ADM-LDS | `/admin/leads`, `/admin/lead-profile/:uid?` | todo |
| 25 | `admin-calls` | ADM-CLS | `/admin/calls` | todo |
| 26 | `admin-templates` | ADM-TPL | `/admin/email-templates` | todo |
| 27 | `admin-offplatform` | ADM-OFF | `/admin/offplatform`, `/admin-listing` | todo |
| 28 | `admin-home` | ADM-HOM | `/admin/home`, `/admin/market-signals` | todo |
| 29 | `admin-login` | ADM-LGN | `/admin/login` | todo |

## Biz user

| # | Slug | Prefix | Routes | Status |
|---|---|---|---|---|
| 30 | `biz-user-buyer-view` | BIZ-BYR | buyer screens seen by a biz user | todo |
| 31 | `biz-user-seller-view` | BIZ-SLR | `/admin-user/dashboard/:companyId` | todo |

## Cross-role journeys (after the modules they cross)

| # | Slug | Prefix | Covers | Status |
|---|---|---|---|---|
| 32 | `journey-interest-to-intro` | JRN-INT | buyer express interest → seller accept → intro pending | todo |
| 33 | `journey-mandate-match` | JRN-MND | buyer mandate → admin match → seller | todo |
| 34 | `journey-seller-onboarding-live` | JRN-ONB | seller onboarding → listing live → visible to buyers | todo |

## Not planned

| Route | Why |
|---|---|
| `/buyer/not-found`, `/admin/not-found`, `/not-found`, `/login`, `/signup` | redirects and 404s; one smoke test covers them |
| `/buyer/deeplink`, `/unsubscribe`, `/user-auth` | entry points driven by email links; check manually |

## Notes

- **Prefixes are permanent.** Tests name them and the coverage report and impact analysis read them.
- **The two pilots are one unit:** browse is how every buyer test reaches a company, so its page
  object and the cue card's are settled together before anything else is written.
- **Data cost:** each module spec records what a full run consumes. Express interest and accept are
  one-time per company, so modules touching them stay `destructive` and don't run in parallel.
- **Feature work doesn't wait for this backlog.** A new PRD goes through `/new-feature-tests`; if it
  touches a module already mapped, its impact is proposed against that module.
