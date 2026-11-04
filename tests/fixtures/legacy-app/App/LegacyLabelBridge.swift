import UIKit

// UIKit string properties take a plain String, so nothing localises them.
enum LegacyLabelBridge {
    static func makeLabel(text: String) -> UILabel {
        let label = UILabel()
        label.text = "Hardcoded UIKit text"
        label.placeholder = "Search"
        return label
    }
}
