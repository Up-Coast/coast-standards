import Foundation

func savedStatus(time: String) -> String {
    String(format: String(localized: "checkIn.saved.statusFormat"), time)
}

func savedCount(count: Int) -> String {
    String(
        format: NSLocalizedString("checkIn.saved.countFormat", comment: ""),
        count)
}
