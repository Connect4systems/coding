frappe.ui.form.on("Item", {
	setup(frm) {
		frm.set_query("item_group", () => ({ filters: { is_group: 0 } }));
	},

	async item_group(frm) {
		if (!frm.is_new() || frm.doc.variant_of) return;
		const item_group = frm.doc.item_group;
		if (!item_group) {
			await frm.set_value({ custom_category: null, brand: null });
			return;
		}
		const response = await frappe.db.get_value("Item Group", item_group, [
			"custom_category",
			"custom_brand",
		]);
		if (frm.doc.item_group !== item_group || !frm.is_new()) return;
		await frm.set_value({
			custom_category: response.message.custom_category || null,
			brand: response.message.custom_brand || null,
		});
	},
});
