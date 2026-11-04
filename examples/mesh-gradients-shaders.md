# iOS 18 MeshGradient & Metal Shader Effects

This example illustrates how to build dynamic Apple-style fluid visual effects using iOS 18 `MeshGradient` and SwiftUI Metal stitchable shaders.

```swift
import SwiftUI

// MARK: - 1. iOS 18 Dynamic Mesh Gradient Card
struct DynamicMeshHeroCard: View {
    @State private var phase: Float = 0.0

    var body: some View {
        ZStack {
            #if swift(>=6.0)
            if #available(iOS 18.0, macOS 15.0, *) {
                MeshGradient(
                    width: 3,
                    height: 3,
                    points: [
                        [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],
                        [0.0, 0.5], [0.5 + sin(phase) * 0.15, 0.5 + cos(phase) * 0.1], [1.0, 0.5],
                        [0.0, 1.0], [0.5, 1.0], [1.0, 1.0]
                    ],
                    colors: [
                        .purple, .indigo, .blue,
                        .cyan, .teal, .indigo,
                        .blue, .purple, .pink
                    ],
                    smoothsColors: true
                )
            } else {
                // Fallback for iOS 17
                LinearGradient(
                    colors: [.purple, .blue, .teal],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            }
            #else
            LinearGradient(
                colors: [.purple, .blue, .teal],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            #endif

            // Content Overlay with Material Frosting
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "wand.and.stars")
                        .font(.title2)
                        .foregroundStyle(.white)
                    Spacer()
                    Text("NEW")
                        .font(.caption2.bold())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(.ultraThinMaterial, in: Capsule())
                        .foregroundStyle(.white)
                }

                Spacer()

                Text("Apple Intelligence Ready")
                    .font(.title2.bold())
                    .foregroundStyle(.white)

                Text("Experience fluid real-time generative interfaces designed natively.")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.85))
            }
            .padding(24)
        }
        .frame(height: 240)
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        .shadow(color: .purple.opacity(0.3), radius: 20, x: 0, y: 10)
        .onAppear {
            withAnimation(.easeInOut(duration: 5.0).repeatForever(autoreverses: true)) {
                phase = .pi * 2
            }
        }
    }
}

// MARK: - 2. Metal Color Sheen Modifier
public extension View {
    func opticalSheen(time: Double, tint: Color = .white) -> some View {
        #if canImport(SwiftUI)
        if #available(iOS 17.0, macOS 14.0, *) {
            return self.colorEffect(
                ShaderLibrary.tintSheen(
                    .float(time),
                    .color(tint)
                )
            )
        }
        #endif
        return self
    }
}
```
