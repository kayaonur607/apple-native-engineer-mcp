import AVFoundation
import WebKit

// Deliberately risky patterns: this file exists so the App Store review engine
// has something to find. Every construct below maps to a guideline section.

final class RiskyFeatures: NSObject {
    func captureSession() {
        let session = AVCaptureSession()
        session.startRunning()
    }

    func loadWeb(_ url: URL) {
        let webView = WKWebView()
        webView.load(URLRequest(url: url))
    }

    func createAccount() {
        // TODO: replace this placeholder before shipping
        let banner = "Coming soon"
        print(banner)
    }

    let checkoutURL = "https://stripe.com/pay"

    func callPrivate(_ target: NSObject) {
        _ = target.performSelector(NSSelectorFromString("privateThing"))
    }
}
