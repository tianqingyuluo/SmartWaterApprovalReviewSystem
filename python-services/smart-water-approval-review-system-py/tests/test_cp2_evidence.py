import unittest
from unittest.mock import patch


class TestCp2Evidence(unittest.TestCase):
    @patch("src.cp2_evidence._check_config")
    @patch("src.cp2_evidence.run_ingest")
    @patch("src.cp2_evidence.verify_chromadb")
    @patch("src.cp2_evidence.run_tool_demos")
    def test_run_full_evidence_calls_all_stages(self, mock_demos, mock_verify, mock_ingest, mock_config):
        from src.cp2_evidence import run_full_evidence

        run_full_evidence(rebuild=True)
        mock_config.assert_called_once()
        mock_ingest.assert_called_once_with(rebuild=True)
        mock_verify.assert_called_once()
        mock_demos.assert_called_once()

    @patch("src.cp2_evidence._check_config")
    @patch("src.cp2_evidence.run_ingest")
    @patch("src.cp2_evidence.verify_chromadb")
    @patch("src.cp2_evidence.run_tool_demos")
    def test_no_rebuild_passes_false(self, mock_demos, mock_verify, mock_ingest, mock_config):
        from src.cp2_evidence import run_full_evidence

        run_full_evidence(rebuild=False)
        mock_ingest.assert_called_once_with(rebuild=False)
