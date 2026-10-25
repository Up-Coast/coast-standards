import SwiftUI

struct HomeView: View {
    @State private var checkIn: CheckInViewModel?
    @State private var history = HistoryViewModel()
    let recorder: AudioRecorder

    var body: some View {
        VStack {
            Button("checkIn.start") { checkIn = CheckInViewModel(recorder: recorder) }
            NavigationLink(destination: HistoryView(viewModel: history)) {
                Text("history.open")
            }
        }
        .sheet(item: $checkIn) { model in
            CheckInView(viewModel: model)
        }
        // .fullScreenCover { CheckInView(viewModel: CheckInViewModel()) }
        .popover(isPresented: .constant(false)) {
            Text("checkIn.help")
        }
    }
}
