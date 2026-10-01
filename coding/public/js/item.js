function configure_item_coding(frm) {
	if (frm.doc.variant_of) return;
	frm.set_df_property("item_code", "hidden", 0);
	frm.set_df_property("item_code", "depends_on", "");
	frm.set_df_property("item_code", "read_only", 1);
	frm.toggle_reqd("item_code", false);
	frm.set_query("brand", () => ({ filters: { name: ["in", frm.coding_brands || []] } }));
	frm.set_query("item_group", () => ({ filters: {
		is_group: 0, custom_category: frm.doc.custom_category || "",
	} }));
	frm.set_df_property("brand", "read_only", !frm.doc.custom_category);
	frm.set_df_property("item_group", "read_only", !frm.doc.custom_category || !frm.doc.brand);
}

async function load_category_brands(frm) {
	const category = frm.doc.custom_category;
	frm.coding_brands = [];
	if (!category) return;
	const response = await frappe.call({
		method: "coding.api.get_category_brands", args: { category },
	});
	if (category === frm.doc.custom_category) frm.coding_brands = response.message || [];
}

async function update_item_code(frm) {
	if (frm.doc.variant_of) return;
	configure_item_coding(frm);
	delete frm.doc.__coding_confirmed_code;
	const request = (frm.coding_request || 0) + 1;
	frm.coding_request = request;
	const { custom_category: category, brand, item_group } = frm.doc;
	if (frm.is_new()) await frm.set_value("item_code", "");
	if (!category || !brand || !item_group) return;
	const response = await frappe.call({
		method: "coding.api.get_item_code_preview",
		args: { category, brand, item_group, item: frm.is_new() ? null : frm.doc.name },
	});
	if (request !== frm.coding_request) return;
	if (category !== frm.doc.custom_category || brand !== frm.doc.brand || item_group !== frm.doc.item_group) return;
	if (frm.is_new()) await frm.set_value("item_code", response.message);
	return response.message;
}

frappe.ui.form.on("Item", {
	setup: configure_item_coding,
	async refresh(frm) {
		configure_item_coding(frm);
		if (!frm.is_dirty()) {
			frm.coding_saved_selections = [frm.doc.custom_category, frm.doc.brand, frm.doc.item_group];
		}
		await load_category_brands(frm);
		if (frm.is_new()) await update_item_code(frm);
	},
	async custom_category(frm) {
		if (frm.doc.variant_of) return;
		delete frm.doc.__coding_confirmed_code;
		frm.coding_request = (frm.coding_request || 0) + 1;
		configure_item_coding(frm);
		const category = frm.doc.custom_category;
		await load_category_brands(frm);
		if (category !== frm.doc.custom_category) return;
		if (frm.doc.brand && !frm.coding_brands.includes(frm.doc.brand)) await frm.set_value("brand", "");
		if (frm.doc.item_group) {
			const group = frm.doc.item_group;
			const result = await frappe.db.get_value("Item Group", group, "custom_category");
			if (category !== frm.doc.custom_category) return;
			if (group === frm.doc.item_group && (!category || result.message.custom_category !== category)) {
				await frm.set_value("item_group", "");
			}
		}
		return update_item_code(frm);
	},
	brand: update_item_code,
	item_group: update_item_code,
	async validate(frm) {
		if (frm.doc.variant_of) return;
		const selections = [frm.doc.custom_category, frm.doc.brand, frm.doc.item_group];
		if (!frm.is_new() && frm.coding_saved_selections &&
			selections.every((value, index) => value === frm.coding_saved_selections[index])) return;
		if (selections.some((value) => !value)) {
			frappe.throw(__("Select Category, Brand and Item Group before saving."));
		}
		const code = await update_item_code(frm);
		if (!code) frappe.throw(__("Selections changed while checking the Item Code. Save again."));
		if (frm.is_new() || code === frm.doc.item_code) return;
		const confirmed = await new Promise((resolve) => frappe.confirm(
			__("Rename Item from {0} to {1}?", [
				frappe.utils.escape_html(frm.doc.item_code), frappe.utils.escape_html(code),
			]), () => resolve(true), () => resolve(false),
		));
		if (!confirmed) {
			frappe.validated = false;
			return;
		}
		if (!selections.every((value, index) => value === [frm.doc.custom_category, frm.doc.brand, frm.doc.item_group][index])) {
			frappe.throw(__("Selections changed. Save again to confirm the new Item Code."));
		}
		frm.doc.__coding_confirmed_code = code;
	},
});
