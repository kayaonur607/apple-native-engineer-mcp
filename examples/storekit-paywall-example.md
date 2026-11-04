# StoreKit 2 Custom Subscription Paywall Example

This example demonstrates an App-Store-compliant subscription paywall using StoreKit 2, complete with subscription tiers, pricing display, terms/privacy policy links, and purchase restoration.

```swift
import SwiftUI
import StoreKit

// MARK: - Paywall View
struct ProUpgradePaywallView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var selectedProduct: Product?
    @State private var availableProducts: [Product] = []
    @State private var isLoading = true
    @State private var errorMessage: String?

    // Group ID configured in App Store Connect
    let subscriptionGroupID = "21405928"
    let productIdentifiers = [
        "com.example.app.pro.annual",
        "com.example.app.pro.monthly"
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // 1. Hero Graphic
                    VStack(spacing: 12) {
                        Image(systemName: "crown.fill")
                            .font(.system(size: 56))
                            .foregroundStyle(.yellow.gradient)
                            .shadow(color: .orange.opacity(0.4), radius: 10, y: 5)

                        Text("Upgrade to Pro")
                            .font(.largeTitle.bold())

                        Text("Unlock all native design tools, unlimited exports, and CloudKit sync.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }
                    .padding(.top, 24)

                    // 2. Feature Comparison List
                    VStack(alignment: .leading, spacing: 14) {
                        FeatureRow(icon: "sparkles", title: "Liquid Glass Materials", subtitle: "Access Metal-backed optical shaders")
                        FeatureRow(icon: "icloud.fill", title: "iCloud Sync", subtitle: "Instant multi-device continuous sync")
                        FeatureRow(icon: "shield.lefthalf.filled", title: "Privacy Manifest Auditor", subtitle: "Automated pre-submission validation")
                        FeatureRow(icon: "bolt.fill", title: "Priority Support", subtitle: "Direct responses from developer team")
                    }
                    .padding(20)
                    .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .padding(.horizontal)

                    // 3. Subscription Options
                    if isLoading {
                        ProgressView()
                            .padding()
                    } else if let error = errorMessage {
                        Text(error)
                            .font(.footnote)
                            .foregroundStyle(.red)
                    } else {
                        VStack(spacing: 12) {
                            ForEach(availableProducts) { product in
                                ProductTierCard(
                                    product: product,
                                    isSelected: selectedProduct?.id == product.id
                                ) {
                                    selectedProduct = product
                                }
                            }
                        }
                        .padding(.horizontal)
                    }

                    // 4. Purchase Action Button
                    Button {
                        if let product = selectedProduct {
                            Task { await purchase(product: product) }
                        }
                    } label: {
                        Text("Continue")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .frame(height: 52)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(selectedProduct == nil)
                    .padding(.horizontal)

                    // 5. App Store Compliance Disclosures & Links
                    VStack(spacing: 8) {
                        Button("Restore Purchases") {
                            Task {
                                try? await AppStore.sync()
                            }
                        }
                        .font(.footnote)
                        .foregroundStyle(.secondary)

                        HStack(spacing: 16) {
                            Link("Terms of Use (EULA)", destination: URL(string: "https://example.com/terms")!)
                            Text("•")
                                .foregroundStyle(.secondary)
                            Link("Privacy Policy", destination: URL(string: "https://example.com/privacy")!)
                        }
                        .font(.caption2)
                        .foregroundStyle(.secondary)

                        Text("Subscriptions automatically renew unless auto-renew is turned off at least 24 hours before the end of the current billing cycle.")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 24)
                    }
                    .padding(.bottom, 24)
                }
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
            .task {
                await loadProducts()
            }
        }
    }

    private func loadProducts() async {
        do {
            let products = try await Product.products(for: productIdentifiers)
            self.availableProducts = products.sorted { $0.price > $1.price }
            self.selectedProduct = self.availableProducts.first
            self.isLoading = false
        } catch {
            self.errorMessage = "Failed to load products: \(error.localizedDescription)"
            self.isLoading = false
        }
    }

    private func purchase(product: Product) async {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                if case .verified(let transaction) = verification {
                    await transaction.finish()
                    dismiss()
                }
            case .userCancelled:
                break
            case .pending:
                break
            @unknown default:
                break
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Supporting Row Subviews
struct FeatureRow: View {
    let icon: String
    let title: String
    let subtitle: String

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(.blue)
                .frame(width: 28)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.subheadline.bold())
                Text(subtitle).font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}

struct ProductTierCard: View {
    let product: Product
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(product.displayName)
                        .font(.headline)
                    Text(product.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text(product.displayPrice)
                    .font(.title3.bold())
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(isSelected ? Color.blue : Color.gray.opacity(0.3), lineWidth: isSelected ? 2 : 1)
                    .background(isSelected ? Color.blue.opacity(0.05) : Color.clear)
            )
        }
        .buttonStyle(.plain)
    }
}
```
