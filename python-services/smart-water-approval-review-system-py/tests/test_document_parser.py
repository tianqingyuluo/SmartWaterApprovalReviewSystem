import unittest
from pathlib import Path

from src.ingest.document_parser import SUPPORTED_EXTENSIONS, list_source_files, parse_file


class TestDocumentParser(unittest.TestCase):
    def test_supported_extensions_contains_expected(self):
        self.assertIn(".docx", SUPPORTED_EXTENSIONS)
        self.assertIn(".pdf", SUPPORTED_EXTENSIONS)
        self.assertIn(".jpg", SUPPORTED_EXTENSIONS)
        self.assertIn(".jpeg", SUPPORTED_EXTENSIONS)
        self.assertIn(".png", SUPPORTED_EXTENSIONS)
        self.assertIn(".doc", SUPPORTED_EXTENSIONS)

    def test_parse_unsupported_extension_returns_empty(self):
        result = parse_file("/fake/test.txt")
        self.assertEqual(result, [])

    def test_list_source_files_nonexistent_dir(self):
        result = list_source_files("/nonexistent/path")
        self.assertEqual(result, [])

    def test_parse_docx_nonexistent_file_returns_empty(self):
        result = parse_file("/nonexistent/test.docx")
        self.assertEqual(result, [])

    def test_parse_pdf_nonexistent_file_returns_empty(self):
        result = parse_file("/nonexistent/test.pdf")
        self.assertEqual(result, [])

    def test_parse_image_returns_placeholder_block(self):
        result = parse_file("/fake/test.jpg")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].doc_type, "image")
        self.assertIn("GLM OCR", result[0].content)

    def test_parse_png_returns_placeholder(self):
        result = parse_file("/fake/test.png")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].doc_type, "image")

    def test_list_source_files_source_dir_does_not_exist(self):
        result = list_source_files("/tmp/nonexistent_src_dir_for_test")
        self.assertEqual(result, [])

    def test_source_dir_with_no_matching_files(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "readme.txt").write_text("hello")
            result = list_source_files(tmpdir)
            self.assertEqual(result, [])
