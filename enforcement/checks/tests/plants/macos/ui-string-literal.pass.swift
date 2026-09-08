// The pass plant carries every context Coast's copy guard treats as NOT copy
// (CoastCopyGuardTests.skipSuffixes and its raw-value / key rules), plus the
// customer-app contexts and the SQL shape tuned on Coast's own tree (E1.2).
// The scanner must report nothing here — parity with the guard is the proof.
import SwiftUI

struct HomeView: View {
    enum Sheet: String {
        case shipConfirm = "Ship it now"                      // a raw-value case is an identifier
    }
    static let key = "Save your changes"                      // a named key, not words on screen
    let id: String = "receipt-\(UUID())"                      // an identifier around an interpolation
    var body: some View {
        VStack {
            Text("home.saveButton")                              // a semantic key
            Image(systemName: "square.and.arrow.up")
            Label("home.share", systemImage: "square.and.arrow.up")
            Button("home.ok") {}.keyboardShortcut("s", modifiers: .command)
            Text(verbatim: String(localized: "home.title"))
            TextField("home.name", text: .constant(""))
                .accessibilityIdentifier("Home Name Field")
            Text(Font.custom("Avenir Next", size: 12).description)
            Color("Brand Teal")
            Text(store.status == "Ready to ship" ? "home.ready" : "home.waiting")
            Text(names.contains("Pat Lee") ? "home.known" : "home.new")
            Text(dictionary["Display Name"] ?? "home.unknown")
            Text(project.hasPrefix("Coast ") ? "home.coast" : "home.other")
        }
        .tag("Home Tab")
        .onAppear { print("Home appeared on screen") }
        .task { _ = try? await database.execute("SELECT name, count FROM items WHERE done = 0 ORDER BY name") }
    }
}

#Preview("Home, empty state") { HomeView() }
