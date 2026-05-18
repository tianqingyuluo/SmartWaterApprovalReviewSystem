import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ingest.ingest_pipeline import IngestPipeline
from src.ingest.models import ChunkResult, IngestStats


class TestIngestPipeline(unittest.TestCase):
    @patch("src.ingest.ingest_pipeline.EmbeddingClient")
    @patch("src.ingest.ingest_pipeline.ChromaStore")
    def test_no_source_dir_returns_error(self, mock_store, mock_embedder):
        pipeline = IngestPipeline(source_dir="")
        stats = pipeline.run()
        self.assertGreater(len(stats.errors), 0)
        self.assertTrue(any("KNOWLEDGE_SOURCE_DIR" in err for err in stats.errors))

    @patch("src.ingest.ingest_pipeline.EmbeddingClient")
    @patch("src.ingest.ingest_pipeline.ChromaStore")
    def test_source_dir_not_found_returns_error(self, mock_store, mock_embedder):
        pipeline = IngestPipeline(source_dir="/tmp/nonexistent_dir_for_test_12345")
        stats = pipeline.run()
        self.assertGreater(len(stats.errors), 0)

    @patch("src.ingest.ingest_pipeline.IngestPipeline.run")
    def test_stats_shape(self, mock_run):
        mock_run.return_value = IngestStats(
            doc_count=3,
            block_count=10,
            chunk_count=25,
            vector_count=25,
            sources=["a.docx", "b.pdf", "c.jpg"],
            errors=[],
        )
        stats = mock_run()
        self.assertEqual(stats.doc_count, 3)
        self.assertEqual(stats.chunk_count, 25)
        self.assertEqual(stats.vector_count, 25)
        self.assertEqual(len(stats.sources), 3)
        self.assertEqual(len(stats.errors), 0)

    @patch("src.ingest.ingest_pipeline.config")
    @patch("src.ingest.ingest_pipeline.list_source_files")
    @patch("src.ingest.ingest_pipeline.parse_file")
    @patch("src.ingest.ingest_pipeline.split_blocks")
    @patch("src.ingest.ingest_pipeline.ChromaStore")
    @patch("src.ingest.ingest_pipeline.EmbeddingClient")
    def test_embedding_batch_failure_keeps_chunk_embedding_paired(
        self,
        mock_embedder_cls,
        mock_store_cls,
        mock_split,
        mock_parse,
        mock_list,
        mock_config,
    ):
        with tempfile.TemporaryDirectory() as source_dir:
            mock_config.CHUNK_SIZE = 100
            mock_config.CHUNK_OVERLAP = 10

            def _make_chunk(i):
                return ChunkResult(content=f"token{i}", metadata={"source_file": "a.pdf", "chunk_index": i})

            mock_list.return_value = [Path(source_dir) / "a.pdf"]
            mock_parse.return_value = [_make_chunk(0)] * 16

            batch_0_chunks = [_make_chunk(i) for i in range(16)]
            batch_1_chunks = [_make_chunk(i) for i in range(16, 32)]
            mock_split.return_value = batch_0_chunks + batch_1_chunks

            mock_embedder = mock_embedder_cls.return_value
            batch_1_embs = [[float(i + 16), float(i + 17)] for i in range(16)]
            mock_embedder.embed.side_effect = [RuntimeError("boom"), batch_1_embs]

            mock_store = mock_store_cls.return_value

            pipeline = IngestPipeline(source_dir=source_dir)
            stats = pipeline.run()

            self.assertEqual(1, mock_store.store_chunks.call_count)
            stored_chunks, _stored_embs = mock_store.store_chunks.call_args[0]
            stored_texts = [c.content for c in stored_chunks]

            self.assertIn("token16", stored_texts)
            self.assertNotIn("token0", stored_texts)
            self.assertEqual(len(stats.errors), 1)
