import unittest

from src.ingest.models import DocumentBlock
from src.ingest.text_splitter import split_blocks


class TestTextSplitter(unittest.TestCase):
    def test_empty_blocks_produces_no_chunks(self):
        result = split_blocks([], chunk_size=100, chunk_overlap=10)
        self.assertEqual(result, [])

    def test_image_block_is_skipped(self):
        block = DocumentBlock(
            source_file="test.jpg",
            source_title="test",
            content="[Image]",
            doc_type="image",
        )
        result = split_blocks([block], chunk_size=100, chunk_overlap=10)
        self.assertEqual(result, [])

    def test_short_text_creates_one_chunk(self):
        block = DocumentBlock(
            source_file="test.docx",
            source_title="test",
            content="这是测试内容。",
            doc_type="paragraph",
        )
        result = split_blocks([block], chunk_size=512, chunk_overlap=64)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].content, "这是测试内容。")
        self.assertEqual(result[0].metadata["source_file"], "test.docx")
        self.assertEqual(result[0].metadata["chunk_index"], 0)

    def test_long_text_is_split(self):
        text = "段落内容。" * 200
        block = DocumentBlock(
            source_file="long.docx",
            source_title="long",
            content=text,
            doc_type="paragraph",
        )
        result = split_blocks([block], chunk_size=200, chunk_overlap=20)
        self.assertGreater(len(result), 1)

    def test_metadata_preserved_in_chunks(self):
        block = DocumentBlock(
            source_file="test.docx",
            source_title="TestDoc",
            content="测试内容保留元数据。",
            doc_type="paragraph",
            chapter="第一章",
            page_num=1,
        )
        result = split_blocks([block], chunk_size=100, chunk_overlap=10)
        self.assertEqual(len(result), 1)
        meta = result[0].metadata
        self.assertEqual(meta["source_file"], "test.docx")
        self.assertEqual(meta["source_title"], "TestDoc")
        self.assertEqual(meta["chapter"], "第一章")
        self.assertEqual(meta["page_num"], 1)
