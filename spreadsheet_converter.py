"""Spreadsheet conversion without the pandas runtime dependency.

UwUConverter focuses on cell values rather than workbook formatting.  The
converter therefore uses the native readers/writers for each supported format
instead of routing everything through pandas.  Besides reducing package size,
this avoids importing a large data-science stack for simple file conversion.
"""
import csv
import datetime as _datetime
import math
import pathlib
import re


_INVALID_EXCEL_SHEET_CHARS = re.compile(r"[\\/*?:\[\]]")


def convert_spreadsheet(
    file_path,
    output_file_path,
    output_format,
):
    output_format = str(output_format).lower()
    sheets = read_spreadsheet(file_path)

    if output_format == "csv":
        _write_delimited(
            output_file_path,
            _first_sheet(sheets),
            ",",
        )

    elif output_format == "tsv":
        _write_delimited(
            output_file_path,
            _first_sheet(sheets),
            "\t",
        )

    elif output_format == "xlsx":
        save_as_xlsx(
            sheets,
            output_file_path,
        )

    elif output_format == "ods":
        save_as_ods(
            sheets,
            output_file_path,
        )

    elif output_format == "xls":
        save_as_xls(
            sheets,
            output_file_path,
        )

    elif output_format == "pdf":
        save_as_pdf(
            sheets,
            output_file_path,
        )

    else:
        raise ValueError(
            "Unsupported spreadsheet output format: "
            + output_format
        )


def read_spreadsheet(file_path):
    extension = pathlib.Path(file_path).suffix.lower()

    if extension == ".csv":
        return {
            "Sheet1": _read_delimited(
                file_path,
                ",",
            )
        }

    if extension == ".tsv":
        return {
            "Sheet1": _read_delimited(
                file_path,
                "\t",
            )
        }

    if extension in {".xlsx", ".xlsm"}:
        return _read_xlsx(file_path)

    if extension == ".xls":
        return _read_xls(file_path)

    if extension == ".ods":
        return _read_ods(file_path)

    if extension == ".xlsb":
        return _read_xlsb(file_path)

    raise ValueError(
        "Unsupported spreadsheet input format: "
        + extension
    )


def _read_delimited(file_path, delimiter):
    with pathlib.Path(file_path).open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as stream:
        return [
            list(row)
            for row in csv.reader(
                stream,
                delimiter=delimiter,
            )
        ]


def _write_delimited(file_path, rows, delimiter):
    with pathlib.Path(file_path).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        writer = csv.writer(
            stream,
            delimiter=delimiter,
        )

        for row in rows:
            writer.writerow(
                [
                    "" if _is_blank(value) else value
                    for value in row
                ]
            )


def _read_xlsx(file_path):
    from openpyxl import load_workbook

    workbook = load_workbook(
        filename=file_path,
        read_only=True,
        data_only=True,
    )

    try:
        sheets = {}

        for worksheet in workbook.worksheets:
            sheets[worksheet.title] = [
                list(row)
                for row in worksheet.iter_rows(
                    values_only=True
                )
            ]

        return sheets

    finally:
        workbook.close()


def _read_xls(file_path):
    import xlrd

    workbook = xlrd.open_workbook(file_path)
    sheets = {}

    for worksheet in workbook.sheets():
        rows = []

        for row_index in range(worksheet.nrows):
            rows.append(
                [
                    _xlrd_cell_value(
                        worksheet.cell(
                            row_index,
                            column_index,
                        ),
                        workbook,
                        xlrd,
                    )
                    for column_index in range(
                        worksheet.ncols
                    )
                ]
            )

        sheets[worksheet.name] = rows

    return sheets


def _xlrd_cell_value(cell, workbook, xlrd):
    if cell.ctype in {
        xlrd.XL_CELL_EMPTY,
        xlrd.XL_CELL_BLANK,
    }:
        return None

    if cell.ctype == xlrd.XL_CELL_DATE:
        try:
            return xlrd.xldate.xldate_as_datetime(
                cell.value,
                workbook.datemode,
            )
        except Exception:
            return cell.value

    if cell.ctype == xlrd.XL_CELL_BOOLEAN:
        return bool(cell.value)

    if cell.ctype == xlrd.XL_CELL_ERROR:
        return xlrd.error_text_from_code.get(
            cell.value,
            "#ERROR",
        )

    return cell.value


def _read_xlsb(file_path):
    from pyxlsb import open_workbook

    sheets = {}

    with open_workbook(str(file_path)) as workbook:
        for sheet_name in workbook.sheets:
            with workbook.get_sheet(sheet_name) as worksheet:
                sheets[sheet_name] = [
                    [
                        cell.v
                        for cell in row
                    ]
                    for row in worksheet.rows()
                ]

    return sheets


def _read_ods(file_path):
    from odf import teletype
    from odf.namespaces import TABLENS
    from odf.opendocument import load
    from odf.table import Table, TableRow

    document = load(str(file_path))
    sheets = {}

    cell_names = {
        (TABLENS, "table-cell"),
        (TABLENS, "covered-table-cell"),
    }

    for table in document.spreadsheet.getElementsByType(Table):
        sheet_name = table.getAttribute("name") or "Sheet"
        rows = []

        for row in table.getElementsByType(TableRow):
            values = []

            for cell in row.childNodes:
                if getattr(cell, "qname", None) not in cell_names:
                    continue

                repeated = _safe_repeat_count(
                    cell.getAttribute(
                        "numbercolumnsrepeated"
                    )
                )
                value = _ods_cell_value(
                    cell,
                    teletype,
                )
                values.extend(
                    [value] * repeated
                )

            row_repeat = _safe_repeat_count(
                row.getAttribute(
                    "numberrowsrepeated"
                )
            )

            for _ in range(row_repeat):
                rows.append(list(values))

        sheets[sheet_name] = _trim_empty_edges(rows)

    return sheets


