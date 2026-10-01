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
			custom_item_group_abr="tv",
			custom_category="Electronics",
		)
		frappe.get_doc = MagicMock(
			side_effect=lambda doctype, name: {
				"Item Group": self.group,
				"Category": SimpleNamespace(name="Electronics", category_abr=" ele ", get=lambda field, default=None: [SimpleNamespace(brand="Samsung"), SimpleNamespace(brand="Another Brand")]),
				"Brand": SimpleNamespace(name=name, custom_brand_abr="sam"),
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
			flags=SimpleNamespace(),
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

	def test_category_must_match_group(self):
		self.doc.custom_category = "Other"
		self.group.custom_category = "Other"
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def test_preview_does_not_allocate_and_accounts_for_legacy_codes(self):
		self.group.check_permission = MagicMock()
		# Use stable documents so each permission check is exercised.
		documents = {
			"Item Group": self.group,
			"Category": SimpleNamespace(name="Electronics", category_abr="ELE", check_permission=MagicMock(), get=lambda field, default=None: [SimpleNamespace(brand="Samsung")]),
			"Brand": SimpleNamespace(name="Samsung", custom_brand_abr="SAM", check_permission=MagicMock()),
		}
		self.frappe.get_doc.side_effect = lambda doctype, name: documents[doctype]
		self.frappe.db.get_value.return_value = 2
		self.frappe.get_all.return_value = ["ELE-SAM-TV-050", "ELE-SAM-TV-OTHER"]
		self.assertEqual(self.module.preview_item_code("Electronics", "Samsung", "TV"), "ELE-SAM-TV-051")
		self.series.assert_not_called()
		self.frappe.db.sql.assert_not_called()
		for document in documents.values():
			document.check_permission.assert_called_once_with("read")

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

	def test_brand_outside_category_rejected(self):
		self.doc.brand = "Unlisted"
		with self.assertRaises(ValueError):
			self.module.set_item_code(self.doc)
		self.series.assert_not_called()

	def prepare_edit(self, confirmed=None):
		previous = SimpleNamespace(item_code="OLD-001")
		previous.get = lambda field: {"custom_category": "Old", "brand": "Samsung", "item_group": "TV"}.get(field)
		self.doc.is_new = lambda: False
		self.doc.get_doc_before_save = lambda: previous
		self.doc.get = lambda field: confirmed if field == "__coding_confirmed_code" else getattr(self.doc, field, None)
		self.doc.item_code = previous.item_code

	def test_edit_requires_confirmation_without_allocating(self):
		self.prepare_edit()
		with self.assertRaises(ValueError):
			self.module.validate_item_coding(self.doc)
		self.series.assert_not_called()

	def test_confirmed_edit_allocates_and_renames(self):
		self.prepare_edit("ELE-SAM-TV-001")
		self.module.validate_item_coding(self.doc)
		self.assertEqual(self.doc.item_code, "OLD-001")
		self.frappe.rename_doc = MagicMock()
		self.doc.get_all_children = lambda: [self.child]
		self.child = SimpleNamespace(parent="old")
		self.module.rename_updated_item(self.doc)
		self.frappe.rename_doc.assert_called_once_with("Item", "old", "ELE-SAM-TV-001", merge=False)
		self.assertEqual(self.doc.name, "ELE-SAM-TV-001")
		self.assertEqual(self.child.parent, self.doc.name)

	def test_changed_sequence_requires_confirmation_again(self):
		self.prepare_edit("ELE-SAM-TV-001")
		self.series.return_value = "002"
		with self.assertRaises(ValueError):
			self.module.validate_item_coding(self.doc)
		self.assertFalse(hasattr(self.doc.flags, "coding_rename_to"))

	def test_same_prefix_keeps_existing_sequence(self):
		self.prepare_edit()
		previous = self.doc.get_doc_before_save()
		previous.item_code = self.doc.item_code = "ELE-SAM-TV-042"
		self.module.validate_item_coding(self.doc)
		self.series.assert_not_called()

	def test_unrelated_legacy_edit_allowed(self):
		self.prepare_edit()
		self.doc.custom_category = "Old"
		self.module.validate_item_coding(self.doc)
		self.series.assert_not_called()

	def test_direct_code_edit_rejected(self):
		self.prepare_edit()
		self.doc.custom_category = "Old"
		self.doc.item_code = "MANUAL"
		with self.assertRaises(ValueError):
			self.module.validate_item_coding(self.doc)
		self.series.assert_not_called()

	def test_leaf_group_requires_category(self):
		doc = SimpleNamespace(is_group=0, get=lambda field: None)
		with self.assertRaises(ValueError):
			self.module.validate_item_group_category(doc)
		doc.is_group = 1
		self.module.validate_item_group_category(doc)

	def test_insert_has_code_before_standard_naming_and_allocates_only_once(self):
		# Follow the registered hooks, with a standard naming check in between.
		spec = importlib.util.spec_from_file_location(
			"tested_hooks", Path(__file__).parents[1] / "coding/hooks.py"
		)
		hooks = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(hooks)
		self.doc.item_code = None
		before_insert = hooks.doc_events["Item"]["before_insert"].rsplit(".", 1)[1]
		getattr(self.module, before_insert)(self.doc)
		self.assertEqual(self.doc.item_code, "ELE-SAM-TV-001")
		# Frappe clears name; ERPNext derives it from item_code.
		self.doc.name = None
		if not self.doc.item_code:
			raise ValueError("Item Code is required")
		self.doc.name = self.doc.item_code
		autoname = hooks.doc_events["Item"]["autoname"].rsplit(".", 1)[1]
		getattr(self.module, autoname)(self.doc)
		self.assertEqual(self.doc.name, "ELE-SAM-TV-001")
		self.series.assert_called_once_with("ELE-SAM-TV-", 3)

	def test_standard_naming_series_cannot_replace_generated_code(self):
		self.module.set_item_code(self.doc)
		self.doc.item_code = self.doc.name = "STO-ITEM-2026-00001"
		self.module.restore_item_name(self.doc)
		self.assertEqual(self.doc.item_code, "ELE-SAM-TV-001")
		self.assertEqual(self.doc.name, "ELE-SAM-TV-001")
		self.series.assert_called_once()

	def test_restore_without_allocation_keeps_variant_or_existing_name(self):
		self.module.restore_item_name(self.doc)
		self.assertEqual(self.doc.item_code, "COPIED-CODE")
		self.series.assert_not_called()

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
