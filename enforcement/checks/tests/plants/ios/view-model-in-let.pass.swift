import SwiftUI

struct CheckInView: View {
    let viewModel: CheckInViewModel
    @State private var session = SessionStore()
    @StateObject private var legacy = LegacyViewModel()
    @State private var history: HistoryViewModel

    init(viewModel: CheckInViewModel) {
        self.viewModel = viewModel
        _history = State(initialValue: HistoryViewModel())
    }

    var body: some View {
        Button("checkIn.retry") {
            let draft = DraftViewModel()
            draft.start()
        }
    }
}

final class CheckInViewModel {
    let child = ChildViewModel()
}

@Observable
final class SessionStore {}
