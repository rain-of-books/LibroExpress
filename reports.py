"""
Módulo de reportes de ventas y exportación a CSV, Excel y PDF.
"""

import csv
import importlib
from datetime import date, datetime
from typing import Dict, List

from sales import IVA_RATE


def _parse_sale_date(sale_date: str) -> date:
    return datetime.fromisoformat(sale_date).date()


def build_sales_report_rows(sales, start_date: date, end_date: date) -> List[Dict]:
    """Construye filas detalladas por producto vendido dentro del rango de fechas."""
    rows: List[Dict] = []

    for sale in sales:
        sale_date = _parse_sale_date(sale.created_at)
        if sale_date < start_date or sale_date > end_date:
            continue

        for item in sale.items:
            iva_amount = round(item.subtotal * IVA_RATE)
            rows.append(
                {
                    "sale_id": sale.id,
                    "date": sale_date.isoformat(),
                    "client": sale.client_name or "No especificado",
                    "document": sale.client_document or "No especificado",
                    "product": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                    "iva": iva_amount,
                    "total_with_iva": item.subtotal + iva_amount,
                    "payment_method": sale.payment_method,
                }
            )

    return rows


def summarize_sales_rows(rows: List[Dict]) -> Dict:
    """Calcula resumen general para visualización y exportaciones."""
    net_total = sum(row["subtotal"] for row in rows)
    iva_total = round(net_total * IVA_RATE)
    gross_total = net_total + iva_total
    sale_ids = {row["sale_id"] for row in rows}

    return {
        "lines": len(rows),
        "sales": len(sale_ids),
        "net_total": net_total,
        "iva_total": iva_total,
        "gross_total": gross_total,
    }


def export_sales_report_csv(rows: List[Dict], file_path: str) -> None:
    """Exporta el reporte detallado a CSV."""
    summary = summarize_sales_rows(rows)

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ID Venta",
                "Fecha",
                "Cliente",
                "Documento",
                "Producto",
                "Cantidad",
                "Precio Unitario",
                "Subtotal",
                "IVA",
                "Total con IVA",
                "Método Pago",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row["sale_id"],
                    row["date"],
                    row["client"],
                    row["document"],
                    row["product"],
                    row["quantity"],
                    row["unit_price"],
                    row["subtotal"],
                    row["iva"],
                    row["total_with_iva"],
                    row["payment_method"],
                ]
            )

        writer.writerow([])
        writer.writerow(["RESUMEN"])
        writer.writerow(["Ventas", summary["sales"]])
        writer.writerow(["Líneas", summary["lines"]])
        writer.writerow(["Subtotal", summary["net_total"]])
        writer.writerow(["IVA", summary["iva_total"]])
        writer.writerow(["TOTAL GENERAL CON IVA", summary["gross_total"]])


