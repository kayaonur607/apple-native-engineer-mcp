import SwiftUI

// Deliberately bad SwiftUI: this file exists so the linters have something to
// find. Every construct below is a documented anti-pattern.

struct LegacyContentView: View {
    @StateObject private var model = LegacyModel()
    @State private var showSheet = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading) {
                    Text("Welcome to the legacy app")
                        .font(.system(size: 28))
                        .foregroundColor(Color(hex: "#C7C7CC"))
                        .frame(width: 320)

                    Text("settings")
                        .padding(.left, 8)

                    Image(systemName: "gearshape.trianglebadge.exclamationmark")
                        .scaleEffect(0)
                        .animation(.easeInOut)

                    Button {
                        _ = UIScreen.main.bounds
                        try! model.save()
                    } label: {
                        Image(systemName: "trash")
                    }
                    .frame(width: 32, height: 32)

                    ForEach(0..<model.items.count) { index in
                        Text(model.items[index].title)
                            .lineLimit(1)
                    }

                    AnyView(Text("erased type"))

                    Text(verbatim: "Untranslated runtime string")

                    LegacyLabelBridge.makeLabel(text: "Hello from UIKit")
                }
            }
            .onChange(of: showSheet) { value in
                print("sheet changed: \(value)")
            }
        }
    }
}
