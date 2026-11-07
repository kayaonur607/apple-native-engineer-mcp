// native_render.swift — macOS-native rasteriser for the screenshot studio.
//
// Draws with CoreGraphics, AppKit text (the system San Francisco font with its
// optical sizes, real kerning and line breaking for every script) and ImageIO.
// Output is always an opaque RGB PNG at the exact pixel size requested, which
// is what App Store Connect accepts (no alpha channel).
//
// Commands:
//   native_render render <layouts.json>     draw every layout in the array
//   native_render flatten <png> [<png> …]   rewrite captures as opaque RGB
//
// The layout format is produced by compose_marketing.py; coordinates are
// pixels with a top-left origin. Results are printed as one JSON object.

import AppKit
import Foundation
import ImageIO
import UniformTypeIdentifiers

struct Failure: Error, CustomStringConvertible { let description: String }

func color(_ hex: String, _ alpha: CGFloat = 1) -> CGColor {
    var value: UInt64 = 0
    Scanner(string: hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))).scanHexInt64(&value)
    return CGColor(srgbRed: CGFloat((value >> 16) & 0xFF) / 255, green: CGFloat((value >> 8) & 0xFF) / 255,
                   blue: CGFloat(value & 0xFF) / 255, alpha: alpha)
}

func number(_ any: Any?, _ fallback: CGFloat = 0) -> CGFloat {
    if let value = any as? NSNumber { return CGFloat(truncating: value) }
    return fallback
}

func rect(_ dict: [String: Any]) -> CGRect {
    CGRect(x: number(dict["x"]), y: number(dict["y"]), width: number(dict["width"]), height: number(dict["height"]))
}

func opaqueContext(width: Int, height: Int, space: CGColorSpace) throws -> CGContext {
    guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                                  space: space, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue) else {
        throw Failure(description: "cannot create a \(width)x\(height) bitmap context")
    }
    context.interpolationQuality = .high
    context.setShouldAntialias(true)
    return context
}

func writePNG(_ context: CGContext, to path: String) throws {
    guard let image = context.makeImage(),
          let destination = CGImageDestinationCreateWithURL(URL(fileURLWithPath: path) as CFURL,
                                                            UTType.png.identifier as CFString, 1, nil) else {
        throw Failure(description: "cannot write \(path)")
    }
    CGImageDestinationAddImage(destination, image, nil)
    guard CGImageDestinationFinalize(destination) else { throw Failure(description: "cannot finalise \(path)") }
}

func loadImage(_ path: String) throws -> CGImage {
    guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        throw Failure(description: "cannot read image \(path)")
    }
    return image
}

func fontWeight(_ name: String?) -> NSFont.Weight {
    switch name {
    case "heavy": return .heavy
    case "bold": return .bold
    case "semibold": return .semibold
    case "medium": return .medium
    default: return .regular
    }
}

struct PreparedText {
    let text: String
    let attributes: [NSAttributedString.Key: Any]
    let size: CGFloat
    let height: CGFloat
    let fits: Bool
}

/// Measures text in `width`, shrinking from `size` toward `minSize` until it fits `maxHeight`.
func prepareText(_ spec: [String: Any], width: CGFloat, maxHeight: CGFloat) -> PreparedText {
    let text = spec["text"] as? String ?? ""
    var size = number(spec["size"], 48)
    let minimum = number(spec["minSize"], size * 0.6)
    let rtl = spec["rtl"] as? Bool ?? false
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = { switch spec["align"] as? String {
        case "center": return .center
        case "right": return .right
        default: return rtl ? .right : .left } }()
    paragraph.baseWritingDirection = rtl ? .rightToLeft : .natural
    paragraph.lineBreakMode = .byWordWrapping
    paragraph.lineBreakStrategy = .standard
    var attributes: [NSAttributedString.Key: Any] = [:]
    var height: CGFloat = 0
    while true {
        let font = NSFont.systemFont(ofSize: size, weight: fontWeight(spec["weight"] as? String))
        paragraph.lineHeightMultiple = number(spec["lineHeight"], 1.0)
        attributes = [.font: font, .paragraphStyle: paragraph,
                      .foregroundColor: NSColor(cgColor: color(spec["color"] as? String ?? "#FFFFFF")) ?? .white,
                      .kern: number(spec["tracking"]) * size / 100]
        height = ceil((text as NSString).boundingRect(with: CGSize(width: width, height: .greatestFiniteMagnitude),
                                                      options: [.usesLineFragmentOrigin, .usesFontLeading],
                                                      attributes: attributes).height)
        if height <= maxHeight || size <= minimum { break }
        size = max(minimum, size - 2)
    }
    return PreparedText(text: text, attributes: attributes, size: size, height: height, fits: height <= maxHeight)
}

