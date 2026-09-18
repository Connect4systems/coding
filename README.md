### Coding

Item Code generator

## Item code generation

The app adds cascading Item selectors and generates an Item code during
`before_validate`:

```text
{category_abr}-{brand_abr}-{item_group_abr}-{sequence}
```

The implementation expects these fields:

- `Category.category_abr`
- `Brand.custom_categories`, `Brand.custom_brand_abr`
- `Item Group.custom_category`, `Item Group.custom_brands`, `Item Group.custom_item_group_abr`
- `Item.custom_category`, `Item.brand`, and the standard `Item.item_group`

Brands are filtered by category. Item groups are filtered by both category and
brand. The sequence starts at `001` for each three-part prefix and is assigned
only when `item_code` is empty.

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
