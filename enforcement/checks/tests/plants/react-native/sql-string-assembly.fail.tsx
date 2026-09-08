const rows = await db.execAsync(`SELECT * FROM notes WHERE id = ${noteId}`);
