import unittest
from unittest.mock import patch

from src.ingest.ingest_pipeline import IngestPipeline
from src.ingest.models import IngestStats


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
