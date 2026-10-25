import Foundation

func savedStatus(time: String) -> String {
    String(localized: "checkIn.saved.status \(time)")
}

func durationLabel(seconds: Double) -> String {
    String(format: "%.1f", seconds)
}
