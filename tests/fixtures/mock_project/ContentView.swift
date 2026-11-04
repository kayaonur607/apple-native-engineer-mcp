import SwiftUI

public struct ContentView: View {
    public init() {}
    
    public var body: some View {
        VStack {
            Text("Hello, World!")
                .font(.headline)
            Button("Action") {
                UserDefaults.standard.set(true, forKey: "hasLaunched")
            }
            .buttonStyle(.borderedProminent)
            .frame(minHeight: 44)
        }
        .padding()
    }
}
