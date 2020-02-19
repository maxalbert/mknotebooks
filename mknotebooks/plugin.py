import mkdocs, pathlib, os, re, warnings
from mkdocs.structure.files import Files
from traitlets.config import Config
from nbconvert import MarkdownExporter
import nbformat

here = os.path.dirname(os.path.abspath(__file__))


def get_line_indentation_depth(line: str):
    """
    Return the number of spaces at the beginning of the line.
    """
    initial_spaces = re.match("^( *)", line).group(1)
    return len(initial_spaces)


def get_paragraph_indentation_depth(input_str):
    """
    Return the minimum common indentation depth of all lines in the input string.
    """
    lines = input_str.split("\n")
    non_empty_lines = [l for l in lines if l != ""]
    return min([get_line_indentation_depth(line) for line in non_empty_lines])


def is_indented_markdown_code_block(input_str):
    """
    Returns True if each line in the input string is indented with
    at least four spaces, indicating a markdown code block.
    """
    return get_paragraph_indentation_depth(input_str) >= 4


def remove_leading_indentation(input_str):
    """
    Remove the leading four spaces of each line in the input string and return the result.
    """
    lines = input_str.split("\n")
    dedented_lines = [l[4:] if l != "" else l for l in lines]
    return "\n".join(dedented_lines)


def is_pandas_dataframe_div(input_str):
    """
    Return True if the input string contains a HTML table
    representing a pandas dataframe, otherwise return False.
    """
    m = re.match('^<div>.*<table .*class="dataframe">.*</table>.*</div>$', input_str.strip(), re.DOTALL)
    return m is not None


def wrap_as_jupyter_input_cell(input_str):
    return f"<div class='jupyterInputCell'>\n{input_str}\n</div>"


def wrap_as_jupyter_output_cell(input_str):
    """

    """
    if is_indented_markdown_code_block(input_str):
        return f"<div class='jupyterOutputCell'>\n```\n{remove_leading_indentation(input_str)}\n```\n</div>"
    elif is_pandas_dataframe_div(input_str):
        return input_str
    else:
        warnings.warn("[WWW] Warning! Not a regular indented markdown code block!!")
        return input_str


class NotebookFile(mkdocs.structure.files.File):
    """
    Wraps a regular File object to make ipynb files appear as
    valid documentation files.
    """

    def __init__(self, file, use_directory_urls, site_dir, **kwargs):
        self.file = file
        self.dest_path = self._get_dest_path(use_directory_urls)
        self.abs_dest_path = os.path.normpath(os.path.join(site_dir, self.dest_path))
        self.url = self._get_url(use_directory_urls)

    def __getattr__(self, item):
        return self.file.__getattribute__(item)

    def is_documentation_page(self):
        return True


class Plugin(mkdocs.plugins.BasePlugin):
    config_scheme = (
        ("execute", mkdocs.config.config_options.Type(bool, default=False)),
        ("preamble", mkdocs.config.config_options.FilesystemObject()),
        ("timeout", mkdocs.config.config_options.Type(int)),
        ("write_markdown", mkdocs.config.config_options.Type(bool, default=False)),
    )

    def on_config(self, config):
        c = Config()
        if self.config["execute"]:
            if self.config["preamble"]:
                default_preprocessors = MarkdownExporter.default_preprocessors.default_args[
                    0
                ]
                default_preprocessors.insert(
                    default_preprocessors.index(
                        "nbconvert.preprocessors.ExecutePreprocessor"
                    ),
                    "nbconvert_utils.ExecuteWithPreamble",
                )
                c.default_preprocessors = default_preprocessors
                c.ExecutePreprocessor.timeout = self.config["timeout"]
                c.ExecuteWithPreamble.enabled = True
                c.ExecuteWithPreamble.preamble_scripts = [self.config["preamble"]]
            else:
                c.Executor.enabled = True

        template_file = os.path.join(here, "templates", "custom_markdown.tpl")
        exporter = MarkdownExporter(config=c, template_file=template_file)
        exporter.register_filter("wrap_as_jupyter_output_cell", wrap_as_jupyter_output_cell)
        exporter.register_filter("wrap_as_jupyter_input_cell", wrap_as_jupyter_input_cell)

        config["notebook_exporter"] = exporter
        return config

    def on_files(self, files, config):
        files = Files(
            [
                NotebookFile(f, **config)
                if str(f.abs_src_path).endswith("ipynb")
                else f
                for f in files
            ]
        )
        return files

    def on_page_read_source(self, _, page, config):
        print(page)
        if str(page.file.abs_src_path).endswith("ipynb"):
            with open(page.file.abs_src_path) as nbin:
                nb = nbformat.read(nbin, 4)

            exporter = config["notebook_exporter"]
            body, resources = exporter.from_notebook_node(nb)

            if self.config["write_markdown"]:
                pathlib.Path(page.file.abs_dest_path).parent.mkdir(
                    parents=True, exist_ok=True
                )
                with open(
                    pathlib.Path(page.file.abs_src_path).with_suffix(".md.tmp"), "w"
                ) as fout:
                    fout.write(body)
            for fname, content in resources["outputs"].items():
                pathlib.Path(page.file.abs_dest_path).parent.mkdir(
                    parents=True, exist_ok=True
                )
                with open(
                    pathlib.Path(page.file.abs_dest_path).parent / fname, "wb"
                ) as fout:
                    fout.write(content)
            return body
        return None
