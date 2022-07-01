import re
from typing import Optional, Dict, Set, List
import logging

logger = logging.getLogger(__name__)


TAB = '\t'
DEFAULT_TOC_HEADER = '## Table of Contents\n'

REGEX_HEADER = '^#* (.*?)$'
REGEX_HEADER_WITH_ANCHOR = '.*<a.*class="anchor".*</a>'


class Header:
    def __init__(self, header_line: str):
        self.header_line = header_line  # direct reference to original notebook dict but immutable
        self.level: int = self._parse_level()
        self.text: str = self._parse_text()

    def generate_anchor_tag(self, anchor_id: str) -> str:
        """ generate anchor tag for the header """
        assert not self.has_anchor_tag
        return f'<a class=\"anchor\" id=\"{anchor_id}\"></a>\n'

    @property
    def anchor_id(self) -> Optional[str]:
        return self._parse_anchor_id_from_header_line(self.header_line)

    @property
    def has_anchor_tag(self) -> bool:
        """ check if the header has anchor tag """
        return re.match(REGEX_HEADER_WITH_ANCHOR, self.header_line) is not None

    def get_toc_markdown(self) -> str:
        """
        create a row in Markdown language for the TOC cell
        Example: "* [My Introduction](#introduction)\n",
        """
        toc_line = f'{self.level * TAB} * [{self.text}](#{self.anchor_id})'
        return toc_line

    def _parse_level(self) -> int:
        """
        identify the header level (count of #'s)
        """
        level = self.header_line.find(' ') - 1  # # -> 0, ## -> 1 etc.
        if level == -1:
            raise ValueError(f'Could not parse header level from {self.header_line}')
        return level

    def _parse_anchor_id_from_header_line(self, header_line: str) -> Optional[str]:
        """
        parse anchor id from link
        """
        if not self.has_anchor_tag:
            return None
        anchor_tag = re.findall('<a.*class="anchor".*</a>', header_line)[0]
        anchor_ids = re.findall('id="(.*?)"', anchor_tag)
        if not anchor_ids:
            raise ValueError(f'Could not parse anchor id from {anchor_tag}.')
        return anchor_ids[0]

    def _parse_text(self) -> str:
        """
        parse header text
        """
        if self.anchor_id:
            texts = re.findall('^#* (.*?)<a', self.header_line)
        else:
            texts = re.findall('^#* (.*?)$', self.header_line)
        if not texts:
            raise ValueError(f'Could not parse header text from {self.header_line}.')
        return texts[0].strip()


def line_has_header(line: str) -> bool:
    return re.match(REGEX_HEADER, line) is not None


class HeaderCell:
    def __init__(self, cell: Dict):
        self.cell = cell  # direct reference to original notebook dict
        self.first_line = cell['source'][0]  # direct reference to original notebook dict
        self.header = Header(self.first_line)

    @property
    def has_anchor_tag(self) -> bool:
        return self.header.has_anchor_tag

    @property
    def anchor_id(self) -> str:
        return self.header.anchor_id

    def get_header(self) -> Header:
        return self.header

    def insert_anchor_tag(self, anchor_id_blacklist: Set):
        """generate a missing anchor tag and insert it into the first line
        we have to do this in the cell dictionary as strings are immutable"""
        assert not self.has_anchor_tag
        leading_words = self.header.text.lower().split()[:3]
        anchor_id = '_'.join(leading_words)

        tries = 0
        while anchor_id in anchor_id_blacklist and tries < 50:
            anchor_id += '_' + str(tries)
        anchor_tag = self.header.generate_anchor_tag(anchor_id=anchor_id)
        self.cell['source'][0] = self.first_line.strip() + ' ' + anchor_tag
        self.first_line = self.cell['source'][0]
        self.header = Header(self.first_line)

        logger.info(f'Generated anchor id {anchor_id} for {self.header.text}')


