// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MockApp",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "MockApp", targets: ["MockApp"])
    ],
    targets: [
        .target(name: "MockApp")
    ]
)
