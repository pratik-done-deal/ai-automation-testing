"""Selectors for /buyer/login: the email step and the passcode step (module buyer-login).

Traps this screen sets, all confirmed in the JSX:
  * both fields are MUI TextFields (CommonComponent/NewTextField) with generated ids (`:r2:`) and no
    name, aria-label or <label for>, so they are reached by placeholder;
  * both steps share ONE <button type="submit"> whose label changes ("Verify" -> "Verify & Login"),
    inside one <form onSubmit>, and it is never disabled;
  * the resend affordance is a <span onClick> (BuyerLogin/index.js:70-74), not a button;
  * the edit-email affordance is a bare <svg> in a <span onClick> with no accessible name
    (NewAuthOtpFlow/index.js:65-68), so it is located inside the sentence that names the email;
  * "Continue with Google" is an aria-hidden, pointer-events-none decoy over the real GIS iframe
    (GoogleSignInButton/index.js:261-268) - it is never the target of a click here.
"""

LOGIN_FORM = "form"
EMAIL_STEP = ".login-form-field-container"
FIELD_LABEL = ".onboarding-field-label"

EMAIL_INPUT = "input[placeholder='Enter your work email']"
OTP_INPUT = "input[placeholder='Enter 6-digit code']"

# MUI renders helper text only while the field is in the error state, and the two steps never
# show a field at the same time, so one helper locator serves both.
HELPER_TEXT = "p.MuiFormHelperText-root"
FIELD_IN_ERROR = ".MuiOutlinedInput-root.Mui-error"

SUBMIT_BUTTON = "form button[type='submit']"
SIGNUP_LINK = "a[href='/buyer/onboarding']"

# Step 2: "We've sent a 6-digit code to <email> . Enter it below to verify and continue securely."
# `.last` of this selector is the sentence itself (ancestors match the text too).
CODE_SENT_SENTENCE = 'div:has-text("Enter it below to verify and continue securely.")'
EDIT_EMAIL_ICON = "span.cursor-pointer:has(svg)"
RESEND_LINK = "span.cursor-pointer.underline"

# BuyerRouteStructure wraps the shell in <div style="filter: ..."> for useBlurOnFocusLoss.
BLUR_WRAPPER = 'div[style*="filter"]'