class Notebook:
    """ """
    def __init__(self, notebook_dict: Dict, force_toc_in_first_cell: bool):
        self.notebook: Dict = notebook_dict  # direct reference to original notebook dict
        self.updated = False
        self.header_cells = self._identify_header_cells()
        self.toc_cell = self._identify_toc_cell()
        self.force_toc_in_first_cell = force_toc_in_first_cell
        self.overall_title = self._identify_overall_title()  # optionally skipped for tag creation & toc inserted after

    def _identify_overall_title(self) -> Optional[HeaderCell]:
        """
        find out whether the first notebook cell is a header cell of level 0; return the cell if so
        """
        first_cell = self.notebook['cells'][0]
        if first_cell == self.header_cells[0].cell and self.header_cells[0].header.level == 0:
            return self.header_cells[0]

    def write_toc(self):
        """
        update existing or create new toc cell
        """
        toc_lines = self.generate_new_toc_lines()
        if not toc_lines:
            logger.warning('Skip writing TOC: No TOC Lines found/generated.')
            return

        if self.toc_cell:
            self._update_toc_cell(new_toc_lines=toc_lines)
        else:
            self._insert_toc_cell(new_toc_lines=toc_lines)

    def _update_toc_cell(self, new_toc_lines: List[str]):
        """
        overwrite existing toc cell with new toc lines
        """
        toc_lines = self.toc_cell.cell['source']
        if toc_lines[1:] == new_toc_lines:
            logger.info('Skipping update of TOC: No Changes')
            return

        # remove all but first line (keeping header)
        logger.info(f'Removing {len(toc_lines)-1} old lines from TOC.')
        while len(toc_lines) > 1:
            toc_lines.pop()

        # append new toc lines
        toc_lines.extend(new_toc_lines)
        logger.info(f'Inserted {len(new_toc_lines)} new lines into TOC.')
        self.updated = True

    def _insert_toc_cell(self, new_toc_lines: List[str]):
        """
        insert new toc cell at the top of the notebook
        """
        new_toc_lines.insert(0, DEFAULT_TOC_HEADER)
        logger.debug(f'Used default header for TOC: {DEFAULT_TOC_HEADER}')
        toc_cell = {
            'cell_type': 'markdown',
            'metadata': {},
            'source': new_toc_lines,
        }

        logger.info(f'Generated TOC cell with {len(new_toc_lines)-1} lines.')
        position = 1 if self.overall_title and not self.force_toc_in_first_cell else 0
        logger.debug(f'Inserting TOC cell at position {position}.')
        self.notebook['cells'].insert(position, toc_cell)

        self.updated = True
        self.header_cells = self._identify_header_cells()
        self.toc_cell = self._identify_toc_cell()

    def add_anchor_tags(self):
        """
        add anchor tags to header cells if missing
        """
        # anchor ids must be unique
        current_anchor_ids = {c.anchor_id for c in self.header_cells if c.has_anchor_tag}
        logger.debug(f'Current anchor ids: {current_anchor_ids}')

        header_cells_without_anchor_id = [c for c in self.header_cells if not c.has_anchor_tag
                                          and c is not self.toc_cell
                                          and (c is not self.overall_title or self.force_toc_in_first_cell)]
        logger.debug(f'Header cells without anchor id: {header_cells_without_anchor_id}')
        if not header_cells_without_anchor_id:
            logger.info('No anchor tags missing.')
            return

        for cell in header_cells_without_anchor_id:
            cell.insert_anchor_tag(anchor_id_blacklist=current_anchor_ids)
            logger.debug(f'Added anchor id: {cell.anchor_id} to {cell.header.text}')
            current_anchor_ids.add(cell.anchor_id)
        self.updated = True

    def generate_new_toc_lines(self) -> List[str]:
        """
        create toc line for each header cell with an anchor tag
        """
        header_cells_without_anchor = [c for c in self.header_cells if not c.has_anchor_tag]
        if header_cells_without_anchor:
            first_lines = [c.first_line for c in header_cells_without_anchor]
            logger.warning(f'Skipping Header cells without anchor tag: {first_lines}')

        header_cells_with_anchor = [c for c in self.header_cells if c.has_anchor_tag]
        headers = [c.get_header() for c in header_cells_with_anchor]
        toc_lines = []
        for counter, header in enumerate(headers):
            toc_line = header.get_toc_markdown()
            if counter < len(headers)-1:
                toc_line += '\n'
            toc_lines.append(toc_line)

        logger.info(f"Parsed {len(toc_lines)} header lines for Table of Contents.")
        return toc_lines

    def _identify_header_cells(self) -> List[HeaderCell]:
        """
        identify markdown (as opposed to code) cells with a header (like ##...) in the
        first line
        """
        markdown_cells = [c for c in self.notebook['cells'] if c['cell_type'] == 'markdown']
        code_cells = [c for c in self.notebook['cells'] if c['cell_type'] == 'code']
        other_cells = [c for c in self.notebook['cells'] if c['cell_type'] not in {'markdown', 'code'}]
        logger.info(f'Identified {len(markdown_cells)} markdown, {len(code_cells)} code and '
                    f'{len(other_cells)} other cells.')

        header_cells = [HeaderCell(c) for c in markdown_cells if line_has_header(c['source'][0])]
        header_cells_with_anchor = [c for c in header_cells if c.has_anchor_tag]
        header_cells_without_anchor = [c for c in header_cells if not c.has_anchor_tag]

        logger.info(
            f'Identified {len(header_cells_with_anchor)} header cells with and '
            f'{len(header_cells_without_anchor)} header cells without anchor tag.')
        return header_cells

    def _identify_toc_cell(self) -> Optional[HeaderCell]:
        """
        find a markdown cell that has a TOC header in the first line
        """
        toc_variations = {'toc', 'table of contents', 'table of content', 'inhalt', 'inhaltsverzeichnis'}
        toc_cells = [c for c in self.header_cells if c.header.text.strip().lower() in toc_variations]
        return toc_cells[0] if toc_cells else None
