import re

import frappe
from frappe import _
from frappe.model.naming import getseries


def _abbreviation(value, label):
	value = (value or "").strip().upper()
	if not value:
		frappe.throw(_("{0} abbreviation is required.").format(label))
	if not re.fullmatch(r"[A-Z0-9]+", value):
		frappe.throw(_("{0} abbreviation may contain only letters and numbers.").format(label))
	return value


def set_item_code(doc, method=None):
	"""Name new Items from their Item Group, within the insert transaction."""
	if not doc.is_new() or doc.get("variant_of"):
		return
	if not doc.item_group:
		frappe.throw(_("Select an Item Group before saving the Item."))

	group = frappe.get_doc("Item Group", doc.item_group)
	if group.is_group:
		frappe.throw(_("Select a leaf Item Group, not a parent group."))
	if not group.custom_category or not group.custom_brand:
		frappe.throw(
			_("Set Category and Brand in Item Group {0} before creating an Item.").format(group.name)
		)

	category = frappe.get_doc("Category", group.custom_category)
	brand = frappe.get_doc("Brand", group.custom_brand)
	prefix = (
		"-".join(
			(
				_abbreviation(category.category_abr, _("Category")),
				_abbreviation(brand.custom_brand_abr, _("Brand")),
				_abbreviation(group.custom_item_group_abr, _("Item Group")),
			)
		)
		+ "-"
	)

	# Frappe locks the series counter until the Item transaction completes.
	sequence = getseries(prefix, 3)
	if sequence == "001":
		# Continue from legacy codes, including sequences with gaps.
		codes = frappe.get_all("Item", filters={"item_code": ["like", prefix + "%"]}, pluck="item_code")
		numbers = [int(code[len(prefix) :]) for code in codes if code[len(prefix) :].isdigit()]
		if numbers:
			frappe.db.sql("UPDATE `tabSeries` SET `current`=%s WHERE `name`=%s", (max(numbers), prefix))
			sequence = getseries(prefix, 3)
	code = prefix + sequence
	while frappe.db.exists("Item", code):
		code = prefix + getseries(prefix, 3)

	doc.custom_category = group.custom_category
	doc.brand = group.custom_brand
	doc.item_code = doc.name = code
