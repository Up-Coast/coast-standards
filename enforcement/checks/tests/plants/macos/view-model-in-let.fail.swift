import SwiftUI

struct CheckInView: View {
    let viewModel: CheckInViewModel
    var session = SessionStore()

    init(recorder: AudioRecorder) {
        self.viewModel = CheckInViewModel(recorder: recorder)
    }

    var body: some View {
        Text("checkIn.title")
    }
}

struct HistoryView: View {
    private let viewModel = HistoryViewModel()

    var body: some View {
        Text("history.title")
    }
}

@Observable
final class SessionStore {}
