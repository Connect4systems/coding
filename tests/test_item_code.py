import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch


class ItemCodeTests(unittest.TestCase):
	def setUp(self):
		frappe = ModuleType("frappe")
		frappe._ = lambda value: value
		frappe.throw = MagicMock(side_effect=ValueError)
		frappe.db = MagicMock()
		frappe.db.exists.return_value = False
		frappe.get_all = MagicMock(return_value=[])
		self.group = SimpleNamespace(
			name="TV",
			is_group=0,
			custom_category="Electronics",
			custom_item_group_abr="tv",
		)
		frappe.get_doc = MagicMock(
			side_effect=lambda doctype, name: {
				"Item Group": self.group,
				"Category": SimpleNamespace(category_abr=" ele "),
				"Brand": SimpleNamespace(custom_brand_abr="sam"),
			}[doctype]
		)
		naming = ModuleType("frappe.model.naming")
		naming.getseries = MagicMock(return_value="001")
		spec = importlib.util.spec_from_file_location(
			"tested_item_code", Path(__file__).parents[1] / "coding/item_code.py"
		)
		self.module = importlib.util.module_from_spec(spec)
		with patch.dict(sys.modules, {"frappe": frappe, "frappe.model.naming": naming}):
			spec.loader.exec_module(self.module)
		self.frappe = frappe
		self.series = naming.getseries
		self.doc = SimpleNamespace(
			item_group="TV",
			item_code="COPIED-CODE",
			name="old",
			brand="Samsung",
			custom_category="Electronics",
			is_new=lambda: True,
			get=lambda field: None,
		)

	def test_generate_from_item_selections_and_replace_copied_code(self):
		self.module.set_item_code(self.doc)
		self.assertEqual(self.doc.item_code, "ELE-SAM-TV-001")
		self.assertEqual(self.doc.name, self.doc.item_code)
		self.assertEqual((self.doc.brand, self.doc.custom_category), ("Samsung", "Electronics"))

		self.frappe.get_doc.assert_any_call("Brand", "Samsung")
		self.frappe.get_doc.assert_any_call("Category", "Electronics")

	def test_category_mismatch_rejected(self):
		self.doc.custom_category = "Other"
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_missing_category_rejected(self):
		self.doc.custom_category = None
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_different_brand_uses_selected_brand(self):
		self.doc.brand = "Another Brand"
		self.module.set_item_code(self.doc)
		self.frappe.get_doc.assert_any_call("Brand", "Another Brand")
		self.assertEqual(self.doc.brand, "Another Brand")

	def test_existing_items_unchanged(self):
		self.doc.is_new = lambda: False
		self.module.set_item_code(self.doc)
		self.assertEqual(self.doc.item_code, "COPIED-CODE")
		self.series.assert_not_called()

	def test_variants_keep_standard_naming(self):
		self.doc.get = lambda field: "template"
		self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_missing_brand_fails_before_allocating(self):
		self.doc.brand = None
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_invalid_abbreviation_fails_before_allocating(self):
		self.group.custom_item_group_abr = "T-V"
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_parent_group_rejected(self):
		self.group.is_group = 1
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_legacy_gaps_and_non_numeric_suffixes(self):
		self.frappe.get_all.return_value = ["ELE-SAM-TV-002", "ELE-SAM-TV-050", "ELE-SAM-TV-OTHER"]
		self.series.side_effect = ["001", "051"]
		self.module.set_item_code(self.doc)
		self.assertEqual(self.doc.item_code, "ELE-SAM-TV-051")
		self.assertEqual(self.frappe.db.sql.call_args.args[1], (50, "ELE-SAM-TV-"))

	def test_existing_code_skipped(self):
		self.series.side_effect = ["002", "003"]
		self.frappe.db.exists.side_effect = [True, False]
		self.module.set_item_code(self.doc)
		self.assertEqual(self.doc.item_code, "ELE-SAM-TV-003")

	def test_sequence_continues_past_999(self):
		self.series.return_value = "1000"
		self.module.set_item_code(self.doc)
		self.assertEqual(self.doc.item_code, "ELE-SAM-TV-1000")


if __name__ == "__main__":
	unittest.main()
