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


def get_code_prefix(category, brand, item_group, check_permissions=False):
	if not item_group:
		frappe.throw(_("Select an Item Group before saving the Item."))

	group = frappe.get_doc("Item Group", item_group)
	if group.is_group:
		frappe.throw(_("Select a leaf Item Group, not a parent group."))
	if not category or not brand:
		frappe.throw(_("Select Category and Brand before saving the Item."))

	category = frappe.get_doc("Category", category)
	brand = frappe.get_doc("Brand", brand)
	if check_permissions:
		for document in (group, category, brand):
			document.check_permission("read")
	if group.custom_category != category.name:
		frappe.throw(_("Item Group must belong to the selected Category."))
	if brand.name not in [row.brand for row in category.get("brands", [])]:
		frappe.throw(_("Brand must belong to the selected Category's Brand table."))
	return (
		"-".join(
			(
				_abbreviation(category.category_abr, _("Category")),
				_abbreviation(brand.custom_brand_abr, _("Brand")),
				_abbreviation(group.custom_item_group_abr, _("Item Group")),
			)
		)
		+ "-"
	)


def preview_item_code(category, brand, item_group):
	"""Read-only preview; the final number is allocated in the save transaction."""
	prefix = get_code_prefix(category, brand, item_group, check_permissions=True)
	# Series has no modified column; override Frappe's default ordering.
	current = int(frappe.db.get_value("Series", prefix, "current", order_by="name") or 0)
	codes = frappe.get_all("Item", filters={"item_code": ["like", prefix + "%"]}, pluck="item_code")
	numbers = [int(code[len(prefix) :]) for code in codes if code[len(prefix) :].isdigit()]
	return prefix + f"{max([current, *numbers]) + 1:03d}"


def set_item_code(doc, method=None):
	"""Allocate the code before naming or validation can require Item Code."""
	if not doc.is_new() or doc.get("variant_of"):
		return
	prefix = get_code_prefix(doc.custom_category, doc.brand, doc.item_group)

	code = allocate_item_code(prefix)
	doc.item_code = doc.name = code
	doc.flags.coding_item_code = code


def allocate_item_code(prefix):
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

	return code


def validate_item_coding(doc, method=None):
	if doc.get("variant_of"):
		return
	previous = doc.get_doc_before_save()
	fields = ("custom_category", "brand", "item_group")
	changed = previous and any(doc.get(field) != previous.get(field) for field in fields)
	# Do not block unrelated edits to legacy items awaiting category setup.
	if not doc.is_new() and not changed:
		if previous and doc.item_code != previous.item_code:
			frappe.throw(_("Item Code is generated automatically and cannot be edited directly."))
		return
	prefix = get_code_prefix(doc.custom_category, doc.brand, doc.item_group)
	if changed:
		if re.fullmatch(re.escape(prefix) + r"\d{3,}", previous.item_code or ""):
			doc.item_code = previous.item_code
			return
		confirmed = doc.get("__coding_confirmed_code")
		if not confirmed or not re.fullmatch(re.escape(prefix) + r"\d{3,}", confirmed):
			frappe.throw(_("Confirm the new Item Code before saving these selections."))
		code = allocate_item_code(prefix)
		if code != confirmed:
			frappe.throw(_("The next Item Code has changed. Save again to confirm the new code."))
		doc.flags.coding_rename_to = code
		doc.item_code = previous.item_code


def validate_item_group_category(doc, method=None):
	if not doc.is_group and not doc.get("custom_category"):
		frappe.throw(_("Select a Category for this leaf Item Group."))


def rename_updated_item(doc, method=None):
	code = getattr(doc.flags, "coding_rename_to", None)
	if not code:
		return
	frappe.rename_doc("Item", doc.name, code, merge=False)
	frappe.db.set_value("Item", code, "item_code", code, update_modified=False)
	doc.name = doc.item_code = code
	for child in doc.get_all_children():
		child.parent = code
	doc.flags.coding_rename_to = None


def restore_item_name(doc, method=None):
	"""Keep ERPNext naming from replacing the code allocated before insert."""
	code = getattr(doc.flags, "coding_item_code", None)
	if doc.is_new() and not doc.get("variant_of") and code:
		doc.item_code = doc.name = code
