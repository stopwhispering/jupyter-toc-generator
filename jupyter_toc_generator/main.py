import json
import logging

from jupyter_toc_generator.notebook import Notebook
from jupyter_toc_generator.util import copy_to_clipboard, parse_arguments, setup_logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    args = parse_arguments()
    setup_logging(args.log_level)

    with open(args.file) as f:
        notebook_dict = json.load(f)

    notebook = Notebook(notebook_dict=notebook_dict,
                        force_toc_in_first_cell=args.force_toc_in_first_cell)

    if not args.skip_anchor_tags:
        notebook.add_anchor_tags()

    if not args.skip_write_toc:
        notebook.write_toc()

    if notebook.updated:
        print(f'Saving updates to {args.file}')
        with open(args.file, 'w') as f:
            f.write(json.dumps(notebook_dict))
    else:
        print('No changes to be saved.')

    if args.clipboard:
        print(f'Copying Table of Contents Markdown to clipboard.')
        toc_lines = notebook.generate_new_toc_lines()
        copy_to_clipboard(toc_lines)