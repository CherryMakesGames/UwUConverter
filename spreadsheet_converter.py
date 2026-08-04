import pathlib

import pandas as pd
import xlwt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle
)


def convert_spreadsheet(
    file_path,
    output_file_path,
    output_format
):
    sheets = read_spreadsheet(file_path)

    if output_format == "csv":
        first_sheet = next(iter(sheets.values()))
        first_sheet.to_csv(
            output_file_path,
            index=False
        )

    elif output_format == "tsv":
        first_sheet = next(iter(sheets.values()))
        first_sheet.to_csv(
            output_file_path,
            index=False,
            sep="\t"
        )

    elif output_format == "xlsx":
        with pd.ExcelWriter(
            output_file_path,
            engine="openpyxl"
        ) as writer:
            write_sheets(writer, sheets)

    elif output_format == "ods":
        with pd.ExcelWriter(
            output_file_path,
            engine="odf"
        ) as writer:
            write_sheets(writer, sheets)

    elif output_format == "xls":
        save_as_xls(
            sheets,
            output_file_path
        )

    elif output_format == "pdf":
        save_as_pdf(
            sheets,
            output_file_path
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
            "Sheet1": pd.read_csv(file_path)
        }

    if extension == ".tsv":
        return {
            "Sheet1": pd.read_csv(
                file_path,
                sep="\t"
            )
        }

    engines = {
        ".xlsx": "openpyxl",
        ".xlsm": "openpyxl",
        ".xls": "xlrd",
        ".ods": "odf",
        ".xlsb": "pyxlsb"
    }

    engine = engines.get(extension)

    if engine is None:
        raise ValueError(
            "Unsupported spreadsheet input format: "
            + extension
        )

    return pd.read_excel(
        file_path,
        sheet_name=None,
        engine=engine
    )


def write_sheets(writer, sheets):
    for sheet_name, dataframe in sheets.items():
        dataframe.to_excel(
            writer,
            sheet_name=str(sheet_name)[:31],
            index=False
        )


def save_as_xls(sheets, output_file_path):
    workbook = xlwt.Workbook()

    for sheet_name, dataframe in sheets.items():
        safe_name = str(sheet_name)[:31] or "Sheet"
        worksheet = workbook.add_sheet(safe_name)

        for column_index, column_name in enumerate(
            dataframe.columns
        ):
            worksheet.write(
                0,
                column_index,
                str(column_name)
            )

        for row_index, row in enumerate(
            dataframe.itertuples(index=False),
            start=1
        ):
            for column_index, value in enumerate(row):
                if pd.isna(value):
                    value = ""

                worksheet.write(
                    row_index,
                    column_index,
                    value
                )

    workbook.save(output_file_path)


def save_as_pdf(sheets, output_file_path):
    styles = getSampleStyleSheet()

    document = SimpleDocTemplate(
        output_file_path,
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    elements = []

    for sheet_name, dataframe in sheets.items():
        elements.append(
            Paragraph(
                str(sheet_name),
                styles["Heading2"]
            )
        )

        table_data = [
            [
                str(column)
                for column in dataframe.columns
            ]
        ]

        for row in dataframe.itertuples(index=False):
            table_data.append(
                [
                    ""
                    if pd.isna(value)
                    else str(value)
                    for value in row
                ]
            )

        table = Table(
            table_data,
            repeatRows=1
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7
                    )
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 18))

    document.build(elements)
