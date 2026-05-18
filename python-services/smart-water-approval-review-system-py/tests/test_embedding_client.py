import unittest
from unittest.mock import patch

from src.ingest.embedding_client import EmbeddingClient


class TestEmbeddingClient(unittest.TestCase):
    @patch("src.ingest.embedding_client.OpenAI")
    def test_embed_empty_list(self, mock_openai):
        client = EmbeddingClient()
        result = client.embed([])
        self.assertEqual(result, [])

    @patch("src.ingest.embedding_client.OpenAI")
    def test_embed_success(self, mock_openai):
        mock_instance = mock_openai.return_value
        mock_emb = mock_instance.embeddings.create.return_value
        mock_emb.data = [
            type("EmbeddingData", (), {"embedding": [0.1, 0.2, 0.3]})(),
            type("EmbeddingData", (), {"embedding": [0.4, 0.5, 0.6]})(),
        ]

        client = EmbeddingClient()
        result = client.embed(["text1", "text2"])

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], [0.1, 0.2, 0.3])
        self.assertEqual(result[1], [0.4, 0.5, 0.6])

    @patch("src.ingest.embedding_client.OpenAI")
    def test_embed_api_error_raises(self, mock_openai):
        mock_instance = mock_openai.return_value
        mock_instance.embeddings.create.side_effect = RuntimeError("API error")

        client = EmbeddingClient()
        with self.assertRaises(RuntimeError):
            client.embed(["text1"])
