Button("notes.delete", role: .destructive) { delete() }
Button("notes.keep") { dismiss() }
    .keyboardShortcut(.defaultAction)
