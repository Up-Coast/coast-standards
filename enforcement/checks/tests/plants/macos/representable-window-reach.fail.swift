struct Bridge: NSViewRepresentable { func makeNSView(context: Context) -> NSView { let v = NSView(); v.window?.title = "x"; return v } }
