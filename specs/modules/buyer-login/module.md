# Buyer Login (email + OTP) — module spec

Slug: buyer-login · Roles: buyer · Mapped: 2026-09-23
Sources: code; QA walk (yes, logged-out screens + the already-authenticated redirect); Figma (not current — not consulted)

## Scope

`/buyer/login`, the two-step **email → 6-digit passcode** sign-in for buyers, rendered by
`src/Container/NewLoginContainer/index.js` through `src/Container/BuyersContainer/BuyerLogin/index.js`.
Covers: the email step and its validation, the passcode request, the unregistered-email branch, the OTP
step and its errors, resend, what a successful login writes to localStorage and Redux, and where the
buyer is sent afterwards (including the already-authenticated redirect on this route).

**Deliberately excluded** (listed here so a later module or feature picks them up, not because they are
untested-by-accident):

| Excluded | Where it lives |
|---|---|
| Google sign-in (`Continue with Google`, personal-email warning, OTP fallback) | `src/CommonComponent/GoogleSignInButton/index.js`, `NewLoginContainer/index.js:288-311` |
| Saved-profile / one-tap login (`SavedProfileLogin`, `handleOneTapLogin`) | `src/Component/SavedProfileLogin/`, `NewLoginContainer/index.js:433-494` — currently unreachable: the `SAVED_PROFILE_KEY` reader is commented out (`:110-125`), so `isSavedLoginInfo` is always false |
| Device/session rules (`DEVICE_SESSION_ALREADY_ACTIVE`, `DEVICE_TOKEN_*`, `DEVICE_NOT_REGISTERED`, `user/device/register`) | `NewLoginContainer/index.js:398-431,452-471` |
| `/buyer/sharedcard/login` and `/social-auth-login` | `src/Container/Login/SharedLogin`, social-auth route |
| `/admin/login` and seller `/login` (same container, `isAdminUser` / `userType: 2`) | `src/Routes/AdminRoutes.js:288`, `src/Container/Login/` — neighbouring **admin-login** / **seller-login** modules |
| Buyer onboarding / signup after an unregistered email | `/buyer/onboarding` → neighbouring **buyer-onboarding** module (this spec asserts only the hand-off) |
| Logout, session expiry, forbidden modal | `src/Container/HomeLayoutContainer/LogoutModal`, `src/utils/apiService.js` |

Where the post-login redirect depends on buyer verification status, this spec asserts the redirect only;
the profile/onboarding screens themselves belong to **buyer-onboarding** and **buyer-profile**.

## Screens and states

| # | Screen | How to reach it | States | Rendered by |
|---|---|---|---|---|
| S1 | Email step (step 1) | `GET /buyer/login` logged out | default; field error (empty / malformed / unregistered / backend message); global loader while `user/send/passcode` is in flight | `NewLoginContainer/index.js:165-172` → `Component/LoginFormField/index.js` inside `BuyersContainer/BuyerLogin/index.js` |
| S2 | Passcode step (step 2, "Check Your Device") | submit a registered email at S1 | default (email only); email + mobile when the passcode response carries `mobile`; empty-code error; wrong-code error; resend snackbar | `NewLoginContainer/index.js:168` → `Component/NewAuthOtpFlow/index.js` |
| S3 | S2 reached directly on mount | arrive with `authorizationStore.passcodeSuccessData.payload.postBody.email` set (came from buyer onboarding/signup) | same as S2, passcode auto-sent | `NewLoginContainer/index.js:69-82` |
| S4 | S2 reached via a buyer link | `/buyer/login?listingUid=…` or `?pocUid=…`, or arriving from such a path | same as S2, email prefilled from `buyer/linkInfo` | `NewLoginContainer/index.js:84-108` |
| S5 | No screen — redirect | open `/buyer/login` with a live session | redirected to the buyer's landing route (or `/buyer/onboarding`) | `src/Routes/NonProtectedRoutes/index.js:14-30` |

Out-of-scope surfaces that are nevertheless **visible on S1/S2** and will appear in locator work: the
"Continue with Google" decoy button and the "Use a work email to Sign in" caption (see Code facts).

## Requirements

