from pathlib import Path
from typing import List
from argparse import ArgumentParser, Namespace
import logging

from jupyter_toc_generator.notebook import DEFAULT_TOC_HEADER


def copy_to_clipboard(toc_lines: List[str]):
    """
    note that pyperclip doesn't do unicode on windows
    install via "pip install pyperclip
    """
    import pyperclip  # lazy import optional dependency
    toc_lines.insert(0, DEFAULT_TOC_HEADER)
    one_line = ''.join(toc_lines)
    pyperclip.copy(one_line)


def parse_arguments() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('file',
                        type=Path,
                        help='Jupyter Notebook file to process')
    parser.add_argument('-l', '--log_level',
                        help='Set Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
                        default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument('-sa', '--skip_anchor_tags',
                        help="Don't add anchor tags to header cells if missing.",
                        action='store_true')  # sets default to False
    parser.add_argument('-sw', '--skip_write_toc',
                        help="Don't Update TOC directly in notebook or insert if missing.",
                        action='store_true')  # sets default to False
    parser.add_argument('-f', '--force_toc_in_first_cell',
                        help="If inserting missing TOC, don't skip overall title cell but always insert into"
                             "first cell.",
                        action='store_true')  # sets default to False
    parser.add_argument('-c', '--clipboard',
                        help='Copy generated TOC to clipboard.',
                        action='store_true')  # sets default to False
    return parser.parse_args()


def setup_logging(log_level: str):
    logging.getLogger().setLevel(log_level)
