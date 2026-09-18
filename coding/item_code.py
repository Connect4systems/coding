import re

import frappe
from frappe import _


CATEGORY_DOCTYPE = "Category"
BRAND_DOCTYPE = "Brand"
ITEM_GROUP_DOCTYPE = "Item Group"
ITEM_DOCTYPE = "Item"


def _abbreviation(value, label):
	value = (value or "").strip().upper()
	if not value:
		frappe.throw(_(f"{label} abbreviation is required."))
	if not re.fullmatch(r"[A-Z0-9]+", value):
		frappe.throw(_(f"{label} abbreviation may contain only letters and numbers."))
	return value


def _get_code_parts(category, brand, item_group):
	category_doc = frappe.get_doc(CATEGORY_DOCTYPE, category)
	brand_doc = frappe.get_doc(BRAND_DOCTYPE, brand)
	item_group_doc = frappe.get_doc(ITEM_GROUP_DOCTYPE, item_group)

	if not any(row.category == category for row in brand_doc.custom_categories):
		frappe.throw(_("The selected brand does not belong to the selected category."))
	if item_group_doc.custom_category != category or not any(
		row.brand == brand for row in item_group_doc.custom_brands
	):
		frappe.throw(_("The selected item group does not belong to the selected category and brand."))

	return (
		_abbreviation(category_doc.category_abr, "Category"),
		_abbreviation(brand_doc.custom_brand_abr, "Brand"),
		_abbreviation(item_group_doc.custom_item_group_abr, "Item group"),
	)


def _next_sequence(prefix):
	last_code = frappe.db.sql(
		f"""
		SELECT item_code
		FROM `tab{ITEM_DOCTYPE}`
		WHERE item_code LIKE %s
		ORDER BY item_code DESC
		LIMIT 1
		""",
		(prefix + "-%") ,
		as_dict=False,
	)

	last_number = 0
	if last_code:
		match = re.search(r"-(\d{3})$", last_code[0][0])
		if match:
			last_number = int(match.group(1))

	next_number = last_number + 1
	if next_number > 999:
		frappe.throw(_("The item-code sequence limit of 999 has been reached."))

	return next_number


def make_item_code(category, brand, item_group):
	category_abr, brand_abr, item_group_abr = _get_code_parts(category, brand, item_group)
	prefix = f"{category_abr}-{brand_abr}-{item_group_abr}"
	sequence = _next_sequence(prefix)
	item_code = f"{prefix}-{sequence:03d}"

	if frappe.db.exists(ITEM_DOCTYPE, item_code):
		frappe.throw(_("The next item code already exists. Please try again."))

	return item_code


def set_item_code(doc, method=None):
	if doc.item_code or not (doc.custom_category and doc.brand and doc.item_group):
		return

	doc.item_code = make_item_code(doc.custom_category, doc.brand, doc.item_group)