function set_item_link_queries(frm) {
	const item_group_field = frappe.meta.get_docfield("Item", "item_group", frm.doc.name);
	if (item_group_field) {
		item_group_field.link_filters = null;
	}

		frm.set_query("brand", () => ({
			query: "coding.api.get_brands",
			filters: { category: frm.doc.custom_category },
		}));

		frm.set_query("item_group", () => ({
			query: "coding.api.get_item_groups",
			filters: {
				category: frm.doc.custom_category,
				brand: frm.doc.brand,
			},
		}));
}

frappe.ui.form.on("Item", {
	setup(frm) {
		set_item_link_queries(frm);
	},

	onload(frm) {
		set_item_link_queries(frm);
	},

	custom_category(frm) {
		frm.set_value("brand", null);
		frm.set_value("item_group", null);
	},

	brand(frm) {
		frm.set_value("item_group", null);
	},
});