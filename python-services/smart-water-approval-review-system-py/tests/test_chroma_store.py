import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.config import config
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
        mock_collection.upsert.assert_called_once()

        count = store.count()
        self.assertEqual(count, 2)

    def test_fresh_persist_dir_first_write_creates_collection(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            persist_dir = Path(tmpdir) / "chroma"
            orig_persist = config.CHROMA_PERSIST_DIR
            orig_collection = config.CHROMA_COLLECTION_NAME
            try:
                config.CHROMA_PERSIST_DIR = str(persist_dir)
                config.CHROMA_COLLECTION_NAME = "fresh_test"
                store = ChromaStore()

                chunk = ChunkResult(content="hello", metadata={"source_file": "a.pdf", "chunk_index": 0})
                emb = [[0.1, 0.2, 0.3]]
                count = store.store_chunks([chunk], emb)

                self.assertEqual(1, count)
                self.assertEqual(1, store.count())
            finally:
                config.CHROMA_PERSIST_DIR = orig_persist
                config.CHROMA_COLLECTION_NAME = orig_collection

    def test_repeat_ingest_different_file_order_does_not_duplicate(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            persist_dir = Path(tmpdir) / "chroma"
            orig_persist = config.CHROMA_PERSIST_DIR
            orig_collection = config.CHROMA_COLLECTION_NAME
            try:
                config.CHROMA_PERSIST_DIR = str(persist_dir)
                config.CHROMA_COLLECTION_NAME = "dup_test"
                store = ChromaStore()

                emb = [[0.1, 0.2, 0.3]]
                chunks_a = [
                    ChunkResult(
                        content="docx block 0 chunk 0",
                        metadata={"source_file": "a.docx", "block_index": 0, "chunk_index": 0},
                    ),
                    ChunkResult(
                        content="pdf block 0 chunk 0",
                        metadata={"source_file": "b.pdf", "block_index": 0, "chunk_index": 0},
                    ),
                ]
                emb_a = [emb[0], emb[0]]

                r1 = store.store_chunks(chunks_a, emb_a)
                self.assertEqual(2, r1)
                self.assertEqual(2, store.count())

                chunks_b = [
                    ChunkResult(
                        content="pdf block 0 chunk 0",
                        metadata={"source_file": "b.pdf", "block_index": 0, "chunk_index": 0},
                    ),
                    ChunkResult(
                        content="docx block 0 chunk 0",
                        metadata={"source_file": "a.docx", "block_index": 0, "chunk_index": 0},
                    ),
                ]
                emb_b = [emb[0], emb[0]]

                r2 = store.store_chunks(chunks_b, emb_b)
                self.assertEqual(2, r2)
                self.assertEqual(2, store.count())
            finally:
                config.CHROMA_PERSIST_DIR = orig_persist
                config.CHROMA_COLLECTION_NAME = orig_collection
