app_name = "coding"
app_title = "Coding"
app_publisher = "Connect 4 Systems"
app_description = "Item Code generator"
app_email = "info@connect4systems.com"
app_license = "mit"

required_apps = ["erpnext"]

doc_events = {
	"Item": {"autoname": "coding.item_code.set_item_code"},
}

doctype_js = {
	"Item": "public/js/item.js",
}
