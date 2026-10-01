import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	# Restore the category field without guessing relationships for existing data.
	create_custom_fields({"Item Group": [{
		"fieldname": "custom_category",
		"fieldtype": "Link",
		"options": "Category",
		"label": "Category",
		"insert_after": "item_group_name",
		"mandatory_depends_on": "eval:!doc.is_group",
		"in_standard_filter": 1,
	}]})
	frappe.clear_cache(doctype="Item Group")
