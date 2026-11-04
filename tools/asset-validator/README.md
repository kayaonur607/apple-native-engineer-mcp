# Asset Validator Tool

Executable tool that inspects and validates App Store asset requirements:
- **App Icons**: Validates exact 1024x1024pt dimensions, PNG signature, and verifies that no alpha channel (transparency) exists.
- **App Store Screenshots**: Validates pixel dimensions against Apple's official display specifications (iPhone 6.9", 6.7", 6.5", iPad 13", iPad 12.9", Mac).

---

## Usage

```bash
# Validate an App Icon
./tools/asset-validator/validate_assets.py --icon /path/to/AppIcon-1024.png

# Validate an App Store Screenshot
./tools/asset-validator/validate_assets.py --screenshot /path/to/screen_6_7.png

# Output JSON for CI or MCP integration
./tools/asset-validator/validate_assets.py --icon /path/to/AppIcon-1024.png --json
```
