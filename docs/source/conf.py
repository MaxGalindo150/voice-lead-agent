# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Voice Lead Agent'
copyright = '2025, Maximiliano Galindo'
author = 'Maximiliano Galindo'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',          # Generar documentación automáticamente desde docstrings
    'sphinx.ext.napoleon',         # Soporte para estilos Google y NumPy en docstrings
    'sphinx.ext.autodoc.typehints',# Incluir anotaciones de tipos en la documentación
    'sphinx.ext.viewcode',         # Agregar enlaces al código fuente
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']
