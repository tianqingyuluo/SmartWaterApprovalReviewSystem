import unittest
from unittest.mock import MagicMock, patch

from src.ingest.chroma_store import ChromaStore
from src.ingest.models import ChunkResult


class TestChromaStore(unittest.TestCase):
    @patch("src.ingest.chroma_store.chromadb.PersistentClient")
    def test_store_chunks_empty(self, mock_persistent):
        store = ChromaStore()
        result = store.store_chunks([], [])
        self.assertEqual(result, 0)

    @patch("src.ingest.chroma_store.chromadb.PersistentClient")
    def test_store_chunks_mismatch_raises(self, mock_persistent):
        store = ChromaStore()
        chunks = [ChunkResult(content="test", metadata={"source_file": "a.pdf", "chunk_index": 0})]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        with self.assertRaises(ValueError):
            store.store_chunks(chunks, embeddings)

    @patch("src.ingest.chroma_store.chromadb.PersistentClient")
    def test_store_and_count(self, mock_persistent):
        store = ChromaStore()
        mock_collection = MagicMock()
        store._client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 2

        chunks = [
            ChunkResult(content="chunk1", metadata={"source_file": "a.pdf", "chunk_index": 0}),
            ChunkResult(content="chunk2", metadata={"source_file": "a.pdf", "chunk_index": 1}),
        ]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

        result = store.store_chunks(chunks, embeddings)
        self.assertEqual(result, 2)
        mock_collection.add.assert_called_once()

        count = store.count()
        self.assertEqual(count, 2)
