# Application route inventory

Read from /Users/mainadmin/Desktop/donedeal-web/src. A route counts as covered when a module spec's footprint lists it.

64 routes.

## admin (20)

| Route | Renders | Source | Module spec |
|---|---|---|---|
| `/admin-listing` | AdminListing | `src/RoutesStructure/index.js` | **none** |
| `/admin-user/dashboard/:companyId` | SellerDashboardHomeComponent | `src/RoutesStructure/index.js` | **none** |
| `/admin/buyer` | AdminBuyer | `../Container/AdminContainer/AdminBuyer` | **none** |
| `/admin/buyer/profile-page/:uid` | BuyerProfile | `../Container/AdminContainer/BuyerProfile` | **none** |
| `/admin/calls` | AdminCallsContainer | `../Container/AdminContainer/AdminCalls` | **none** |
| `/admin/cue-card/:uid` | CuecardContainer | `../Container/CuecardContainer` | **none** |
| `/admin/deal-notes/:uid` | DealNotesContainer | `../Container/DealNotesContainer` | **none** |
| `/admin/deals` | AdminDealsContainer | `../Container/AdminContainer/AdminDeals` | **none** |
| `/admin/email-templates` | EmailTemplates | `../Container/AdminContainer/EmailTemplates` | **none** |
| `/admin/home` | AdminHome | `../Container/AdminContainer/AdminHome` | **none** |
| `/admin/lead-profile/:uid?` | LeadProfile | `../Container/AdminContainer/LeadProfile` | **none** |
| `/admin/leads` | AdminLeadsContainer | `../Container/LeadContainer` | **none** |
| `/admin/login` | AuthFallbackRedirect | `./AuthFallbackRedirect` | **none** |
| `/admin/mandate` | AdminMandatesContainer | `../Container/AdminContainer/AdminMandates` | **none** |
| `/admin/mandate/:uid` | MandateDetailsContainer | `../Container/AdminContainer/MandateDetailsContainer` | **none** |
| `/admin/market-signals` | MarketSignals | `../Container/AdminContainer/MarketSignals` | **none** |
| `/admin/not-found` | AuthFallbackRedirect | `./AuthFallbackRedirect` | **none** |
| `/admin/notes/:uid` | SellerNotesContainer | `../Container/SellerNotesContainer` | **none** |
| `/admin/offplatform` | OffPlatform | `../Container/OffPlatform` | **none** |
| `/admin/seller` | AdminSeller | `../Container/AdminContainer/AdminSeller` | **none** |

## buyer (23)

| Route | Renders | Source | Module spec |
|---|---|---|---|
| `/buyer/browse` | BrowserScreen | `../../Container/BuyersContainer/BrowserScreen` | **none** |
| `/buyer/categories/:uid` | BuyerCategoryDetails | `../../Component/BuyerComponent/BuyerCategories/BuyerCategoryDetails` | **none** |
| `/buyer/cue-card/:uid` | CuecardContainer | `../../Container/CuecardContainer` | **none** |
| `/buyer/cuecardlisting/:uid` | CueCardListingRedirect | `../../Container/CuecardBookListing/components/CueCardListingRedirect` | **none** |
| `/buyer/deallink/:uid` | DealLinkContainer | `../../Container/DealLinkContainer` | **none** |
| `/buyer/deals` | BuyerDealsContainer | `../../Container/BuyersDealsContainer` | **none** |
| `/buyer/deeplink` | DeepLink | `../../CommonComponent/DeepLink` | **none** |
| `/buyer/digestlisting` | DigestListing | `../../Container/DigestListing` | **none** |
| `/buyer/login` | NewLoginContainer | `../../Container/NewLoginContainer` | **none** |
| `/buyer/mandate` | BuyerMandatesContainer | `../../Container/BuyersContainer/BuyerMandate` | **none** |
| `/buyer/mandate/:uid` | BuyerMandateDetailsContainer | `../../Container/BuyersContainer/BuyerMandateDetailsContainer` | **none** |
| `/buyer/not-found` | AuthFallbackRedirect | `../AuthFallbackRedirect` | **none** |
| `/buyer/onboarding` | BuyersOnboarding | `../../Container/BuyersContainer/BuyersOnboarding` | **none** |
| `/buyer/profile` | BuyersProfile | `../../Container/BuyersContainer/BuyersProfile` | **none** |
| `/buyer/questionnarie` | Questionnarie | `../../Container/Questionnarie` | **none** |
| `/buyer/recocardlisting/:uid?` | RecoCueCardListing | `../../Container/RecoCueCardListing` | **none** |
| `/buyer/recommendations` | BuyerRecommendations | `../../Container/BuyersContainer/BuyerRecommendations` | **none** |
| `/buyer/sharedcard/:uid` | SharedCueCard | `../../Container/SharedCueCard` | **none** |
| `/buyer/sharedcard/login` | SharedLogin | `../../Container/Login/SharedLogin` | **none** |
| `/buyer/shortlisted` | BuyerShortlisted | `../../Container/BuyersContainer/BuyerShortlisted` | **none** |
| `/buyer/tnc-consent` | TncConsentContainer | `../../Container/TncConsentContainer` | **none** |
| `/buyer/view-cue-card/:uid` | OpenCuecardView | `../../Container/OpenCuecardView` | **none** |
| `/buyer/view-pitchdeck/:uid` | OpenPitchdeckView | `../../Container/OpenPitchdeckView` | **none** |

## seller/public (21)

| Route | Renders | Source | Module spec |
|---|---|---|---|
| `/analytics` | SellerAnalytics | `../Container/SellerAnalytics` | **none** |
| `/cue-card/:companyId` | CueCard | `src/RoutesStructure/index.js` | **none** |
| `/dashboard` | SellerDashboardHomeComponent | `src/RoutesStructure/index.js` | **none** |
| `/dataroom/:uid?` | DataRoomHomeComponent | `src/RoutesStructure/index.js` | **none** |
| `/deals/:companyId?` | SellerDealsHomeComponent | `src/RoutesStructure/index.js` | **none** |
| `/dynamicMeetingLink/:uid` | DynamicMeetingLink | `../Container/DynamicMeetingLink` | **none** |
| `/intro` | QuestionnaireFillerScreen | `../Component/QuestionnaireFillerScreen` | **none** |
| `/login` | NotFound | `../Container/NotFound` | **none** |
| `/not-found` | NotFound | `../Container/NotFound` | **none** |
| `/profile-view/:uid` | SellerCuecardViewComponent | `src/RoutesStructure/index.js` | **none** |
| `/scheduleCall` | ScheduleCall | `../Container/ScheduleCall` | **none** |
| `/seller-mandates` | SellerMandatesComponent | `src/RoutesStructure/index.js` | **none** |
| `/seller-onboarding` | SellerOnboardingComponent | `src/RoutesStructure/index.js` | **none** |
| `/seller-profile/:companyId?` | SellerProfile | `../Container/SellerProfile` | **none** |
| `/signup` | NotFound | `../Container/NotFound` | **none** |
| `/social-auth-login` | SocialLoginContainer | `../Container/SocialLoginContainer` | **none** |
| `/unsubscribe` | UnsubscribePage | `../Container/UnsubscribePage` | **none** |
| `/user-auth` | UserAuthentication | `src/RoutesStructure/index.js` | **none** |
| `/valq` | SellerOnboardingComponent | `src/RoutesStructure/index.js` | **none** |
| `/valuation` | Valuation | `../Component/Valuation` | **none** |
| `/valuation-calculator` | ValuationCalculator | `../Container/ValuationCalculator` | **none** |