| ID | Requirement | Type | Role | Testable via | Source | Evidence |
|---|---|---|---|---|---|---|
| BUY-LGN-01 | `/buyer/login` renders the buyer login container at step 1, with document title "Login - Done Deal". | flow | buyer | UI | code, qa-walk | `BuyerRoutes.js:103-111`; `App.js:48`; `PageMeta.js:23-25`; `NewLoginContainer/index.js:53,59` |
| BUY-LGN-02 | Step 1 shows the heading "Enter your email to continue" and the subtitle "We'll verify your email and take you forward." | copy | buyer | UI | qa-walk, code | `LoginFormField/index.js:28-29`; walk 01 |
| BUY-LGN-03 | Step 1 labels the field "Official Email ID*" with placeholder "Enter your work email". | copy | buyer | UI | qa-walk, code | `LoginFormField/index.js:32,40`; `NewLoginContainer/index.js:42`; walk 01 |
| BUY-LGN-04 | Step 1 shows the hint "A 6-digit code will be sent to your email and mobile for verification." | copy | buyer | UI | qa-walk, code | `LoginFormField/index.js:45`; walk 01 |
| BUY-LGN-05 | The step-1 CTA reads "Verify". | copy | buyer | UI | qa-walk, code | `NewLoginContainer/index.js:33`; `BuyerLogin/index.js:63`; walk 01 |
| BUY-LGN-06 | Step 1 shows "Don't have an account? Sign up here", linking to `/buyer/onboarding`. | copy | buyer | UI | qa-walk, code | `BuyerLogin/index.js:102-118`; walk 01 |
| BUY-LGN-07 | Submitting step 1 with an empty email shows "Please enter your registered email ID" under the field. | edge-case | buyer | UI | qa-walk, code | `NewLoginContainer/index.js:355-361`; constant `constants/index.js:169`; walk 02 |
| BUY-LGN-08 | Submitting step 1 with an empty email sends no API request. | edge-case | buyer | UI+API | qa-walk | `NewLoginContainer/index.js:357-360` (early return); walk 02 recorded 0 API calls |
| BUY-LGN-09 | Submitting a malformed email (no `@` or no dot-suffix) shows "Please enter your registered email ID" and stays on step 1. | rule | buyer | UI | qa-walk, code | `commonHelper.js:28-30`; `NewLoginContainer/index.js:357-360`; walk 03 |
| BUY-LGN-10 | A malformed email sends no API request. | rule | buyer | UI+API | qa-walk | walk 03 recorded 0 API calls |
| BUY-LGN-11 | Editing the email after an error clears the error state and hides the helper text. | flow | buyer | UI | code | `NewLoginContainer/index.js:150-159` |
| BUY-LGN-12 | Submitting a well-formed email posts `user/send/passcode` with `{email, userType: 3}`. | flow | buyer | UI+API | qa-walk, code | `NewLoginContainer/index.js:362-372`; `endpoint.js:17`; walk 04/05 payloads |
| BUY-LGN-13 | The first passcode request carries no `resend` key. | rule | buyer | API | qa-walk, code | `NewLoginContainer/index.js:367` (`resend: undefined` dropped by `JSON.stringify`); walk 04/05 payloads |
| BUY-LGN-14 | Leading/trailing whitespace is stripped from the email in the passcode payload. | edge-case | buyer | UI+API | code | `NewLoginContainer/index.js:365` (`.trim()`); `commonHelper.js:29` (regex tolerates surrounding `\s`) |
| BUY-LGN-15 | An unregistered email makes `user/send/passcode` answer HTTP 400 with body `{status:"400", data:{code:"not_registered"}}`, and the app follows it with `GET user/emailCheck?email=<email>&primaryIdType=buyer`. | flow | buyer | UI+API | qa-walk, code | `NewLoginContainer/index.js:213-222`; `endpoint.js:235`; walk 04 |
| BUY-LGN-16 | When `user/emailCheck` returns `data: false`, step 1 shows "Please register using your professional email ID." and the buyer stays on `/buyer/login`. | rule | buyer | UI+API | qa-walk, code | `NewLoginContainer/index.js:200`; walk 04 |
| BUY-LGN-17 | When `user/emailCheck` returns `data: true`, the buyer is navigated to `/buyer/onboarding` with the current query string preserved. | flow | buyer | UI | code | `NewLoginContainer/index.js:195-199` |
| BUY-LGN-18 | When `user/emailCheck` does not answer `status: "200"`, step 1 shows "Something went bad!!" under the email field. | edge-case | buyer | UI+API | code | `NewLoginContainer/index.js:202-204`; `constants/index.js:168` |
| BUY-LGN-19 | A passcode failure whose code is not `not_registered` shows the backend `message` (or "Something went bad!!") under the email field and keeps the buyer on step 1. | edge-case | buyer | UI+API | code | `NewLoginContainer/index.js:224-227` |
| BUY-LGN-20 | A successful passcode request advances to step 2, headed "Check Your Device". | flow | buyer | UI | qa-walk, code | `NewLoginContainer/index.js:207-211`; `NewAuthOtpFlow/index.js:51`; walk 05 |
| BUY-LGN-21 | Step 2 states where the code went: "We've sent a 6-digit code to <email> . Enter it below to verify and continue securely." | copy | buyer | UI | qa-walk, code | `NewAuthOtpFlow/index.js:52-64`; walk 05 |
| BUY-LGN-22 | When the passcode response carries a `mobile`, step 2 names the email **and** that mobile number. | rule | buyer | UI+API | code | `NewAuthOtpFlow/index.js:14,56-61` |
| BUY-LGN-23 | When the passcode response has `mobile: null`, step 2 names only the email. | rule | buyer | UI+API | qa-walk | `NewAuthOtpFlow/index.js:56`; walk 05 (`{"success":true,"mobile":null}`) |
| BUY-LGN-24 | Step 2 labels the field "Verification code*" with placeholder "Enter 6-digit code". | copy | buyer | UI | qa-walk, code | `NewAuthOtpFlow/index.js:71,79`; `NewLoginContainer/index.js:48`; walk 05 |
| BUY-LGN-25 | The step-2 CTA reads "Verify & Login". | copy | buyer | UI | qa-walk, code | `NewLoginContainer/index.js:34`; walk 05 |
| BUY-LGN-26 | Submitting step 2 with an empty code shows the OTP helper text and makes no login request. | edge-case | buyer | UI+API | code | `NewLoginContainer/index.js:230-236` (early return); helper `constants/index.js:167` |
| BUY-LGN-27 | Submitting a code posts `user` with `{email, passcode, device: navigator.platform}`. | flow | buyer | UI+API | code | `NewLoginContainer/index.js:237-245`; `endpoint.js:5`; saga `Redux/saga/Login/index.js:8-19` |
| BUY-LGN-28 | An incorrect code keeps the buyer on step 2 and shows the backend `message` (or "Something went bad!!") under the code field. | edge-case | buyer | UI+API | code | `NewLoginContainer/index.js:275-280` |
| BUY-LGN-29 | The pencil icon beside the email returns to step 1, keeps the typed email and clears the code value, its error and its helper. | flow | buyer | UI | code | `NewAuthOtpFlow/index.js:65-68`; `NewLoginContainer/index.js:350-353,342-348` |
| BUY-LGN-30 | Step 2 shows "Didn't receive the code? Click here to resend"; clicking "Click here" re-posts `user/send/passcode` with `resend: true`. | flow | buyer | UI+API | qa-walk, code | `BuyerLogin/index.js:67-78`; `NewLoginContainer/index.js:355-372`; walk 05 |
| BUY-LGN-31 | A successful resend shows the snackbar "Passcode Sent". | copy | buyer | UI | code | `NewLoginContainer/index.js:374-379` |
| BUY-LGN-32 | A failed resend shows the snackbar "Please try again later". | edge-case | buyer | UI+API | code | `NewLoginContainer/index.js:384-389` |
| BUY-LGN-33 | After a rejected code, a successful resend empties the code field. | flow | buyer | UI | code | `NewLoginContainer/index.js:279,380-382` |
| BUY-LGN-34 | A successful login stores the backend `sessionID` in `localStorage.authToken`. | flow | buyer | UI+API | code | `NewLoginContainer/index.js:255,283-286`; `Services/index.js:79` |
| BUY-LGN-35 | A successful login removes the pre-login `sessionid` localStorage key. | rule | buyer | UI | code | `Services/index.js:80`; the key is written pre-login by `apiService.js:105-109` (observed in walk 04) |
| BUY-LGN-36 | A successful buyer login stores the buyer `uid` in `localStorage.buyerId` and removes `seller_uid`. | rule | buyer | UI | code | `commonHelper.js:1058-1060` |
| BUY-LGN-37 | A successful login removes `saved_buyer_profile` and `saveLoginModalShown` from localStorage. | rule | buyer | UI | code | `NewLoginContainer/index.js:250-254`; keys `constants/index.js:307-308` |
| BUY-LGN-38 | A successful login puts the login response (`userType`, `email`, `isBuyer`, `name`, `phone`, `sessionId`, …) into `authorizationStore.loginResponse`. | flow | buyer | UI | code | `Services/index.js:65-78` |
| BUY-LGN-39 | After a successful buyer login the app calls `buyer/status` before it redirects. | flow | buyer | UI+API | code | `NewLoginContainer/index.js:264-268`; `Redux/saga/BuyerVerification/index.js:5-17`; `endpoint.js:126` |
| BUY-LGN-40 | A verified buyer with no in-app previous path lands on `/buyer/recommendations` at desktop width (> 1180px). | flow | buyer | UI | qa-walk, code | `commonHelper.js:1030-1036`; `Services/index.js:25-32`; `commonHelper.js:182-184`; walk 07 |
| BUY-LGN-41 | The same buyer lands on `/buyer/browse` at mobile/tablet width (<= 1180px). | rule | buyer | UI | code | `Services/index.js:28-29`; `commonHelper.js:173-184` |
| BUY-LGN-42 | A buyer whose `buyer/status` is `not_verified` lands on `/buyer/profile`. | gating | buyer | UI+API | code | `NewLoginContainer/index.js:319-325` |
| BUY-LGN-43 | A `not_verified` buyer whose previous in-app path contains `/buyer/sharedcard` is returned to that path instead. | rule | buyer | UI | code | `NewLoginContainer/index.js:320-323` |
| BUY-LGN-44 | A buyer whose status is neither `verified` nor `not_verified`, and whose previous path does not contain `/buyer/cuecardlisting`, lands on `/buyer/profile`. | gating | buyer | UI+API | code | `NewLoginContainer/index.js:327-330` |
| BUY-LGN-45 | A verified buyer who was bounced to login from a buyer route is returned to that route after login. | flow | buyer | UI | code | `commonHelper.js:994-1032`; allow-list `constants/RouteConstants.js:53,74-88`; previous path written by `HomeLayoutContainer/index.js:86-91` |
| BUY-LGN-46 | A previous path of `/buyer/profile`, `/admin/seller`, `/login` or `/signup` is ignored, and the buyer gets the default landing route instead. | rule | buyer | UI | code | `commonHelper.js:1007-1012` |
| BUY-LGN-47 | Opening `/buyer/login` with a live buyer session never shows the login form: the buyer is redirected to their landing route. | gating | buyer | UI | qa-walk, code | `NonProtectedRoutes/index.js:14-30,36-40`; walk 07 (→ `/buyer/recommendations`) |
| BUY-LGN-48 | Opening `/buyer/login` with a live session whose buyer verification state has no `onboardingStage`, or `onboardingStage === 1`, redirects to `/buyer/onboarding`. | gating | buyer | UI | code | `NonProtectedRoutes/index.js:16-24` |
| BUY-LGN-49 | Landing on `/buyer/login` while a passcode was already requested for an email in this session prefills that email and auto-sends a new passcode, opening step 2 without a click. | flow | buyer | UI+API | code | `NewLoginContainer/index.js:65,72-77`; passcode state stored by `Redux/saga/Login/index.js:64` |
| BUY-LGN-50 | Clicking "Sign up here" clears that stored passcode state, so a later return to `/buyer/login` starts at step 1. | rule | buyer | UI | code | `BuyerLogin/index.js:110-112`; `NewLoginContainer/index.js:69-77` |
| BUY-LGN-51 | Arriving at `/buyer/login` with `listingUid=<uuid>` or `pocUid=<uuid>` (in the URL or in the previous in-app path) posts `buyer/linkInfo`, prefills the returned email and opens step 2. | flow | buyer | UI+API | code | `NewLoginContainer/index.js:84-108,127-138`; `endpoint.js:142` |
| BUY-LGN-52 | Without `listingUid` / `pocUid`, `/buyer/login` makes no `buyer/linkInfo` call. | gating | buyer | UI+API | qa-walk, code | `NewLoginContainer/index.js:91-93`; walk 01 recorded no `linkInfo` call |
| BUY-LGN-53 | Step 1 fires the PostHog event `buyer_landed_login_screen`; step 2 fires `buyer_landed_login_password_screen`. | non-functional | buyer | manual | code | `LoginFormField/index.js:18-24`; `NewAuthOtpFlow/index.js:16-23`; `posthogEvents.js:22-23` |
| BUY-LGN-54 | Clicking the step-2 CTA fires `buyer_login_clicked`; a successful login fires `buyer_signed_in` and the GA4 `login` event. | non-functional | buyer | manual | code | `NewLoginContainer/index.js:392-396,269-272`; `commonHelper.js:1063`; `posthogEvents.js:2,55`; `GAeventsConstants.js:1` |
| BUY-LGN-55 | On the whole `/buyer/*` shell, including `/buyer/login`, injecting any DOM element whose id, class or attribute name/value contains "claude" (or `codex-agent-overlay-root`) clears localStorage and sessionStorage and hard-navigates to `/buyer/login`. | non-functional | buyer | UI | code | `BuyerRouteStructure/index.js:19`; `hooks/useClaudeElementDetector.js:3-28,60-95` (no env gate) |
| BUY-LGN-56 | On QA the viewport guard and the focus-loss blur never trip, because both are gated on the production environment. | non-functional | buyer | UI | code | `hooks/useViewportGuard.js:24-31`; `hooks/useBlurOnFocusLoss.js:17` |

