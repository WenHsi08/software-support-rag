import sqlite3
from pathlib import Path
import json


def init_db(db_path: Path) -> None:
    """建立資料庫與資料表；已存在時保留原本資料。"""

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # with 負責交易提交或回復，finally 負責關閉連線
    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    source_file TEXT NOT NULL UNIQUE,
                    source_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (document_id)
                        REFERENCES documents(id)
                        ON DELETE CASCADE,
                    UNIQUE (document_id, chunk_index)
                );

                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY,
                    chunk_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    vector_json TEXT NOT NULL,
                    FOREIGN KEY (chunk_id)
                        REFERENCES chunks(id)
                        ON DELETE CASCADE,
                    UNIQUE (chunk_id, model, dimensions)
                );
            """)
    finally:
        connection.close()


def save_document(
    db_path: Path,
    source_file: str,
    source_id: str,
    content_hash: str,
    chunks: list[dict],
    vectors: list[list[float]],
    model: str,
) -> None:
    """保存一份文件的區塊與向量，取代該文件的舊資料。"""

    if len(chunks) != len(vectors):
        raise ValueError("區塊數量與向量數量不一致。")

    if not chunks:
        raise ValueError("沒有可保存的區塊。")

    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        # 整份文件一起保存：中途失敗時，回復本次修改
        with connection:
            # 刪除該文件的舊資料
            # ON DELETE CASCADE 會一併刪除其區塊與向量
            connection.execute(
                "DELETE FROM documents WHERE source_file = ?",
                (source_file,),
            )

            cursor = connection.execute(
                """
                INSERT INTO documents (
                    source_file, source_id, content_hash
                )
                VALUES (?, ?, ?)
                """,
                (source_file, source_id, content_hash),
            )

            document_id = cursor.lastrowid

            for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
                cursor = connection.execute(
                    """
                    INSERT INTO chunks (
                        document_id, chunk_index, chunk_type, content
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        index,
                        chunk["chunk_type"],
                        chunk["content"],
                    ),
                )

                chunk_id = cursor.lastrowid

                connection.execute(
                    """
                    INSERT INTO embeddings (
                        chunk_id, model, dimensions, vector_json
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        model,
                        len(vector),
                        json.dumps(vector),
                    ),
                )
    finally:
        connection.close()

def load_document_vectors(
    db_path: Path,
    source_file: str,
    source_id: str,
    content_hash: str,
    chunks: list[dict],
    model: str,
    dimensions: int,
) -> list[list[float]] | None:
    """資料與設定一致時回傳向量，否則回傳 None。"""

    connection = sqlite3.connect(db_path)

    try:
        document = connection.execute(
            """
            SELECT id, source_id, content_hash
            FROM documents
            WHERE source_file = ?
            """,
            (source_file,),
        ).fetchone()

        if document is None:
            return None

        document_id, saved_source_id, saved_hash = document

        # 文件內容或編號不同，不能沿用舊向量
        if saved_source_id != source_id or saved_hash != content_hash:
            return None

        rows = connection.execute(
            """
            SELECT
                c.chunk_index,
                c.chunk_type,
                c.content,
                e.vector_json
            FROM chunks AS c
            JOIN embeddings AS e ON e.chunk_id = c.id
            WHERE c.document_id = ?
              AND e.model = ?
              AND e.dimensions = ?
            ORDER BY c.chunk_index
            """,
            (document_id, model, dimensions),
        ).fetchall()

        if len(rows) != len(chunks):
            return None

        vectors = []

        for index, (row, chunk) in enumerate(zip(rows, chunks)):
            saved_index, saved_type, saved_content, vector_json = row

            # 檢查切分結果、順序與分類是否一致
            if (
                saved_index != index
                or saved_type != chunk["chunk_type"]
                or saved_content != chunk["content"]
            ):
                return None

            vector = json.loads(vector_json)

            if len(vector) != dimensions:
                return None

            vectors.append(vector)

        return vectors

    finally:
        connection.close()