/// Stacks the texts in `block`, vertically centred, with `gap` between them.
func drawTextBlock(_ block: [String: Any], _ specs: [[String: Any]]) -> [[String: Any]] {
    let frame = rect(block), gap = number(block["gap"])
    let shares = specs.map { number($0["share"], 1.0 / CGFloat(max(specs.count, 1))) }
    var prepared: [PreparedText] = []
    for (index, spec) in specs.enumerated() {
        let budget = frame.height * shares[index] - (index > 0 ? gap : 0)
        prepared.append(prepareText(spec, width: frame.width, maxHeight: budget))
    }
    let total = prepared.reduce(0) { $0 + $1.height } + gap * CGFloat(max(prepared.count - 1, 0))
    var y = frame.minY + max(0, (frame.height - total) / 2)
    var results: [[String: Any]] = []
    for item in prepared where !item.text.isEmpty {
        (item.text as NSString).draw(with: CGRect(x: frame.minX, y: y, width: frame.width, height: item.height),
                                     options: [.usesLineFragmentOrigin, .usesFontLeading], attributes: item.attributes)
        y += item.height + gap
        results.append(["text": item.text, "size": Double(item.size), "height": Double(item.height), "fits": item.fits])
    }
    return results
}

/// Draws text into `frame`, shrinking from `size` toward `minSize` until it fits.
func drawText(_ spec: [String: Any]) -> [String: Any] {
    let text = spec["text"] as? String ?? ""
    let frame = rect(spec)
    var size = number(spec["size"], 48)
    let minimum = number(spec["minSize"], size * 0.6)
    let rtl = spec["rtl"] as? Bool ?? false
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = { switch spec["align"] as? String {
        case "center": return .center
        case "right": return .right
        default: return rtl ? .right : .left } }()
    paragraph.baseWritingDirection = rtl ? .rightToLeft : .natural
    paragraph.lineBreakMode = .byWordWrapping
    paragraph.lineBreakStrategy = .standard
    var attributes: [NSAttributedString.Key: Any] = [:]
    var bounds = CGRect.zero
    repeat {
        let font = NSFont.systemFont(ofSize: size, weight: fontWeight(spec["weight"] as? String))
        paragraph.lineHeightMultiple = number(spec["lineHeight"], 1.0)
        attributes = [.font: font, .paragraphStyle: paragraph,
                      .foregroundColor: NSColor(cgColor: color(spec["color"] as? String ?? "#FFFFFF")) ?? .white,
                      .kern: number(spec["tracking"]) * size / 100]
        bounds = (text as NSString).boundingRect(with: CGSize(width: frame.width, height: .greatestFiniteMagnitude),
                                                 options: [.usesLineFragmentOrigin, .usesFontLeading],
                                                 attributes: attributes)
        if bounds.height <= frame.height || size <= minimum { break }
        size = max(minimum, size - 2)
    } while true
    (text as NSString).draw(with: CGRect(x: frame.minX, y: frame.minY, width: frame.width, height: max(frame.height, bounds.height)),
                            options: [.usesLineFragmentOrigin, .usesFontLeading], attributes: attributes)
    return ["text": text, "size": Double(size), "height": Double(bounds.height), "fits": bounds.height <= frame.height]
}

