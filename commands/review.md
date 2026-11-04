# `/apple-native-review` — App Store Review Pre-Flight Audit

Conducts an exhaustive pre-submission review against all five sections of Apple's official App Store Review Guidelines.

---

## Agent Execution Steps

1. **Guideline 2.1 (App Completeness)**:
   - Check for crashes, placeholder text ("Lorem ipsum", "Test Product"), non-functional buttons, and broken URLs.

2. **Guideline 3.1.1 & 3.1.2 (Business & Subscriptions)**:
   - Verify digital goods use StoreKit 2.
   - Verify paywalls clearly disclose price, duration, terms of service, privacy policy, and cancellation instructions.

3. **Guideline 4.2 & 4.8 (Design & Social Login)**:
   - Verify the app is a rich native experience, not a wrapped responsive website.
   - Verify **Sign in with Apple** is offered with equal prominence if third-party logins exist.

4. **Guideline 5.1 (Legal & Privacy)**:
   - Confirm active Privacy Policy URL is present.
   - Verify in-app account deletion is supported if users can create an account (Guideline 5.1.1(v)).

5. **Generate Finding Report**:
   Format every finding using the standardized 7-part report format (Affected File, Guideline URL, Why It Matters, Severity, Fix, Code Example, Verification Method).
