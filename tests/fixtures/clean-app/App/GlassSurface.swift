import SwiftUI

/// Liquid Glass, adopted the way Apple documents it: only on the OS versions that
/// ship the material, with a material fallback that keeps the same layout on
/// everything older.
///
/// This file is compiled only when the SDK provides the iOS 26 glass APIs; the
/// verification script skips it on older toolchains and says so.
struct GlassDemoView: View {
    var body: some View {
        if #available(iOS 26.0, macOS 26.0, *) {
            Text("Liquid Glass")
                .padding(DesignTokens.Spacing.md)
                .glassEffect(.regular, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        } else {
            Text("Liquid Glass")
                .padding(DesignTokens.Spacing.md)
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        }
    }
}

#Preview {
    GlassDemoView()
}
