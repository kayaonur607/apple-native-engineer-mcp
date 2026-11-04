import SwiftUI

// Imitates Liquid Glass with stacked materials and a manual blur. On iOS 26 this
// looks wrong next to real glass and costs an extra offscreen pass per frame.

struct LegacyGlassCard<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(16)
            .background(.ultraThinMaterial)
            .blur(radius: 12)
            .glassEffect()
    }
}
