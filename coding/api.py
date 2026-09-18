import frappe
from frappe.desk.search import search_link as frappe_search_link

from coding.item_code import BRAND_DOCTYPE, ITEM_GROUP_DOCTYPE, make_item_code


@frappe.whitelist()
def get_brands(doctype=None, txt="", searchfield=None, start=0, page_len=20, filters=None):
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
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
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	category = filters.get("category")
	brand = filters.get("brand")
	if not category or not brand:
		return []

	item_groups = frappe.get_all(
		ITEM_GROUP_DOCTYPE,
		filters={"custom_category": category, "is_group": 0},
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


@frappe.whitelist()
def search_link(
	txt="",
	doctype=None,
	reference_doctype=None,
	ignore_user_permissions=False,
	query=None,
	filters=None,
	page_length=10,
	searchfield=None,
):
	"""Handle legacy Item Group filters from cached Item form scripts."""
	parsed_filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	if doctype == ITEM_GROUP_DOCTYPE and parsed_filters.get("category") and parsed_filters.get("brand"):
		groups = get_item_groups(
			doctype=doctype,
			txt=txt,
			start=0,
			page_len=page_length,
			filters={
				"category": parsed_filters["category"],
				"brand": parsed_filters["brand"],
			},
		)
		return [{"value": group[0], "description": group[1]} for group in groups]

	return frappe_search_link(
		txt=txt,
		doctype=doctype,
		reference_doctype=reference_doctype,
		ignore_user_permissions=ignore_user_permissions,
		query=query,
		filters=filters,
		page_length=page_length,
		searchfield=searchfield,
	)