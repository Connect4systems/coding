### Coding

Item Code generator

## Item code generation

Configure Category and Brand abbreviations. On each leaf Item Group, set
**Item Group abr** and **Category**. In each Category, populate the **Brands** table.

To create an Item, select **Category**, **Brand**, and **Item Group**, enter its
name and other required fields, and save. Select Category first, then a Brand from its Brands table, then a leaf Item Group belonging to that Category. Changing Category clears incompatible selections. Item Code appears automatically once all
three are selected. This is a preview; saving allocates the final sequence safely
and may change the number if another user saves first. The server assigns:

```text
{category_abr}-{brand_abr}-{item_group_abr}-{sequence}
```

For example: `COM-HP-LP-001`, then `COM-HP-LP-002`.
Abbreviations use letters and numbers and are uppercased in the code.
Each prefix has its own transaction-protected counter, starting at `001` and
continuing beyond `999`. Existing codes are considered when initializing the
counter. Item Code is read-only; new non-variant Items always receive an automatic
code, including copied Items and imports. Codes are allocated in `before_insert`,
before naming checks can require Item Code, and retained through `autoname`. Existing Items use the same filtering when changing selections. Saving a combination with a different code prefix shows an old-code ? new-code confirmation. Cancelling stops the save and keeps the original code. Confirming allocates the new sequence and renames the Item with Frappe, updating linked records in the same transaction. If another save consumes the previewed code, the save stops and asks for confirmation again. Unchanged prefixes retain their existing sequence. Unrelated edits to legacy Items retain their codes.
Variants retain ERPNext's normal variant naming.

Category owns the Brands table. Legacy Item Group Brand data is retained for historical review and is not used for new Item codes.

### Updating an existing site

```bash
bench --site YOUR_SITE migrate
bench build --app coding
bench --site YOUR_SITE clear-cache
```

Restart the server processes with `bench restart` after deploying Python hook changes,
then reload the browser after updating. Migration restores Category on Item Group and adds the Category Brands table. Populate each Category?s Brands table and assign each leaf Item Group to its Category before creating Items or changing existing Item selections. Existing relationships are not guessed; stored Category values are preserved where available.

### Local checks

```bash
python -m unittest discover -s tests
```

These isolated tests cover code generation with mocked Frappe services. Run a
site-level smoke test after migration to check the forms, permissions, and
concurrent inserts against your installed ERPNext version.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app coding
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/coding
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
