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
		frm.set_value("item_code", null);
	},

	brand(frm) {
		frm.set_value("item_group", null);
		frm.set_value("item_code", null);
	},

	item_group(frm) {
		frm.set_value("item_code", null);
		if (!frm.doc.custom_category || !frm.doc.brand || !frm.doc.item_group) {
			return;
		}

		frappe.call({
			method: "coding.api.generate_item_code",
			args: {
				category: frm.doc.custom_category,
				brand: frm.doc.brand,
				item_group: frm.doc.item_group,
			},
			head: false,
			callback(response) {
				if (response.message && !frm.doc.item_code) {
					frm.set_value("item_code", response.message);
				}
			},
		});
	},
});