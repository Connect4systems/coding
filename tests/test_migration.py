import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch


class MigrationTests(unittest.TestCase):
	def test_migrates_unique_brands_preserves_choices_and_reports_ambiguity(self):
		frappe = ModuleType("frappe")
		frappe.db = MagicMock()
		frappe.db.table_exists.return_value = True
		frappe.db.get_value.side_effect = lambda doctype, name, field: (
			"Chosen" if name == "Existing" else None
		)
		frappe.get_all = MagicMock(
			return_value=[
				SimpleNamespace(parent="Single", brand="A"),
				SimpleNamespace(parent="Single", brand="A"),
				SimpleNamespace(parent="Single", brand=None),
				SimpleNamespace(parent="Multiple", brand="A"),
				SimpleNamespace(parent="Multiple", brand="B"),
				SimpleNamespace(parent="Existing", brand="Old"),
			]
		)
		frappe.delete_doc = MagicMock()
		frappe.log_error = MagicMock()
		fields = ModuleType("frappe.custom.doctype.custom_field.custom_field")
		fields.create_custom_fields = MagicMock()
		spec = importlib.util.spec_from_file_location(
			"tested_migration",
			Path(__file__).parents[1] / "coding/patches/remove_legacy_brand_category_fields.py",
		)
		module = importlib.util.module_from_spec(spec)
		with patch.dict(sys.modules, {"frappe": frappe, fields.__name__: fields}):
			spec.loader.exec_module(module)
		module.execute()
		fields.create_custom_fields.assert_called_once()
		frappe.db.set_value.assert_called_once_with("Item Group", "Single", "custom_brand", "A")
		self.assertEqual(frappe.log_error.call_args.args[0], "Multiple")
		self.assertEqual(
			[call.args[1] for call in frappe.delete_doc.call_args_list],
			[
				"Brand-custom_categories",
				"Item Group-custom_brands",
				"Item Group-custom_section_break_d0ufr",
			],
		)


if __name__ == "__main__":
	unittest.main()