def export_sales_report_excel(rows: List[Dict], file_path: str) -> None:
    """Exporta el reporte detallado a Excel (.xlsx)."""
    summary = summarize_sales_rows(rows)

    try:
        workbook_module = importlib.import_module("openpyxl")
        Workbook = workbook_module.Workbook
    except ImportError as error:
        raise ImportError("openpyxl no está instalado. Ejecute: pip install openpyxl") from error

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reporte Ventas"

    headers = [
        "ID Venta",
        "Fecha",
        "Cliente",
        "Documento",
        "Producto",
        "Cantidad",
        "Precio Unitario",
        "Subtotal",
        "IVA",
        "Total con IVA",
        "Método Pago",
    ]
    sheet.append(headers)

    # Encabezados con estilo para mejorar legibilidad.
    header_fill = workbook_module.styles.PatternFill(fill_type="solid", fgColor="1F4E78")
    thin_side = workbook_module.styles.Side(border_style="thin", color="D9D9D9")
    header_border = workbook_module.styles.Border(
        left=thin_side,
        right=thin_side,
        top=thin_side,
        bottom=thin_side,
    )
    header_alignment = workbook_module.styles.Alignment(horizontal="center", vertical="center", wrap_text=True)

    for cell in sheet[1]:
        cell.font = workbook_module.styles.Font(bold=True)
        cell.fill = header_fill
        cell.border = header_border
        cell.alignment = header_alignment

    for row in rows:
        sheet.append(
            [
                row["sale_id"],
                row["date"],
                row["client"],
                row["document"],
                row["product"],
                row["quantity"],
                row["unit_price"],
                row["subtotal"],
                row["iva"],
                row["total_with_iva"],
                row["payment_method"],
            ]
        )

    sheet.append([])
    sheet.append(["RESUMEN"])
    sheet.append(["Ventas", summary["sales"]])
    sheet.append(["Líneas", summary["lines"]])
    sheet.append(["Subtotal", summary["net_total"]])
    sheet.append(["IVA", summary["iva_total"]])
    sheet.append(["TOTAL GENERAL CON IVA", summary["gross_total"]])

    # Formato de tabla: filtros, congelación, alineación y bordes.
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:K{max(1, 1 + len(rows))}"

    text_alignment = workbook_module.styles.Alignment(horizontal="left", vertical="center")
    number_alignment = workbook_module.styles.Alignment(horizontal="right", vertical="center")
    body_border = workbook_module.styles.Border(
        left=thin_side,
        right=thin_side,
        top=thin_side,
        bottom=thin_side,
    )

    # Aplicar estilo de celdas al bloque principal del reporte.
    for row_idx in range(2, 2 + len(rows)):
        for col_idx in range(1, 12):
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.border = body_border
            cell.alignment = number_alignment if col_idx in (6, 7, 8, 9, 10) else text_alignment

    # Dar formato visual a la fila final de total general.
    total_row_idx = sheet.max_row
    for col_idx in range(1, 3):
        total_cell = sheet.cell(row=total_row_idx, column=col_idx)
        total_cell.font = workbook_module.styles.Font(bold=True)
        total_cell.fill = workbook_module.styles.PatternFill(fill_type="solid", fgColor="E2F0D9")
        total_cell.border = body_border
        total_cell.alignment = number_alignment if col_idx == 2 else text_alignment

    # Ajuste de ancho por columna según contenido visible.
    min_width_by_col = {
        "A": 16,
        "B": 12,
        "C": 22,
        "D": 14,
        "E": 24,
        "F": 10,
        "G": 14,
        "H": 14,
        "I": 12,
        "J": 16,
        "K": 14,
    }
    max_width = 34

    for column_cells in sheet.columns:
        column_letter = column_cells[0].column_letter
        max_length = 0
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))

        computed_width = max(max_length + 2, min_width_by_col.get(column_letter, 12))
        sheet.column_dimensions[column_letter].width = min(computed_width, max_width)

    # Formato numérico de moneda/entero para columnas financieras.
    money_format = '#,##0'
    for row_idx in range(2, 2 + len(rows)):
        sheet[f"G{row_idx}"].number_format = money_format
        sheet[f"H{row_idx}"].number_format = money_format
        sheet[f"I{row_idx}"].number_format = money_format
        sheet[f"J{row_idx}"].number_format = money_format

    # Formato numérico del total general.
    sheet[f"B{total_row_idx}"].number_format = money_format

    workbook.save(file_path)


