import aiosqlite


class AsyncSQLiteSessionDB:
    def __init__(self):
        self.db_name = 'db.sqlite'
        self.connection = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_name)
        await self.create_sessions_table()

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def create_sessions_table(self):
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_file_path TEXT NOT NULL
            );
        '''
        await self.connection.execute(create_table_query)
        await self.connection.commit()

    async def insert_session(self, session_file_path):
        insert_query = '''
            INSERT INTO sessions (session_file_path) VALUES (?);
        '''
        cursor = await self.connection.execute(insert_query, (session_file_path,))
        await self.connection.commit()
        return cursor.lastrowid

    async def get_session(self, session_id):
        select_query = '''
            SELECT * FROM sessions WHERE id = ?;
        '''
        cursor = await self.connection.execute(select_query, (session_id,))
        return await cursor.fetchone()

    async def get_all_sessions(self):
        select_query = '''
            SELECT * FROM sessions;
        '''
        cursor = await self.connection.execute(select_query)
        return await cursor.fetchall()

    async def update_session(self, session_id, session_file_path):
        update_query = '''
            UPDATE sessions SET session_file_path = ? WHERE id = ?;
        '''
        await self.connection.execute(update_query, (session_file_path, session_id))
        await self.connection.commit()

    async def delete_session(self, session_id):
        delete_query = '''
            DELETE FROM sessions WHERE id = ?;
        '''
        await self.connection.execute(delete_query, (session_id,))
        await self.connection.commit()
