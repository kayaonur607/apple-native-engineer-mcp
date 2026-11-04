# `/apple-native` — Master Application Inspection & Refactoring

The master orchestration command that evaluates an existing Apple platform project across its complete lifecycle: architecture, design, privacy, and App Store readiness.

---

## Agent Execution Steps

1. **Workspace Inspection**:
   Run the project inspector tool to analyze project type, frameworks, and architecture:
   ```bash
   ./tools/project-inspector/inspect_project.py . --json
   ```

2. **Privacy & Security Audit**:
   Scan for Required-Reason APIs and verify `PrivacyInfo.xcprivacy`:
   ```bash
   ./tools/privacy-auditor/audit_privacy.py . --json
   ```

3. **Release Readiness Evaluation**:
   Generate an end-to-end readiness score and quality gate report:
   ```bash
   ./tools/release-readiness/generate_report.py .
   ```

4. **Interactive Alignment**:
   Present the findings to the developer, classified by severity (Critical, High, Medium, Low, Suggestion). Propose a prioritized remediation plan and ask for approval before modifying code.

5. **Implementation & Verification**:
   Apply approved native SwiftUI changes, verify dynamic type resilience, and run `./scripts/validate-skill.sh`.
