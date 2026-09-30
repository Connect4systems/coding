frappe.ui.form.on("Item", {
	setup(frm) {
		frm.set_query("item_group", () => ({
			filters: { is_group: 0, custom_category: frm.doc.custom_category || "" },
		}));
	},

	refresh(frm) {
		if (frm.is_new() && !frm.doc.variant_of) {
			// ERPNext can change this requirement based on Stock Settings.
			frm.toggle_reqd("item_code", false);
		}
	},

	custom_category(frm) {
		if (frm.is_new()) return frm.set_value("item_group", null);
	},
});
