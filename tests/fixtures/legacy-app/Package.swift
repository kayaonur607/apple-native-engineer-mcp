// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LegacyApp",
    platforms: [
        .iOS(.v16),
        .macOS(.v14)
    ],
    products: [
        .library(name: "LegacyApp", targets: ["LegacyApp"])
    ],
    targets: [
        .target(name: "LegacyApp", path: "App")
    ]
)