## Acceptance criteria

- **BUY-LGN-01** Given a logged-out browser, when it opens `/buyer/login`, then the email step renders and the tab title is "Login - Done Deal".
- **BUY-LGN-02** Given step 1, then "Enter your email to continue" and "We'll verify your email and take you forward." are visible.
- **BUY-LGN-03** Given step 1, then the field label is "Official Email ID" with a red asterisk, and the input placeholder is "Enter your work email".
- **BUY-LGN-04** Given step 1, then "A 6-digit code will be sent to your email and mobile for verification." is visible.
- **BUY-LGN-05** Given step 1, then the submit button's text is exactly "Verify".
- **BUY-LGN-06** Given step 1 on `/buyer/login`, then a link "Sign up here" is present with `href="/buyer/onboarding"`.
- **BUY-LGN-07 / 08** Given an empty email field, when "Verify" is clicked, then "Please enter your registered email ID" appears under the field and no request to the API base is made.
- **BUY-LGN-09 / 10** Given the email `not-an-email`, when "Verify" is clicked, then the same helper appears, the URL is still `/buyer/login`, and no API request is made.
- **BUY-LGN-11** Given the helper is showing, when one character is typed into the email field, then the helper disappears and the field is no longer in the error state.
- **BUY-LGN-12 / 13** Given `DD_BUYER_LOGIN_EMAIL`, when "Verify" is clicked, then exactly one `POST user/send/passcode` is sent whose body is `{"email": "<that email>", "userType": 3}` with no `resend` key.
- **BUY-LGN-14** Given the email typed with a leading and trailing space, when "Verify" is clicked, then the `email` in the payload has no surrounding whitespace.
- **BUY-LGN-15** Given `DD_BUYER_LOGIN_UNREGISTERED_EMAIL`, when "Verify" is clicked, then `user/send/passcode` answers HTTP 400 with `data.code == "not_registered"`, and a `GET user/emailCheck` follows with that email and `primaryIdType=buyer`.
- **BUY-LGN-16** Given that `emailCheck` returns `data: false`, then "Please register using your professional email ID." is shown under the email field and the URL is still `/buyer/login`.
- **BUY-LGN-17** Given `emailCheck` returns `data: true` (rewrite the response to test it), then the browser navigates to `/buyer/onboarding` and any query string on the login URL is still present.
- **BUY-LGN-18** Given `emailCheck` is rewritten to `status: "500"`, then "Something went bad!!" is shown under the email field.
- **BUY-LGN-19** Given `user/send/passcode` is rewritten to `{status:"400", data:{code:"blocked", message:"Account locked"}}`, then "Account locked" is shown under the email field and step 1 is still on screen.
- **BUY-LGN-20 / 21 / 23 / 24 / 25** Given `DD_BUYER_LOGIN_EMAIL` submitted successfully, then step 2 shows "Check Your Device", the sentence "We've sent a 6-digit code to <email> . Enter it below to verify and continue securely." with no mobile number (QA answers `mobile: null`), the label "Verification code", the placeholder "Enter 6-digit code" and the CTA "Verify & Login".
- **BUY-LGN-22** Given `user/send/passcode` is rewritten with `data.mobile = "9876543210"`, then step 2 names both the email and that number.
- **BUY-LGN-26** Given step 2 with an empty code, when "Verify & Login" is clicked, then the code field goes into the error state showing "The OTP you entered is incorrect. Please try again." and no `POST user` is sent. *(The copy is wrong for this case — see suspected bug 1.)*
- **BUY-LGN-27** Given `DD_BUYER_LOGIN_OTP`, when "Verify & Login" is clicked, then one `POST user` is sent with `email`, `passcode` and a `device` string.
- **BUY-LGN-28** Given the code `000000` (or a rewritten failure response), when submitted, then step 2 is still on screen and the backend message is shown under the code field. *(Do not run this against a shared test account more than once per run — see Data cost.)*
- **BUY-LGN-29** Given step 2, when the pencil icon after the email is clicked, then step 1 is shown with the email still filled and the code cleared.
- **BUY-LGN-30 / 31** Given step 2, when "Click here" is clicked, then a second `POST user/send/passcode` is sent with `"resend": true` and the snackbar "Passcode Sent" appears.
- **BUY-LGN-32** Given the resend call is rewritten to fail, then the snackbar "Please try again later" appears.
- **BUY-LGN-33** Given a rejected code is on screen, when a successful resend happens, then the code input is empty.
- **BUY-LGN-34…38** Given `DD_BUYER_LOGIN_EMAIL` + `DD_BUYER_LOGIN_OTP` submitted successfully, then `localStorage.authToken` equals the `sessionID` from the `user` response, `localStorage.sessionid` is gone, `localStorage.buyerId` equals the response `uid`, `seller_uid`, `saved_buyer_profile` and `saveLoginModalShown` are absent, and `authorizationStore.loginResponse.userType` is 3.
- **BUY-LGN-39 / 40** Given that same login from a directly-opened `/buyer/login` at 1440×900, then `buyer/status` is requested after `user`, and the browser ends on `/buyer/recommendations`.
- **BUY-LGN-41** Given a 390×844 viewport, then the same login ends on `/buyer/browse`.
- **BUY-LGN-42 / 44** Given `buyer/status` rewritten to `data.status = "not_verified"` (resp. `"pending"`), then the browser ends on `/buyer/profile`.
- **BUY-LGN-43** Given `buyer/status` rewritten to `not_verified` and a previous in-app path under `/buyer/sharedcard`, then the browser returns to that path.
- **BUY-LGN-45** Given a logged-out browser that opens `/buyer/shortlisted`, is bounced to `/buyer/login`, and then logs in, then it ends on `/buyer/shortlisted`.
- **BUY-LGN-46** Given the same with `/buyer/profile` as the bounced-from path, then it ends on the default landing route, not back on `/buyer/profile`.
- **BUY-LGN-47** Given the saved buyer session, when `/buyer/login` is opened, then no email field is ever visible and the final URL is the buyer's landing route.
- **BUY-LGN-48** Given a saved session whose persisted `buyerVerificationStore.buyerVerificationState.onboardingStage` is 1, when `/buyer/login` is opened, then the final URL is `/buyer/onboarding`.
- **BUY-LGN-49** Given a passcode was requested for an email in this browser session, when `/buyer/login` is re-opened, then step 2 renders without any click and a `user/send/passcode` call is made on mount.
- **BUY-LGN-50** Given that state, when "Sign up here" is clicked and `/buyer/login` is opened again, then step 1 renders.
- **BUY-LGN-51** Given `/buyer/login?listingUid=<a known uuid>`, then `POST buyer/linkInfo` is sent with `{listingUid}` and, when it returns an email, step 2 renders with that email.
- **BUY-LGN-52** Given a plain `/buyer/login`, then no `buyer/linkInfo` request is made.
- **BUY-LGN-53 / 54** *(manual)* Confirm in PostHog that `buyer_landed_login_screen`, `buyer_landed_login_password_screen`, `buyer_login_clicked` and `buyer_signed_in` arrive for one run, and the GA4 `login` event on success.
- **BUY-LGN-55** Given `/buyer/login` is open, when a `<div id="claude-probe">` is appended to the document, then localStorage is cleared and the browser hard-navigates to `/buyer/login`. **The test suite must never inject markup whose attributes contain "claude" while on a `/buyer/*` page.**
- **BUY-LGN-56** Given QA (`qa.done.deals`), when the window is resized or loses focus, then no "Screen size changed" panel and no blur are applied.

