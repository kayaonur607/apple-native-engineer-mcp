# `/apple-native-metadata` — App Store Metadata Assistant

Drafts, checks, and validates App Store listing copy against character limits and search optimization rules.

---

## Agent Execution Steps

1. **Draft Listing Copy**:
   Use `templates/metadata/app_metadata_template.json` to structure localized metadata (Name, Subtitle, Description, Keywords, What's New).

2. **Automated Validation**:
   Run the metadata validator:
   ```bash
   ./tools/metadata-validator/validate_metadata.py /path/to/metadata.json
   ```

3. **Keyword Optimization**:
   - Verify keywords do not exceed 100 characters.
   - Remove redundant keywords already present in the app name.
   - Eliminate prohibited superlatives ("best app", "#1", "top rated").

4. **Mandatory URLs**:
   Ensure valid `privacyPolicyUrl` and `supportUrl` are specified.