def _safe_repeat_count(value):
    try:
        return max(1, min(int(value or 1), 16384))
    except (TypeError, ValueError):
        return 1


def _ods_cell_value(cell, teletype):
    value_type = cell.getAttribute("valuetype")
    text = teletype.extractText(cell)

    if value_type in {
        "float",
        "currency",
        "percentage",
    }:
        raw = cell.getAttribute("value")
        try:
            number = float(raw)
            return (
                int(number)
                if number.is_integer()
                else number
            )
        except (TypeError, ValueError):
            return text

    if value_type == "boolean":
        raw = str(
            cell.getAttribute("booleanvalue")
        ).lower()
        return raw == "true"

    if value_type == "date":
        raw = cell.getAttribute("datevalue")
        if raw:
            try:
                return _datetime.datetime.fromisoformat(raw)
            except ValueError:
                return raw

    if value_type == "time":
        return cell.getAttribute("timevalue") or text

    return text or None


def _trim_empty_edges(rows):
    while rows and all(
        _is_blank(value)
        for value in rows[-1]
    ):
        rows.pop()

    if not rows:
        return []

    max_width = max(
        (
            len(row)
            for row in rows
        ),
        default=0,
    )

    while max_width > 0 and all(
        len(row) < max_width
        or _is_blank(row[max_width - 1])
        for row in rows
    ):
        max_width -= 1

    return [
        list(row[:max_width])
        for row in rows
    ]


def save_as_xlsx(sheets, output_file_path):
    from openpyxl import Workbook

    workbook = Workbook(write_only=True)
    used_names = set()

    for sheet_name, rows in sheets.items():
        worksheet = workbook.create_sheet(
            _safe_sheet_name(
                sheet_name,
                used_names,
            )
        )

        for row in rows:
            worksheet.append(
                [
                    None if _is_blank(value) else value
                    for value in row
                ]
            )

    if not workbook.worksheets:
        workbook.create_sheet("Sheet1")

    workbook.save(output_file_path)


def save_as_ods(sheets, output_file_path):
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    document = OpenDocumentSpreadsheet()

    for sheet_name, rows in sheets.items():
        table = Table(
            name=str(sheet_name) or "Sheet"
        )

        for row in rows:
            table_row = TableRow()

            for value in row:
                cell = _make_ods_cell(
                    value,
                    TableCell,
                    P,
                )
                table_row.addElement(cell)

            table.addElement(table_row)

        document.spreadsheet.addElement(table)

    document.save(str(output_file_path))


def _make_ods_cell(value, TableCell, P):
    if _is_blank(value):
        return TableCell()

    if isinstance(value, bool):
        cell = TableCell(
            valuetype="boolean",
            booleanvalue=(
                "true" if value else "false"
            ),
        )

    elif isinstance(value, (int, float)):
        cell = TableCell(
            valuetype="float",
            value=str(value),
        )

    elif isinstance(value, (_datetime.datetime, _datetime.date)):
        cell = TableCell(
            valuetype="date",
            datevalue=value.isoformat(),
        )

    else:
        cell = TableCell(
            valuetype="string"
        )

    cell.addElement(
        P(text=_display_value(value))
    )
    return cell


def save_as_xls(sheets, output_file_path):
    import xlwt

    workbook = xlwt.Workbook()
    used_names = set()

    for sheet_name, rows in sheets.items():
        worksheet = workbook.add_sheet(
            _safe_sheet_name(
                sheet_name,
                used_names,
            )
        )

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                if _is_blank(value):
                    value = ""

                worksheet.write(
                    row_index,
                    column_index,
                    value,
                )

    workbook.save(output_file_path)


def save_as_pdf(sheets, output_file_path):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()

    document = SimpleDocTemplate(
        str(output_file_path),
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    elements = []

    for sheet_name, rows in sheets.items():
        elements.append(
            Paragraph(
                str(sheet_name),
                styles["Heading2"],
            )
        )

        table_data = [
            [
                _display_value(value)
                for value in row
            ]
            for row in rows
        ]

        if not table_data:
            table_data = [[""]]

        table = Table(
            table_data,
            repeatRows=(
                1 if table_data else 0
            ),
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 18))

    document.build(elements)


def _first_sheet(sheets):
    try:
        return next(iter(sheets.values()))
    except StopIteration:
        return []


def _safe_sheet_name(name, used_names):
    base = _INVALID_EXCEL_SHEET_CHARS.sub(
        "_",
        str(name or "Sheet"),
    ).strip("'")[:31]
    base = base or "Sheet"
    candidate = base
    number = 2

    while candidate.casefold() in used_names:
        suffix = f" ({number})"
        candidate = (
            base[: 31 - len(suffix)]
            + suffix
        )
        number += 1

    used_names.add(candidate.casefold())
    return candidate


def _is_blank(value):
    if value is None:
        return True

    if isinstance(value, float):
        return math.isnan(value)

    return False


def _display_value(value):
    if _is_blank(value):
        return ""

    if isinstance(value, _datetime.datetime):
        return value.isoformat(sep=" ")

    if isinstance(value, _datetime.date):
        return value.isoformat()

    return str(value)
