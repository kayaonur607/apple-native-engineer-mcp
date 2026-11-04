// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "CleanApp",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(name: "CleanApp", targets: ["CleanApp"])
    ],
    targets: [
        .target(name: "CleanApp", path: "App"),
        .testTarget(name: "CleanAppTests", dependencies: ["CleanApp"], path: "Tests")
    ]
)
