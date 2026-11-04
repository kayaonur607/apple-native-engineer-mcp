# App Store Metadata Validator Tool

Validates App Store metadata against official Apple App Store Connect specifications:
- **Character Limits**: Name (30), Subtitle (30), Description (4000), Keywords (100), Promotional Text (170), What's New (4000).
- **Mandatory URLs**: Validates `privacyPolicyUrl` (Guideline 5.1.1) and `supportUrl`.
- **Keyword Optimization**: Detects duplicate keywords and keywords redundantly repeated in the app title.
- **Review Sensitivity**: Flags unsubstantiated marketing superlatives ("best app", "#1", "top rated").

---

## Usage

```bash
# Validate metadata template or project metadata JSON
./tools/metadata-validator/validate_metadata.py templates/metadata/app_metadata_template.json

# Output in JSON format for automated CI or MCP tools
./tools/metadata-validator/validate_metadata.py templates/metadata/app_metadata_template.json --json
```
