import frappe

from coding.item_code import preview_item_code


@frappe.whitelist()
def get_item_code_preview(category, brand, item_group):
	frappe.has_permission("Item", "create", throw=True)
	return preview_item_code(category, brand, item_group)
