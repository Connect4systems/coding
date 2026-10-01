import re

import frappe

from coding.item_code import get_code_prefix, preview_item_code


@frappe.whitelist()
def get_item_code_preview(category, brand, item_group, item=None):
	if item:
		doc = frappe.get_doc("Item", item)
		doc.check_permission("write")
		prefix = get_code_prefix(category, brand, item_group, check_permissions=True)
		if re.fullmatch(re.escape(prefix) + r"\d{3,}", doc.item_code or ""):
			return doc.item_code
	else:
		frappe.has_permission("Item", "create", throw=True)
	return preview_item_code(category, brand, item_group)


@frappe.whitelist()
def get_category_brands(category):
	doc = frappe.get_doc("Category", category)
	doc.check_permission("read")
	return list(dict.fromkeys(row.brand for row in doc.get("brands", []) if row.brand))
