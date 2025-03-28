#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
カスタムUIウィジェットモジュール
テーブルモデルなどの特殊なUIコンポーネントを提供します
"""

from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize

class DataTableModel(QAbstractTableModel):
    """
    分析結果を表示するためのテーブルモデル
    """
    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else []
        self._headers = []
        
        # データがDataFrameの場合、ヘッダーとデータを取得
        if hasattr(data, 'columns'):
            self._headers = list(data.columns)
            self._data = data.values.tolist()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers) if self._headers else (len(self._data[0]) if self._data else 0)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            try:
                return str(self._data[index.row()][index.column()])
            except (IndexError, TypeError):
                return None
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                return self._headers[section]
            except IndexError:
                return str(section + 1)
                
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)
            
        return None
    
    def setData(self, data):
        """
        テーブルのデータを更新します
        
        引数:
            data: 表示するデータ（DataFrameまたはリスト）
        """
        # pandas DataFrameの場合
        if hasattr(data, 'columns'):
            self._headers = list(data.columns)
            self._data = data.values.tolist()
        else:
            self._data = data
        
        # モデルが変更されたことを通知
        self.layoutChanged.emit()


class ResultTableView(QTableView):
    """
    結果表示用のカスタムテーブルビュー
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 外観設定
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        self.setSortingEnabled(False)
        
        # 選択動作
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        
        # サイズ調整
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(28)
    
    def sizeHint(self):
        """
        推奨サイズを返します
        """
        return QSize(800, 400)