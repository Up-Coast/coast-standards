const rows = await sql.query('SELECT * FROM notes WHERE id = $1', [noteId]);