## Code facts for testers

**Route and guards**
- `App.js:48` mounts `buyer/*` → `BuyerRouteStructure` → `BuyerRoutes.js:103-111`: `path="login"` wrapped in
  `NonProtectedRoute` + `WithTracker` (title "Login - Done Deal").
- `NewLoginContainer` is shared: `/buyer/login` renders it with no props (`step = 1`, `isAdminUser` falsy);
  `/admin/login` renders `<NewLoginContainer isAdminUser/>` (`AdminRoutes.js:288`). Almost every buyer-vs-admin
  branch is a **`window.location.pathname === '/buyer/login'` string check**, not a prop
  (`NewLoginContainer/index.js:213,362`; `BuyerLogin/index.js:103`; `LoginFormField/index.js:15`).
- `NonProtectedRoute` renders nothing until its check has run, then either redirects (`reRouteUser`) or renders
  children — so an assertion on the login form must wait for the field, not for `load`.

**Endpoints** (base `https://qa.done.deals/api/company-service/v1/`)

| Call | Method / URL | Body / params | Observed response |
|---|---|---|---|
| Send passcode (step 1, and resend) | `POST user/send/passcode` (`ENDPOINT.SIGNUP.getPasscodeApi`, `endpoint.js:17`) | `{email, userType: 3, resend?: true}` | success: HTTP 200 `{"status":"200","message":"Success","data":{"success":true,"mobile":null}}`; unregistered: HTTP **400** `{"status":"400","message":"Failure","data":{"code":"not_registered","message":"You are not registered with this email ID"}}` |
| Email check (unregistered branch) | `GET user/emailCheck?email=<email>&primaryIdType=buyer` (`endpoint.js:235`) | query only | `{"status":"200","message":"Success","data":false}` |
| **Login (step 2)** | `POST user` (`ENDPOINT.LOGIN.loginApiPath`, `endpoint.js:5`) | `{email, passcode, device: navigator.platform}` | body carries `status`, `code` (`company_found` on success), `sessionID`, `userType`, `uid`, `email`, `name`, `phone`, `officialSignup`, `classification` |
| Buyer status (post-login gate) | `GET buyer/status` (`endpoint.js:126`) | — | `{status, data:{status: 'verified'\|'not_verified'\|…, onboardingStage, …}}`. **Returned HTTP 502 (HTML body) during this walk** — see oddity 5 |
| Buyer link prefill | `POST buyer/linkInfo` (`endpoint.js:142`) | `{listingUid, pocUid}` | `data.email` |

