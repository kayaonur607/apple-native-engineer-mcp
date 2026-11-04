# `/apple-native-icon` — Professional App Icon Creation & Asset Cataloging

Guides the creation, validation, and Xcode asset cataloging of production-grade 1024x1024 app icons.

---

## Agent Execution Steps

1. **Brand Identity & Concepts**:
   - Inspect the application's core functionality, audience, and color palette.
   - Formulate 3 distinct conceptual directions (e.g., Symbolic Glyph, Layered Depth, Minimal Monogram).

2. **Creation / Generation**:
   - Use an available image-generation tool or asset file provided by the user.

3. **Technical Validation**:
   Run the asset validator to ensure exact 1024x1024 dimensions and zero alpha channel transparency:
   ```bash
   ./tools/asset-validator/validate_assets.py --icon /path/to/icon.png
   ```

4. **Asset Catalog Integration**:
   Prepare an Xcode-ready asset catalog using the template in `templates/app-icon/Contents.json`:
   ```bash
   mkdir -p Assets.xcassets/AppIcon.appiconset
   cp templates/app-icon/Contents.json Assets.xcassets/AppIcon.appiconset/
   cp /path/to/icon.png Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png
   ```
