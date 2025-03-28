#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF生成モジュール
分析結果をPDF形式で出力します
"""

import logging
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .file_parser import filter_ascii_only

def generate_pdf_report(file_path, result_data, autosleep_data=None, hrv_data=None):
    """
    分析結果をPDF形式で出力します
    
    引数:
        file_path (str): 出力するPDFファイルのパス
        result_data (pandas.DataFrame): 出力する分析結果データ
        autosleep_data (pandas.DataFrame): 原データ（AutoSleep）- 使用しない
        hrv_data (dict): 原データ（HRV）- 使用しない
    """
    try:
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # 最大表示行数
        MAX_ROWS = 30
        
        # タイトル
        title = Paragraph("Sleep and HRV Analysis Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # 結果テーブル（ASCII文字のみ）
        if result_data is not None and not result_data.empty:
            elements.append(Paragraph("Analysis Results", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            # 非ASCII文字をフィルタリング
            filtered_data = result_data.applymap(filter_ascii_only)
            
            # テーブルデータの作成
            table_data = [list(filtered_data.columns)]
            
            # 最大表示行数までのデータを追加
            display_rows = min(len(filtered_data), MAX_ROWS)
            for i in range(display_rows):
                table_data.append(list(filtered_data.iloc[i]))
            
            # テーブル作成
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            
            # 表示されていないデータに関する情報
            if len(filtered_data) > MAX_ROWS:
                not_shown_info = Paragraph(
                    f"Note: Showing {display_rows} of {len(filtered_data)} rows. {len(filtered_data) - display_rows} rows are not displayed.",
                    styles['Italic']
                )
                elements.append(Spacer(1, 10))
                elements.append(not_shown_info)
        
        # PDF生成
        doc.build(elements)
        logging.info(f"PDFレポートを生成しました: {file_path}")
        
    except Exception as e:
        logging.error(f"PDF生成エラー: {str(e)}")
        raise