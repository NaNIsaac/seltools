project = "seltools"
author = "Isaac Yong"
copyright = "2026, Isaac Yong"
release = "0.2.0"

extensions = ["sphinx.ext.doctest", "sphinx.ext.intersphinx"]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "more-itertools": ("https://more-itertools.readthedocs.io/en/stable", None),
}
default_role = "any"
templates_path = ["_templates"]
html_static_path = ["_static"]
html_theme = "python_docs_theme"
html_title = "seltools documentation"
# keep the breadcrumb on this project instead of linking to python.org
html_theme_options = {
    "root_name": "seltools",
    "root_url": "index.html",
    "root_icon": "seltools.svg",
    "root_icon_alt_text": "seltools",
    "root_include_title": False,
}
