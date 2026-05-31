"""
Red Test: 表格字段提取测试

测试目标：验证从表格中提取键值对时的行为
- 空白值提取为占位符 "-"（空字段也要切出，标记为空）
- 值与键完全相同的表头重复行不提取
"""
import unittest

from src.models import ExtractedField


class TestTableFieldExtraction(unittest.TestCase):
    """测试表格字段提取功能"""

    def test_should_extract_empty_table_values_as_placeholder(self):
        """空白的表格值应该提取为占位符 "-"（空字段也要切出）"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        # 模拟空白表单的表格数据
        rows = [
            ["统一社会信用代码（身份证号码）", ""],  # 空值
            ["法定代表人", ""],  # 空值
            ["住所（住址）", ""],  # 空值
            ["邮编", "123456"],  # 有值
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：所有字段都应被提取，空字段标记为 "-"
        self.assertEqual(4, len(fields), "应该提取所有4个字段，包括空字段")

        # 空字段应该用占位符
        empty_fields = [f for f in fields if f.field_value == "-"]
        self.assertEqual(3, len(empty_fields), "应该有3个空字段标记为 -")

        # 有值字段保持原值
        filled_field = [f for f in fields if f.field_value == "123456"]
        self.assertEqual(1, len(filled_field))

    def test_should_not_extract_when_value_is_same_as_key(self):
        """当值与键相同时（可能是表头重复），不应该提取"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        # 模拟表格解析错误，值列重复了键列
        rows = [
            ["统一社会信用代码（身份证号码）", "统一社会信用代码（身份证号码）"],
            ["法定代表人", "法定代表人"],
            ["住所（住址）", "北京市朝阳区"],  # 正常值
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：不应该提取重复的字段
        self.assertEqual(1, len(fields), "不应该提取值与键相同的字段")
        # 注意：字段名会被规范化，括号会被转换为下划线
        self.assertIn(fields[0].field_key, ["住所（住址）", "住所_住址"])
        self.assertEqual("北京市朝阳区", fields[0].field_value)

    def test_should_extract_valid_key_value_pairs(self):
        """应该正确提取有效的键值对"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        rows = [
            ["企业名称", "深圳市宝安区诚信环保处理有限公司"],
            ["统一社会信用代码", "91441303MA531L6K37"],
            ["法定代表人", "张三"],
        ]

        fields = _extract_key_value_fields(rows, "BUSINESS_LICENSE")

        # 验证：应该提取所有有效字段
        self.assertEqual(3, len(fields))
        self.assertEqual("企业名称", fields[0].field_key)
        self.assertEqual("深圳市宝安区诚信环保处理有限公司", fields[0].field_value)

    def test_should_handle_whitespace_only_values(self):
        """只包含空白字符的值应该被视为空值，提取为占位符 "-" """
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        rows = [
            ["字段1", "   "],  # 只有空格
            ["字段2", "\t\n"],  # 只有制表符和换行
            ["字段3", "实际值"],  # 有值
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：所有字段都提取，空白值标记为 "-"
        self.assertEqual(3, len(fields))

        # 空白值字段应标记为 "-"
        empty_fields = [f for f in fields if f.field_value == "-"]
        self.assertEqual(2, len(empty_fields), "2个空白字段应标记为 -")

        # 有值字段保持原值
        filled_field = [f for f in fields if f.field_value == "实际值"]
        self.assertEqual(1, len(filled_field))

    def test_should_handle_single_column_tables(self):
        """单列表格不应该被提取为键值对"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        rows = [
            ["标题"],
            ["内容1"],
            ["内容2"],
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：单列表格不提取
        self.assertEqual(0, len(fields))


if __name__ == "__main__":
    unittest.main()