- **The data request that loads the screen: none.** Step 1 is pure client state; the first API call on
  `/buyer/login` is the passcode request the buyer triggers. Waiting for a "screen loaded" response will hang.
- HTTP status vs body status: `apiService.js:181` returns `error.response` for a failed request, so a 400 or 500
  still resolves and the callback receives the **body**. Every branch in this module tests
  `res.status === '200'` (`API_SUCCESS_CODE`, the *body* field, a string), never the HTTP code. A transport
  failure (no response at all) returns `undefined` instead — see oddity 3.
- A pre-login `sessionid` localStorage key is written from a response header on the first API call
  (`apiService.js:105-109`); it exists during step 1/2 and is removed on login success (`Services/index.js:80`).

**Constants and copy** (all in `src/constants/index.js`; `keyVariableConstants.js` holds **nothing** for this module)
- `INCORRECT_EMAIL_HELPERTEXT` = "Please enter your registered email ID" (`:169`)
- `INCORRECT_OTP_HELPER` = "The OTP you entered is incorrect. Please try again." (`:167`)
- `SOMETHING_WENT_BAD` = "Something went bad!!" (`:168`)
- `API_SUCCESS_CODE` = `'200'` (string, `:180`), `NOT_REGISTERED` = `'not_registered'` (`:191`),
  `COMPANY_FOUND` = `'company_found'` (`:9`)
- `TOKEN_KEY` = `'authToken'` (`:5`), `SESSION_ID` = `'sessionid'` (`:6`), `BUYER_ID` = `'buyerId'` (`:147`),
  `SAVED_PROFILE_KEY` = `'saved_buyer_profile'` (`:307`), `SAVE_LOGIN_MODAL_SHOWN` = `'saveLoginModalShown'` (`:308`)
- Step CTA titles: `StepActionTitle = {1: 'Verify', 2: 'Verify & Login'}` (`NewLoginContainer/index.js:32-35`) —
  the same map drives both the button label and the analytics branch, so asserting the label also pins the event.
- `COMPANY_FOUND` is **not** checked on the email+OTP path; only `body.status === '200'` is
  (`NewLoginContainer/index.js:249`). It is read only in the out-of-scope one-tap path (`:444-445`).

**Element types and selector traps**
- Both inputs are MUI `TextField`s (`CommonComponent/NewTextField`) with **auto-generated ids** (`:r2:`, `:r3:`)
  and **no `name`, no `aria-label` and no `<label for>`**. Select by placeholder ("Enter your work email",
  "Enter 6-digit code") or by `form input`. The email input is `type="text"`, not `type="email"`.
- Helper text renders as `p.MuiFormHelperText-root` and only when the field is in the error state.
- Both CTAs are the **same** `<button type="submit">` (MUI contained) whose label changes with the step, inside
  one `<form onSubmit>`; it is **never disabled**. `get_by_role("button", name="Verify")` matches
  "Verify & Login" too — anchor it exactly.
- "Click here" (resend) is a **`<span>` with `onClick`**, not a button (`BuyerLogin/index.js:70-74`).
- The "edit email" affordance on step 2 is a bare inline **`<svg>` inside a `<span onClick>`** with no accessible
  name (`NewAuthOtpFlow/index.js:65-68`). Locate it relative to the sentence that contains the email.
- The visible "Continue with Google" button is a **decoy**: `aria-hidden="true"`, `tabIndex={-1}`,
  `pointer-events-none`, sitting above the real Google iframe (`GoogleSignInButton/index.js:261-268`).
  `get_by_role("button", name="Continue with Google")` will not find it; a strict-mode "button" query on the
  form will still count it. The caption below reads "Use a work email to Sign in" (uppercased by CSS).
- The OTP input carries `autocomplete="one-time-code"`, `inputMode="numeric"`, `pattern="[0-9]*"` but accepts any
  text; there is no maxlength and no per-digit box.
- Snackbars ("Passcode Sent", "Please try again later") come from the global `updateSnackbar` / `CustomSnackbar`
  in the layout, not from this container.
- The step-1 → step-2 switch is a client-side re-render of the same URL. **The URL never changes across the two
  steps** — assert on copy, not on location.
