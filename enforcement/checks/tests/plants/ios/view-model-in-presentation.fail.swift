import SwiftUI

struct HomeView: View {
    @State private var showingCheckIn = false
    @State private var showingHistory = false
    let recorder: AudioRecorder

    var body: some View {
        VStack {
            Button("checkIn.start") { showingCheckIn = true }
            NavigationLink(destination: HistoryView(viewModel: HistoryViewModel())) {
                Text("history.open")
            }
        }
        .sheet(isPresented: $showingCheckIn) {
            CheckInView(viewModel: CheckInViewModel(recorder: recorder))
        }
        .popover(isPresented: $showingHistory) {
            SessionView(store: SessionStore())
        }
    }
}

@Observable
final class SessionStore {}
