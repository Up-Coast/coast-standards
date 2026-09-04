/// One unsaved note.
public struct Draft {
    /// The note's title.
    public var title: String
    /// Writes the draft to disk.
    public func save() {}
    var cache: Int = 0
}
