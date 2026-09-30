import frappe


def execute():
	ambiguous_item_groups = []
	if frappe.db.table_exists("Brand Table"):
		rows = frappe.get_all(
			"Brand Table",
			filters={"parenttype": "Item Group", "parentfield": "custom_brands"},
			fields=["parent", "brand"],
			order_by="parent asc, idx asc",
		)
		brands_by_item_group = {}
		for row in rows:
			brands_by_item_group.setdefault(row.parent, set()).add(row.brand)

		for item_group, brands in brands_by_item_group.items():
			if len(brands) == 1:
				frappe.db.set_value("Item Group", item_group, "custom_brand", next(iter(brands)))
			elif len(brands) > 1:
				ambiguous_item_groups.append(item_group)

	if ambiguous_item_groups:
		frappe.log_error(
			"\n".join(sorted(ambiguous_item_groups)),
			"Item Groups with multiple legacy brands need review",
		)

	for custom_field in ("Brand-custom_categories", "Item Group-custom_brands"):
		if frappe.db.exists("Custom Field", custom_field):
			frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True)