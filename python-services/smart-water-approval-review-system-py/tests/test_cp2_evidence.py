import unittest
from unittest.mock import patch

from src.cp2_evidence import IngestError


class TestCp2Evidence(unittest.TestCase):
    @patch("src.cp2_evidence._check_config")
    @patch("src.cp2_evidence.run_ingest")
    @patch("src.cp2_evidence.verify_chromadb")
    @patch("src.cp2_evidence.run_tool_demos")
    def test_run_full_evidence_ok_returns_zero(self, mock_demos, mock_verify, mock_ingest, mock_config):
        from src.cp2_evidence import run_full_evidence

        rc = run_full_evidence(rebuild=True)
        self.assertEqual(0, rc)
        mock_config.assert_called_once()
        mock_ingest.assert_called_once_with(rebuild=True)
        mock_verify.assert_called_once()
        mock_demos.assert_called_once()

    @patch("src.cp2_evidence._check_config")
    @patch("src.cp2_evidence.run_ingest")
    @patch("src.cp2_evidence.verify_chromadb")
    @patch("src.cp2_evidence.run_tool_demos")
    def test_ingest_aborted_skips_rest_and_returns_1(
        self, mock_demos, mock_verify, mock_ingest, mock_config
    ):
        from src.cp2_evidence import run_full_evidence

        mock_ingest.side_effect = IngestError("no source")

        rc = run_full_evidence(rebuild=False)
        self.assertEqual(1, rc)
        mock_verify.assert_not_called()
        mock_demos.assert_not_called()
