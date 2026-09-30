from coding.patches.remove_legacy_brand_category_fields import execute as remove_legacy_fields


def execute():
	# Also upgrade sites that already ran the original cleanup patch.
	remove_legacy_fields()