- `/buyer/*` runs `useClaudeElementDetector(true, …)` with no environment gate
  (`BuyerRouteStructure/index.js:19`): any element whose id/class/attribute name or value contains "claude", or
  the attribute `codex-agent-overlay-root`, clears storage and hard-navigates to `/buyer/login`. Test scaffolding,
  debug overlays and injected banners must avoid that substring on buyer pages.
- `useViewportGuard` (>100px chrome gap → "Screen size changed" full-screen panel) and `useBlurOnFocusLoss`
  (blur on tab focus loss) are **production-only** (`IS_PRODUCTION_ENV`), so they are inert on QA but would break
  a run against production.

**Post-login navigation** (`NewLoginContainer/index.js:248-333`)
1. `handleUserSession` (localStorage + Redux) → `setupSessionDataForUser` (`commonHelper.js:1039-1068`:
   `buyerId`, `getDealPartner()`, PostHog user type, GA4 `login`).
2. `isAdminUser` → `handleLoggedInNavigation(userType, navigate, true)`; `isSellerUser()` → the same with `false`.
   Neither applies on `/buyer/login` for a buyer account.
3. Otherwise `fetchBuyerStatus` → `handleStatusApiCB`: `onboardingStage === 1` → `/buyer/onboarding`;
   `data.status === 'not_verified'` → previous `/buyer/sharedcard` path or `/buyer/profile`;
   status not `verified` and previous path not `/buyer/cuecardlisting` → `/buyer/profile`;
   else fall through to `handleLoggedInNavigation`.
4. `handleLoggedInNavigation` (`commonHelper.js:994-1037`) restores `commonStore.previousPath` when it is in the
   per-userType allow-list (`RouteConstants.js:53`) or contains one of the additional buyer paths; otherwise
   `reRouteUser` (`Services/index.js:18-35`) → verified buyer: `/buyer/recommendations` desktop,
   `/buyer/browse` at <=1180px; unverified: `/buyer/profile`.
5. `previousPath` is the **in-app** previous location (`pathname + search`), written on route change and never for
   a path containing `/login` or `/onboarding` (`HomeLayoutContainer/index.js:86-91`). A directly opened
   `/buyer/login` (new tab, or `page.goto`) has `previousPath = ''`, so tests that want the
   "return to where I was" behaviour must navigate **within the app** to the login screen, not `goto` it.

**Proposed `.env` variables** (none of these exist yet in `automation/.env.example`)
```
DD_BUYER_LOGIN_EMAIL=            # registered QA buyer, email+OTP login
DD_BUYER_LOGIN_OTP=              # the fixed OTP QA accepts for test accounts
DD_BUYER_LOGIN_UNREGISTERED_EMAIL=   # never registered; the not_registered branch
```
An unregistered address can also be generated per run (`dd.automation.unknown<ts>@example.com` was used in the
walk and returned `not_registered` cleanly), which keeps the negative case from depending on data staying absent.

## Data cost and sequencing

- **Reads only, with two side effects.** Nothing in this module creates a company, deal or upload.
- **Every step-1 submit of a registered email sends a real passcode** (email, and SMS when the account has a
  mobile). Keep the count low and prefer one passcode per test session; `BUY-LGN-30` (resend) adds a second.
- **A successful login creates a device/session for that account** on the backend (the login response carries
  `sessionID`, and the out-of-scope `DEVICE_SESSION_ALREADY_ACTIVE` code exists precisely because concurrent
  sessions are tracked). Two suites logging the same buyer in at once may evict each other, and a test that
  logs in should be expected to invalidate a previously saved `auth/buyer.json`. Log in serially, and re-save
  the buyer session (`python scripts/save_auth_state.py buyer`) after a run that ends logged in.
- **Wrong-OTP tests are the only lock risk.** `BUY-LGN-28` submits a knowingly bad code. Any lockout policy is
  backend-side and unverified (open question 2), so: at most one deliberate wrong-code attempt per run, and
  prefer proving the branch by **rewriting the `POST user` response** rather than sending a real bad code.
- **Fully rewritable, no data needed:** `BUY-LGN-17, 18, 19, 22, 32, 42, 43, 44, 48` — rewrite
  `user/emailCheck`, `user/send/passcode`, `user`, or `buyer/status`, or seed the persisted Redux state. These
  need no QA account at all and are the cheapest way to cover the error matrix.
- **No API calls at all:** `BUY-LGN-01…11, 52, 56`. A fresh context on `/buyer/login` covers them; run them first.
- **Order:** (1) copy/validation on a fresh context; (2) the unregistered branch; (3) the passcode step with the
  real test email; (4) rewritten failure branches; (5) exactly one real successful login, last, since it changes
  the browser context's storage and the account's session state.
- **No role has to act first.** The only prerequisite is that `DD_BUYER_LOGIN_EMAIL` is a registered, and ideally
  verified, buyer — the verified/unverified landing split (`BUY-LGN-40` vs `42`) otherwise needs two accounts or
  a rewritten `buyer/status`.
- **Manual only:** `BUY-LGN-53, 54` (PostHog/GA4 delivery). The passcode email/SMS itself is deliberately not
  asserted — this suite does not test mailboxes, which is why the fixed QA OTP matters.

## Suspected bugs and oddities

1. **An empty OTP is reported as an incorrect one.** Submitting step 2 with the field empty sets
   `otp.error = true` while the helper text is still `INCORRECT_OTP_HELPER`, so the buyer reads "The OTP you
   entered is incorrect. Please try again." for a code they never entered
   (`NewLoginContainer/index.js:230-236`, `:44-49`).
2. **The OTP error never clears while typing.** `updatePascode` tests `formFieldData.error` — a property of the
   whole form object, which is never set — instead of `formFieldData[key].error`, so the reset branch is dead and
   the error state and message stay on screen as the buyer retypes the code
   (`NewLoginContainer/index.js:140-148`). The email field does this correctly (`:150-159`).
3. **A transport failure calls the callback twice.** `commonPostData` swallows the rejection and returns
   `undefined` (`Redux/saga/Common/index.js:9-18`), so the saga calls `callback(undefined)`; `res.status` then
   throws inside the saga's `try`, and the `catch` calls the same callback again with
   `{status: false, message: 'Something went bad!!'}` (`Redux/saga/Login/index.js:14-27,53-72`). The UI recovers,
   but every such failure runs the handler twice — visible as duplicate error/snackbar work.