def export_sales_report_pdf(rows: List[Dict], file_path: str, title: str, period_label: str) -> None:
    """Exporta el reporte detallado a PDF."""
    try:
        pagesizes_module = importlib.import_module("reportlab.lib.pagesizes")
        units_module = importlib.import_module("reportlab.lib.units")
        pdfmetrics_module = importlib.import_module("reportlab.pdfbase.pdfmetrics")
        canvas_module = importlib.import_module("reportlab.pdfgen.canvas")
        A4 = pagesizes_module.A4
        landscape = pagesizes_module.landscape
        cm = units_module.cm
        pdfmetrics = pdfmetrics_module
        canvas = canvas_module
    except ImportError as error:
        raise ImportError("reportlab no está instalado. Ejecute: pip install reportlab") from error

    def fit_text(text: str, font_name: str, font_size: int, max_width: float) -> str:
        """Recorta texto para que entre dentro del ancho de su columna."""
        value = "" if text is None else str(text)
        if pdfmetrics.stringWidth(value, font_name, font_size) <= max_width:
            return value

        ellipsis = "..."
        trimmed = value
        while trimmed and pdfmetrics.stringWidth(trimmed + ellipsis, font_name, font_size) > max_width:
            trimmed = trimmed[:-1]
        return (trimmed + ellipsis) if trimmed else ellipsis

    pdf = canvas.Canvas(file_path, pagesize=landscape(A4))
    width, height = landscape(A4)

    y = height - 1.5 * cm
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(1.5 * cm, y, title)

    y -= 0.7 * cm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(1.5 * cm, y, f"Periodo: {period_label}")

    left_margin = 1.5 * cm
    right_margin = 1.5 * cm
    table_width = width - left_margin - right_margin

    # Distribución de columnas acorde al contenido esperado.
    columns = [
        {"key": "sale_id", "label": "Venta", "width": 0.10, "align": "left"},
        {"key": "date", "label": "Fecha", "width": 0.09, "align": "left"},
        {"key": "client", "label": "Cliente", "width": 0.13, "align": "left"},
        {"key": "product", "label": "Producto", "width": 0.18, "align": "left"},
        {"key": "quantity", "label": "Cant", "width": 0.06, "align": "right"},
        {"key": "unit_price", "label": "P. Unit", "width": 0.10, "align": "right"},
        {"key": "subtotal", "label": "Subtotal", "width": 0.10, "align": "right"},
        {"key": "iva", "label": "IVA", "width": 0.08, "align": "right"},
        {"key": "total_with_iva", "label": "Total", "width": 0.12, "align": "right"},
        {"key": "payment_method", "label": "Pago", "width": 0.14, "align": "left"},
    ]

    running_x = left_margin
    for col in columns:
        col["width_abs"] = col["width"] * table_width
        col["x_start"] = running_x
        col["x_end"] = running_x + col["width_abs"]
        running_x += col["width_abs"]

    y -= 0.8 * cm
    header_font = "Helvetica-Bold"
    header_size = 9

    # Cabecera de tabla con fondo para mejorar contraste.
    header_top = y + 0.28 * cm
    header_bottom = y - 0.34 * cm
    pdf.saveState()
    pdf.setFillColorRGB(0.12, 0.31, 0.47)
    pdf.rect(left_margin, header_bottom, table_width, header_top - header_bottom, stroke=0, fill=1)
    pdf.restoreState()

    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont(header_font, header_size)
    for col in columns:
        label = fit_text(col["label"], header_font, header_size, col["width_abs"] - 4)
        if col["align"] == "right":
            pdf.drawRightString(col["x_end"] - 2, y, label)
        else:
            pdf.drawString(col["x_start"] + 2, y, label)

    # Líneas verticales de cabecera.
    pdf.setStrokeColorRGB(0.8, 0.8, 0.8)
    for col in columns:
        pdf.line(col["x_start"], header_bottom, col["x_start"], header_top)
    pdf.line(width - right_margin, header_bottom, width - right_margin, header_top)

    y -= 0.4 * cm
    pdf.line(left_margin, y, width - right_margin, y)

    body_font = "Helvetica"
    body_size = 8
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont(body_font, body_size)
    for row in rows:
        y -= 0.5 * cm
        if y < 1.5 * cm:
            pdf.showPage()
            y = height - 1.8 * cm

            # Redibujar encabezado al cambiar de página.
            header_top = y + 0.82 * cm
            header_bottom = y + 0.30 * cm
            pdf.saveState()
            pdf.setFillColorRGB(0.12, 0.31, 0.47)
            pdf.rect(left_margin, header_bottom, table_width, header_top - header_bottom, stroke=0, fill=1)
            pdf.restoreState()

            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont(header_font, header_size)
            for col in columns:
                label = fit_text(col["label"], header_font, header_size, col["width_abs"] - 4)
                if col["align"] == "right":
                    pdf.drawRightString(col["x_end"] - 2, y + 0.6 * cm, label)
                else:
                    pdf.drawString(col["x_start"] + 2, y + 0.6 * cm, label)

            pdf.setStrokeColorRGB(0.8, 0.8, 0.8)
            for col in columns:
                pdf.line(col["x_start"], header_bottom, col["x_start"], header_top)
            pdf.line(width - right_margin, header_bottom, width - right_margin, header_top)
            pdf.line(left_margin, y + 0.35 * cm, width - right_margin, y + 0.35 * cm)

            pdf.setFillColorRGB(0, 0, 0)
            pdf.setFont(body_font, body_size)

        row_values = {
            "sale_id": row["sale_id"],
            "date": row["date"],
            "client": row["client"],
            "product": row["product"],
            "quantity": str(row["quantity"]),
            "unit_price": f"{row['unit_price']:,.0f}",
            "subtotal": f"{row['subtotal']:,.0f}",
            "iva": f"{row['iva']:,.0f}",
            "total_with_iva": f"{row['total_with_iva']:,.0f}",
            "payment_method": row["payment_method"],
        }

        for col in columns:
            value = fit_text(row_values[col["key"]], body_font, body_size, col["width_abs"] - 4)
            if col["align"] == "right":
                pdf.drawRightString(col["x_end"] - 2, y, value)
            else:
                pdf.drawString(col["x_start"] + 2, y, value)

        # Rejilla horizontal para separar filas.
        pdf.setStrokeColorRGB(0.9, 0.9, 0.9)
        pdf.line(left_margin, y - 0.12 * cm, width - right_margin, y - 0.12 * cm)

    summary = summarize_sales_rows(rows)
    y -= 1.0 * cm
    if y < 2.2 * cm:
        pdf.showPage()
        y = height - 2.0 * cm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(1.5 * cm, y, f"Ventas: {summary['sales']} | Líneas: {summary['lines']}")
    y -= 0.6 * cm
    pdf.drawString(
        1.5 * cm,
        y,
        f"Subtotal: {summary['net_total']:,.0f}  IVA: {summary['iva_total']:,.0f}  Total con IVA: {summary['gross_total']:,.0f}",
    )

    pdf.save()
