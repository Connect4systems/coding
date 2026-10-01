app_name = "coding"
app_title = "Coding"
app_publisher = "Connect 4 Systems"
app_description = "Item Code generator"
app_email = "info@connect4systems.com"
app_license = "mit"

required_apps = ["erpnext"]

doc_events = {
	"Item Group": {
		"validate": "coding.item_code.validate_item_group_category",
	},
	"Item": {
		"before_insert": "coding.item_code.set_item_code",
		"autoname": "coding.item_code.restore_item_name",
		"validate": "coding.item_code.validate_item_coding",
		"on_update": "coding.item_code.rename_updated_item",
	},
}

doctype_js = {
	"Item": "public/js/item.js",
}
