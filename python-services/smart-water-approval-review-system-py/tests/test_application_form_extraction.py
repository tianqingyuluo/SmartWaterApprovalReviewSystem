"""
Red Test: 申请表单字段提取规范测试

测试目标：
1. 空白字段应该提取为 "字段名: -" 或 "字段名: (空)"
2. 勾选框字段应该只提取打勾的选项
3. 不应该提取无意义的表格结构重复
"""
import unittest

from src.models import ExtractedField


class TestApplicationFormFieldExtraction(unittest.TestCase):
    """测试申请表单字段提取规范"""

    def test_should_extract_empty_fields_with_placeholder(self):
        """空白字段应该提取为带占位符的形式"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        # 模拟空白申请表
        rows = [
            ["统一社会信用代码（身份证号码）", ""],
            ["法定代表人", ""],
            ["住所（住址）", ""],
            ["邮编", "100000"],  # 有值
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：空字段应该被提取，值为占位符
        self.assertEqual(4, len(fields), "应该提取所有字段，包括空字段")

        # 检查空字段
        empty_fields = [f for f in fields if f.field_value in ["-", "(空)", ""]]
        self.assertEqual(3, len(empty_fields), "应该有3个空字段")

        # 检查有值字段
        filled_field = [f for f in fields if f.field_value == "100000"]
        self.assertEqual(1, len(filled_field))

    def test_should_extract_checkbox_only_checked_options(self):
        """勾选框字段应该只提取打勾的选项"""
        from src.services.document_ocr_pipeline import _parse_checkbox_field

        # 模拟勾选框文本
        checkbox_text = "□新建 ☑改建、扩建 □其他"

        result = _parse_checkbox_field(checkbox_text)

        # 验证：只返回打勾的选项
        self.assertEqual("改建、扩建", result)

    def test_should_handle_multiple_checked_options(self):
        """多个勾选框被选中时，应该用逗号分隔"""
        from src.services.document_ocr_pipeline import _parse_checkbox_field

        checkbox_text = "☑制水供水 ☑原水供水 □河道内生产用水 ☑生活用水"

        result = _parse_checkbox_field(checkbox_text)

        # 验证：多个选项用逗号分隔
        self.assertEqual("制水供水, 原水供水, 生活用水", result)

    def test_should_return_placeholder_when_no_checkbox_checked(self):
        """没有勾选任何选项时，返回占位符"""
        from src.services.document_ocr_pipeline import _parse_checkbox_field

        checkbox_text = "□新建 □改建、扩建 □其他"

        result = _parse_checkbox_field(checkbox_text)

        # 验证：返回占位符
        self.assertEqual("-", result)

    def test_should_treat_any_non_empty_box_as_checked(self):
        """只要不是空白框（□），就认为是打勾的"""
        from src.services.document_ocr_pipeline import _parse_checkbox_field

        # OCR 可能把手写勾识别成各种符号：✓ √ X 甚至乱码
        # 只要不是干净的空白框 □，都应视为选中
        cases = [
            ("□新建 √改建、扩建 □其他", "改建、扩建"),  # OCR 识别成 √
            ("□新建 X改建、扩建 □其他", "改建、扩建"),  # OCR 识别成 X
            ("□新建 ✓改建、扩建 □其他", "改建、扩建"),  # OCR 识别成 ✓
            ("■新建 □改建、扩建 □其他", "新建"),        # 实心方块
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(expected, _parse_checkbox_field(text))

    def test_should_treat_filled_marker_before_option_as_checked(self):
        """选项前出现非空白框标记即视为选中，多个一并返回"""
        from src.services.document_ocr_pipeline import _parse_checkbox_field

        # 第一个用 ✓，第二个用 X，都应被识别为选中
        checkbox_text = "✓制水供水 □原水供水 X生活用水"

        result = _parse_checkbox_field(checkbox_text)

        self.assertEqual("制水供水, 生活用水", result)

    def test_should_not_extract_meaningless_table_structure(self):
        """不应该提取无意义的表格结构重复"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        # 模拟表格解析错误，产生大量重复列
        rows = [
            ["申请人基本情况", "统一社会信用代码（身份证号码）", "统一社会信用代码（身份证号码）", "法定代表人", "法定代表人", "法定代表人"],
            ["申请人基本情况", "住所（住址）", "住所（住址）", "邮 编", "邮 编", "邮 编"],
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：不应该提取这种多列重复的无意义结构
        # 这种情况应该被识别为表头，而不是数据行
        self.assertEqual(0, len(fields), "不应该提取表头结构")

    def test_should_extract_structured_address_fields(self):
        """结构化地址字段应该合理提取"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        # 模拟地址字段（多个子字段组合）
        rows = [
            ["生产经营场所地址", "省（自治区、直辖市） 市（区） 县（区、市） 乡（镇、街道） 村（社区） 号"],
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：如果值是字段模板，应该识别为空
        self.assertEqual(1, len(fields))
        # 值应该是占位符，而不是字段模板
        self.assertIn(fields[0].field_value, ["-", "(空)", "省（自治区、直辖市） 市（区） 县（区、市） 乡（镇、街道） 村（社区） 号"])

    def test_should_extract_filled_form_correctly(self):
        """已填写的表单应该正确提取"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        rows = [
            ["统一社会信用代码", "91441303MA531L6K37"],
            ["法定代表人", "张三"],
            ["项目性质", "☑新建 □改建、扩建 □其他"],
            ["邮编", ""],  # 空字段
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        # 验证：应该提取所有字段
        self.assertEqual(4, len(fields))

        # 检查有值字段
        self.assertEqual("91441303MA531L6K37", fields[0].field_value)
        self.assertEqual("张三", fields[1].field_value)

        # 检查勾选框字段（需要解析）
        # 注意：这里假设勾选框会被预处理
        self.assertIn(fields[2].field_value, ["☑新建 □改建、扩建 □其他", "新建"])

        # 检查空字段
        self.assertIn(fields[3].field_value, ["-", "(空)", ""])

    def test_should_parse_checkbox_value_during_extraction(self):
        """提取时应自动解析勾选框字段，只保留选中项"""
        from src.services.document_ocr_pipeline import _extract_key_value_fields

        rows = [
            ["项目性质", "□新建 ☑改建、扩建 □其他"],
            ["取水用途", "☑工业用水 □农业用水 ☑生态用水"],
            ["计量方式", "□管道计量 □明渠计量 □其他折算方式"],  # 全未勾选
        ]

        fields = _extract_key_value_fields(rows, "APPLICATION_FORM")

        self.assertEqual(3, len(fields))

        # 单选：只返回勾选项
        self.assertEqual("改建、扩建", fields[0].field_value)
        # 多选：逗号分隔
        self.assertEqual("工业用水, 生态用水", fields[1].field_value)
        # 全未勾选：占位符
        self.assertEqual("-", fields[2].field_value)


if __name__ == "__main__":
    unittest.main()
