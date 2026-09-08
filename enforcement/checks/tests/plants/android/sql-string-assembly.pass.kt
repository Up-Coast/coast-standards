val rows = db.rawQuery("SELECT * FROM notes WHERE id = ?", arrayOf(noteId))