func render(_ layout: [String: Any]) throws -> [String: Any] {
    let width = Int(number(layout["width"])), height = Int(number(layout["height"]))
    guard width > 0, height > 0, let output = layout["output"] as? String else {
        throw Failure(description: "layout needs width, height and output")
    }
    let space = CGColorSpace(name: CGColorSpace.sRGB)!
    let context = try opaqueContext(width: width, height: height, space: space)
    context.translateBy(x: 0, y: CGFloat(height))
    context.scaleBy(x: 1, y: -1)
    let graphics = NSGraphicsContext(cgContext: context, flipped: true)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = graphics
    defer { NSGraphicsContext.restoreGraphicsState() }

    let canvas = CGRect(x: 0, y: 0, width: width, height: height)
    let background = layout["background"] as? [String: Any] ?? [:]
    let from = color(background["from"] as? String ?? "#000000"), to = color(background["to"] as? String ?? "#000000")
    let gradient = CGGradient(colorsSpace: space, colors: [from, to] as CFArray, locations: [0, 1])!
    context.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: canvas.width, y: canvas.height), options: [])

    if let glow = layout["glow"] as? [String: Any] {
        let tint = glow["color"] as? String ?? "#0A84FF"
        let radial = CGGradient(colorsSpace: space, colors: [color(tint, number(glow["opacity"], 0.25)), color(tint, 0)] as CFArray,
                                locations: [0, 1])!
        let center = CGPoint(x: canvas.width * number(glow["x"], 0.2), y: canvas.height * number(glow["y"], 0.05))
        context.drawRadialGradient(radial, startCenter: center, startRadius: 0, endCenter: center,
                                   endRadius: max(canvas.width, canvas.height) * number(glow["radius"], 0.8), options: [])
    }

    var texts: [[String: Any]] = []
    if let block = layout["textBlock"] as? [String: Any] {
        texts = drawTextBlock(block, layout["texts"] as? [[String: Any]] ?? [])
    } else {
        for spec in layout["texts"] as? [[String: Any]] ?? [] { texts.append(drawText(spec)) }
    }

    if let shadow = layout["shadow"] as? [String: Any] {
        let box = rect(shadow)
        context.saveGState()
        context.setShadow(offset: CGSize(width: 0, height: number(shadow["offsetY"])), blur: number(shadow["blur"]),
                          color: color("#000000", number(shadow["opacity"], 0.35)))
        context.addPath(CGPath(roundedRect: box, cornerWidth: number(shadow["radius"]), cornerHeight: number(shadow["radius"]), transform: nil))
        context.setFillColor(color(shadow["fill"] as? String ?? "#000000"))
        context.fillPath()
        context.restoreGState()
    }

    if let device = layout["device"] as? [String: Any] {
        let body = rect(device), radius = number(device["radius"])
        context.addPath(CGPath(roundedRect: body, cornerWidth: radius, cornerHeight: radius, transform: nil))
        context.setFillColor(color(device["color"] as? String ?? "#1C1C1E"))
        context.fillPath()
        let rimWidth = number(device["rimWidth"], 4)
        let rim = body.insetBy(dx: rimWidth / 2, dy: rimWidth / 2)
        context.addPath(CGPath(roundedRect: rim, cornerWidth: radius - rimWidth / 2, cornerHeight: radius - rimWidth / 2, transform: nil))
        context.setStrokeColor(color(device["rim"] as? String ?? "#3A3A3C"))
        context.setLineWidth(rimWidth)
        context.strokePath()
    }

    if let image = layout["image"] as? [String: Any], let path = image["path"] as? String {
        let frame = rect(image), radius = number(image["radius"])
        let picture = try loadImage(path)
        let scale = max(frame.width / CGFloat(picture.width), frame.height / CGFloat(picture.height))
        let drawn = CGSize(width: CGFloat(picture.width) * scale, height: CGFloat(picture.height) * scale)
        context.saveGState()
        context.addPath(CGPath(roundedRect: frame, cornerWidth: radius, cornerHeight: radius, transform: nil))
        context.clip()
        // Top-aligned aspect fill: the status bar and title stay visible.
        let target = CGRect(x: frame.midX - drawn.width / 2, y: frame.minY, width: drawn.width, height: drawn.height)
        context.translateBy(x: 0, y: target.minY + target.maxY)
        context.scaleBy(x: 1, y: -1)
        context.draw(picture, in: target)
        context.restoreGState()
    }

    if let island = layout["island"] as? [String: Any] {
        let pill = rect(island)
        context.addPath(CGPath(roundedRect: pill, cornerWidth: pill.height / 2, cornerHeight: pill.height / 2, transform: nil))
        context.setFillColor(color("#000000"))
        context.fillPath()
    }

    try writePNG(context, to: output)
    return ["output": output, "width": width, "height": height, "texts": texts]
}

func flatten(_ path: String) throws -> [String: Any] {
    let image = try loadImage(path)
    let space = image.colorSpace.flatMap { $0.model == .rgb ? $0 : nil } ?? CGColorSpace(name: CGColorSpace.sRGB)!
    let context = try opaqueContext(width: image.width, height: image.height, space: space)
    context.setFillColor(color("#000000"))
    context.fill(CGRect(x: 0, y: 0, width: image.width, height: image.height))
    context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
    try writePNG(context, to: path)
    return ["output": path, "width": image.width, "height": image.height,
            "color_space": (space.name as String?) ?? "rgb"]
}

func emit(_ object: Any) {
    let data = (try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])) ?? Data("{}".utf8)
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data("\n".utf8))
}

let arguments = Array(CommandLine.arguments.dropFirst())
guard let command = arguments.first else {
    FileHandle.standardError.write(Data("usage: native_render render <layouts.json> | flatten <png>…\n".utf8))
    exit(64)
}
var results: [[String: Any]] = []
var errors: [String] = []
switch command {
case "render":
    guard arguments.count == 2, let data = FileManager.default.contents(atPath: arguments[1]),
          let layouts = (try? JSONSerialization.jsonObject(with: data)) as? [[String: Any]] else {
        emit(["ok": false, "errors": ["render expects one JSON file containing an array of layouts"]]); exit(2)
    }
    for layout in layouts {
        do { results.append(try render(layout)) } catch { errors.append("\(error)") }
    }
case "flatten":
    for path in arguments.dropFirst() {
        do { results.append(try flatten(path)) } catch { errors.append("\(error)") }
    }
default:
    emit(["ok": false, "errors": ["unknown command \(command)"]]); exit(64)
}
emit(["ok": errors.isEmpty, "results": results, "errors": errors])
exit(errors.isEmpty ? 0 : 2)
