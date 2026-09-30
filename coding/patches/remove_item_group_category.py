import frappe


def execute():
	# Preserve stored columns while removing obsolete form fields.
	for fieldname in ("custom_category", "custom_brand"):
		name = "Item Group-" + fieldname
		if frappe.db.exists("Custom Field", name):
			frappe.delete_doc("Custom Field", name, ignore_permissions=True)
	frappe.clear_cache(doctype="Item Group")
