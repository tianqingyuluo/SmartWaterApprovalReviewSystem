# -*- coding: utf-8 -*-
from src.services.document_ocr_pipeline import _parse_checkbox_field

# 测试1：单个选中
text1 = "□新建 ☑改建、扩建 □其他"
result1 = _parse_checkbox_field(text1)
print(f"测试1: {text1}")
print(f"结果: {result1}")
print()

# 测试2：多个选中
text2 = "☑制水供水 ☑原水供水 □河道内生产用水 ☑生活用水"
result2 = _parse_checkbox_field(text2)
print(f"测试2: {text2}")
print(f"结果: {result2}")
print()

# 测试3：没有选中
text3 = "□新建 □改建、扩建 □其他"
result3 = _parse_checkbox_field(text3)
print(f"测试3: {text3}")
print(f"结果: {result3}")
