import frappe


def execute():
	# Remove the form field; keep its stored column for historical data.
	if frappe.db.exists("Custom Field", "Item Group-custom_brand"):
		frappe.delete_doc("Custom Field", "Item Group-custom_brand", ignore_permissions=True)
	frappe.clear_cache(doctype="Item Group")