4. **`handleStatusApiCB` reads `onboardingStage` at the wrong depth.** It tests
   `statusApiResponse?.onboardingStage` (`NewLoginContainer/index.js:315`) on the response **body**, while the
   same value is read from `data.data` everywhere else (`Redux/saga/BuyerVerification/index.js:17`;
   `NonProtectedRoutes/index.js:19-22`). If `buyer/status` nests it under `data`, this "send a stage-1 buyer to
   onboarding" branch never fires after login, and such a buyer is routed by the status/verified checks instead.
   Unverified: `buyer/status` answered HTTP 502 during the walk.
5. **`buyer/status` and `buyer/getBuyer` returned HTTP 502 (nginx HTML) on QA during this mapping** (2026-09-23,
   two runs a few minutes apart; `getBuyer` had answered 200 shortly before). Since the 502 body resolves as a
   string, `statusApiResponse?.status` is `undefined` and the post-login redirect silently falls through to
   `handleLoggedInNavigation`. Any redirect test will be flaky while QA is in this state.
6. **The saved-profile path is dead code that is still wired up.** The only reader of `SAVED_PROFILE_KEY` is
   commented out (`NewLoginContainer/index.js:110-125`), so `isSavedLoginInfo` can never become true and
   `SavedProfileLogin`, `handleOneTapLogin`, `registerDeviceToken` and the `DEVICE_*` handling are unreachable
   from this screen — while `handleVerfyPasscodeCB` still deletes the saved profile on every login (`:250-254`).
7. **Buyer/admin behaviour is decided by `window.location.pathname` string comparisons**, not by the
   `isAdminUser` prop that is already passed in (`:213,362`; `BuyerLogin/index.js:103`). Any future route alias
   (a trailing slash, a redirect, an embed) silently flips `userType` to 2 and the not-registered branch off.
8. **`renderSections()` is called for its return value and discarded** inside `fetchPasscodeResponse`
   (`:133`) — a no-op left over from an earlier shape of the component.
9. **Two different code paths request the passcode.** The link-prefill path calls `api.post` directly
   (`:127-138`) while the normal path dispatches the `getPasscode` saga (`:371`); only the saga stores
   `passcodeSuccessData`, so the auto-advance in BUY-LGN-49 is reachable from one path and not the other.
10. **The Google button is inert on QA** (no `REACT_APP_GOOGLE_CLIENT_ID`): the decoy renders and the real GIS
    button never mounts, so a click does nothing. Out of scope here, but it means a "Google sign-in" test would
    silently pass a no-op on this environment.

## Open questions

1. **(blocking)** Which QA buyer account and which fixed OTP should `DD_BUYER_LOGIN_EMAIL` /
   `DD_BUYER_LOGIN_OTP` hold, and is that account **verified** (landing on `/buyer/recommendations`) or
   unverified (`/buyer/profile`)? BUY-LGN-40 vs BUY-LGN-42 need to know which one is the real path, and the other
   then has to be covered by rewriting `buyer/status`.
2. **(blocking)** Is there a wrong-passcode lockout or throttle on the backend, and how many attempts does it
   take? BUY-LGN-28 and the resend tests are written to avoid it, but if a limit exists the real-code negative
   test must be dropped in favour of a rewritten response.
3. **(deferrable)** Does a successful login invalidate an existing session for the same buyer (the
   `DEVICE_SESSION_ALREADY_ACTIVE` code suggests concurrent sessions are policed)? This decides whether the
   login tests can run alongside other suites that use `auth/buyer.json`.
4. **(deferrable)** Is `buyer/status`'s 502 a transient QA outage or a standing breakage? It changes how the
   post-login redirect requirements are marked.
5. **(deferrable)** Does `buyer/status` return `onboardingStage` at the body root or under `data`? That settles
   suspected bug 4 without a code change.
6. **(deferrable)** Should the `/buyer/sharedcard` redirect branch (BUY-LGN-43) stay in this module or move to a
   shared-card module when one is mapped? The code lives here; the destination does not.

## Traceability

Tests: `test_cases/buyer_test_cases/test_buyer_login.py` (42 collected, 38 functions).
Page object: `pages/buyer_module/buyer_login_page.py` · Selectors: `locators/buyer/login_locators.py` ·
Copy and keys: `constants.py` (`BuyerLoginCopy`, the localStorage keys, the landing paths) ·
Mocks and bodies: `utils/network.py` (`api_route`, `mock_json_sequence`, `passcode_success`,
`passcode_not_registered`, `email_check_body`, `login_success`, `buyer_status_body`, `failure_body`).
Logged-out fixture: `conftest.logged_out_page` → `utils.sessions.new_anonymous_page` (a fresh context
per test; `auth/*.json` is never read or written).

