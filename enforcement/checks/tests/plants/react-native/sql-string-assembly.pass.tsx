const rows = await db.getAllAsync('SELECT * FROM notes WHERE id = ?', [noteId]);
