function configure_item_coding(frm) {
	if (frm.doc.variant_of) return;
	frm.set_df_property("item_code", "hidden", 0);
	frm.set_df_property("item_code", "depends_on", "");
	frm.set_df_property("item_code", "read_only", 1);
	frm.toggle_reqd("item_code", false);
	frm.set_query("item_group", () => ({ filters: { is_group: 0 } }));
}

async function update_item_code(frm) {
	if (!frm.is_new() || frm.doc.variant_of) return;
	configure_item_coding(frm);
	const request = (frm.coding_request || 0) + 1;
	frm.coding_request = request;
	const { custom_category: category, brand, item_group } = frm.doc;
	await frm.set_value("item_code", "");
	if (!category || !brand || !item_group) return;
	const response = await frappe.call({
		method: "coding.api.get_item_code_preview",
		args: { category, brand, item_group },
	});
	if (request !== frm.coding_request || !frm.is_new()) return;
	if (category !== frm.doc.custom_category || brand !== frm.doc.brand || item_group !== frm.doc.item_group) return;
	await frm.set_value("item_code", response.message);
}

frappe.ui.form.on("Item", {
	setup: configure_item_coding,
	refresh(frm) {
		configure_item_coding(frm);
		return update_item_code(frm);
	},
	custom_category: update_item_code,
	brand: update_item_code,
	item_group: update_item_code,
	async validate(frm) {
		// Await a preview even when Save is clicked immediately after selection.
		await update_item_code(frm);
	},
});
