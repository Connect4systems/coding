import frappe

from coding.item_code import BRAND_DOCTYPE, ITEM_GROUP_DOCTYPE, make_item_code


@frappe.whitelist()
def get_brands(category):
	if not category:
		return []

	return frappe.get_all(
		BRAND_DOCTYPE,
		filters={"category": category},
		fields=["name", "brand_abr"],
		order_by="name asc",
	)


@frappe.whitelist()
def get_item_groups(category, brand):
	if not category or not brand:
		return []

	return frappe.get_all(
		ITEM_GROUP_DOCTYPE,
		filters={"category": category, "brand": brand},
		fields=["name", "item_group_abr"],
		order_by="name asc",
	)


@frappe.whitelist()
def generate_item_code(category, brand, item_group):
	return make_item_code(category, brand, item_group)