| ID | Test | Data |
|---|---|---|
| BUY-LGN-01 | `test_login_screen_renders_step_one` (smoke) | none |
| BUY-LGN-02 | `test_login_screen_renders_step_one` | none |
| BUY-LGN-03 | `test_step_one_labels_the_field_and_the_cta` | none |
| BUY-LGN-04 | `test_login_screen_renders_step_one` | none |
| BUY-LGN-05 | `test_step_one_labels_the_field_and_the_cta` | none |
| BUY-LGN-06 | `test_signup_link_points_at_buyer_onboarding` | none |
| BUY-LGN-07 | `test_empty_email_shows_the_helper_and_sends_nothing` | none |
| BUY-LGN-08 | `test_empty_email_shows_the_helper_and_sends_nothing` | none |
| BUY-LGN-09 | `test_malformed_email_stays_on_step_one_without_a_request` (3 cases) | none |
| BUY-LGN-10 | `test_malformed_email_stays_on_step_one_without_a_request` | none |
| BUY-LGN-11 | `test_typing_clears_the_email_error` | none |
| BUY-LGN-12 | `test_passcode_request_carries_the_email_and_buyer_user_type`; also live in `test_live_buyer_login_lands_on_a_buyer_screen` | rewritten passcode response |
| BUY-LGN-13 | `test_passcode_request_carries_the_email_and_buyer_user_type` | rewritten |
| BUY-LGN-14 | `test_passcode_request_trims_the_email` | rewritten |
| BUY-LGN-15 | `test_unregistered_email_is_refused_and_then_email_checked` | **real backend**, `DD_BUYER_LOGIN_UNREGISTERED_EMAIL` or a generated address |
| BUY-LGN-16 | `test_email_check_false_asks_for_a_professional_email` | rewritten passcode + emailCheck |
| BUY-LGN-17 | `test_email_check_true_goes_to_onboarding_with_the_query` | rewritten |
| BUY-LGN-18 | `test_failing_email_check_shows_something_went_bad` | rewritten |
| BUY-LGN-19 | `test_other_passcode_failures_show_the_backend_message` | rewritten |
| BUY-LGN-20 | `test_passcode_success_opens_the_code_step` (smoke); also live | rewritten |
| BUY-LGN-21 | `test_passcode_success_opens_the_code_step` | rewritten |
| BUY-LGN-22 | `test_code_step_names_the_mobile_when_the_response_carries_one` | rewritten (`mobile: "9876543210"`) |
| BUY-LGN-23 | `test_passcode_success_opens_the_code_step` | rewritten (`mobile: null`) |
| BUY-LGN-24 | `test_passcode_success_opens_the_code_step` | rewritten |
| BUY-LGN-25 | `test_passcode_success_opens_the_code_step` | rewritten |
| BUY-LGN-26 | `test_empty_code_blocks_the_login_request` — **partial**: the error state and the absent request only, not the copy (bug 1) | rewritten |
| BUY-LGN-27 | `test_code_submit_posts_the_login_payload`; also live | rewritten `user` |
| BUY-LGN-28 | `test_rejected_code_keeps_the_code_step_and_shows_the_message` — rewritten failure, never a real wrong passcode (open question 2) | rewritten `user` |
| BUY-LGN-29 | `test_edit_email_returns_to_step_one_keeping_the_email` | rewritten |
| BUY-LGN-30 | `test_resend_posts_again_with_resend_true` | rewritten |
| BUY-LGN-31 | `test_resend_posts_again_with_resend_true` | rewritten |
| BUY-LGN-32 | `test_failed_resend_shows_try_again_later` | rewritten (2nd call fails) |
| BUY-LGN-33 | `test_successful_resend_after_a_rejected_code_clears_the_field` | rewritten |
| BUY-LGN-34 | `test_successful_login_writes_the_session`; also live | rewritten `user` + `buyer/status` |
| BUY-LGN-35 | `test_successful_login_writes_the_session` (the key is seeded first, so removal is a real check) | rewritten |
| BUY-LGN-36 | `test_successful_login_writes_the_session` | rewritten |
| BUY-LGN-37 | `test_successful_login_writes_the_session` | rewritten |
| BUY-LGN-38 | `test_successful_login_writes_the_session` (read from the persisted store) | rewritten |
| BUY-LGN-39 | `test_buyer_status_is_requested_before_the_redirect`; also live | rewritten |
| BUY-LGN-40 | `test_verified_buyer_lands_on_recommendations` | rewritten `buyer/status` = verified |
| BUY-LGN-41 | `test_verified_buyer_lands_on_browse_on_a_small_screen` (390×844) | rewritten |
| BUY-LGN-42 | `test_buyer_without_verification_lands_on_profile[not_verified]` | rewritten `buyer/status` |
| BUY-LGN-43 | `test_not_verified_buyer_returns_to_a_shared_card_path` | rewritten + seeded `previousPath` |
| BUY-LGN-44 | `test_buyer_without_verification_lands_on_profile[pending]` | rewritten |
| BUY-LGN-45 | `test_bounced_buyer_returns_to_the_route_that_bounced_them` (`/buyer/categories/<uid>`, a real ProtectedRoute bounce) | rewritten |
| BUY-LGN-46 | `test_a_bounced_profile_path_is_ignored` | rewritten |
| BUY-LGN-47 | `test_a_live_session_never_sees_the_login_form` | seeded session (no real login) |
| BUY-LGN-48 | `test_a_live_session_mid_onboarding_goes_to_onboarding` (no stage / stage 1) | seeded session |
| BUY-LGN-49 | `test_a_requested_passcode_reopens_the_code_step` | rewritten |
| BUY-LGN-50 | `test_sign_up_here_clears_the_stored_passcode_state` | rewritten |
| BUY-LGN-51 | `test_listing_uid_prefills_the_email_and_opens_the_code_step` | rewritten `buyer/linkInfo` (no real uid) |
| BUY-LGN-52 | `test_plain_login_makes_no_link_info_call` | none |
| BUY-LGN-53 | **manual** (PostHog delivery) | — |
| BUY-LGN-54 | **manual** (PostHog + GA4 delivery) | — |
| BUY-LGN-55 | **not automated, by policy** (see below) | — |
| BUY-LGN-56 | `test_qa_has_no_viewport_guard_and_no_blur` | none |

**Cost of a full run:** one real `user/send/passcode` call for an *unknown* address (BUY-LGN-15, no
passcode can be delivered), plus — only when `DD_BUYER_LOGIN_EMAIL` and `DD_BUYER_LOGIN_OTP` are set —
one real passcode and one real login in `test_live_buyer_login_lands_on_a_buyer_screen`
(marker `live_login`). **That login creates a device session for the QA buyer and can evict a saved
`auth/buyer.json`: run it last and then re-run `python scripts/save_auth_state.py buyer`.** Everything
else is answered inside the browser. Run order: `pytest test_cases/buyer_test_cases/test_buyer_login.py
-m "not live_login"`, then `pytest -m live_login`.

**BUY-LGN-55 is deliberately not automated.** Its acceptance criterion needs an element whose
attributes contain "claude" to be injected into a `/buyer/*` page; `useClaudeElementDetector` then
clears localStorage and sessionStorage and hard-navigates. The suite must never do that on a buyer
page, so the requirement stays a manual check and no test asserts it (it is the one requirement
`python -m impact.coverage --gaps` still lists for this module).

**Not asserted, because a test would lock a suspected bug in** (module.md "Suspected bugs and
oddities" 1, 2, 3, 8):

| Bug | What is covered instead |
|---|---|
| 1 — an empty passcode is reported as an incorrect one | BUY-LGN-26 asserts the field's error state and that no `POST user` is sent; the helper's wording is read but never compared. |
| 2 — the passcode error never clears while retyping (`formFieldData.error` instead of `formFieldData[key].error`) | Nothing asserts the passcode error either clearing or persisting. BUY-LGN-11 covers the email field, which resets correctly. |
| 3 — a transport failure calls the callback twice | No test forces a transport failure; every failure branch is proven with a rewritten *body* instead (which is also how the app reads failures). |
| 8 — `renderSections()` called for its discarded return value | No test depends on it; BUY-LGN-51 (the link-prefill path it sits on) asserts only the resulting step 2. |

Two more oddities the tests work around rather than assert: `handleVerfyPasscodeCB` shows the
incorrect-code message only when the backend sends a `message` (so `SOMETHING_WENT_BAD` is unreachable
for BUY-LGN-28 — the test supplies a message), and the link-prefill path stores the whole response
body as `passcodeResponse`, so a `mobile` can never render on that path (BUY-LGN-22 is covered on the
normal path only).
