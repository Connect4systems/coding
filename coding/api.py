import frappe

from coding.item_code import BRAND_DOCTYPE, ITEM_GROUP_DOCTYPE, make_item_code


@frappe.whitelist()
def get_brands(doctype=None, txt="", searchfield=None, start=0, page_len=20, filters=None):
	filters = frappe.parse_json(filters or {})
	category = filters.get("category")
	if not category:
		return []

	brands = frappe.get_all(BRAND_DOCTYPE, fields=["name"], order_by="name asc")
	return [
		[brand.name, brand.name]
		for brand in brands
		if (not txt or txt.lower() in brand.name.lower())
		and any(row.category == category for row in frappe.get_doc(BRAND_DOCTYPE, brand.name).custom_categories)
	][int(start) : int(start) + int(page_len)]


@frappe.whitelist()
def get_item_groups(doctype=None, txt="", searchfield=None, start=0, page_len=20, filters=None):
	filters = frappe.parse_json(filters or {})
	category = filters.get("category")
	brand = filters.get("brand")
	if not category or not brand:
		return []

	item_groups = frappe.get_all(
		ITEM_GROUP_DOCTYPE,
		filters={"custom_category": category},
		fields=["name"],
		order_by="name asc",
	)
	return [
		[item_group.name, item_group.name]
		for item_group in item_groups
		if (not txt or txt.lower() in item_group.name.lower())
		and any(row.brand == brand for row in frappe.get_doc(ITEM_GROUP_DOCTYPE, item_group.name).custom_brands)
	][int(start) : int(start) + int(page_len)]


@frappe.whitelist()
def generate_item_code(category, brand, item_group):
	return make_item_code(category, brand, item_group)