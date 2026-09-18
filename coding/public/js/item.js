frappe.ui.form.on("Item", {
	setup(frm) {
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
	},

	custom_category(frm) {
		frm.set_value("brand", null);
		frm.set_value("item_group", null);
	},

	brand(frm) {
		frm.set_value("item_group", null);
	},
});