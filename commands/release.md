# `/apple-native-release` — Pre-Submission Release Readiness

Executes final quality gates and generates a publication-ready release report before submitting to App Store Review.

---

## Agent Execution Steps

1. **Run Full Quality Gate**:
   Execute the release readiness generator:
   ```bash
   ./tools/release-readiness/generate_report.py . --output RELEASE_REPORT.md
   ```

2. **Verify Critical Gates**:
   - Icon: 1024x1024, no alpha transparency.
   - Privacy: `PrivacyInfo.xcprivacy` present and all Required-Reason APIs declared.
   - Metadata: Name <= 30, Subtitle <= 30, Keywords <= 100, active Privacy Policy URL.
   - Review Notes: Active test demo credentials provided for App Store Review team.

3. **Present Readiness Score**:
   Report overall readiness score (0-100) and highlight any blocking critical issues.
