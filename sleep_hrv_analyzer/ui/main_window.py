#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
アプリケーションのメインウィンドウ
UIレイアウトとイベントハンドラを定義します
"""

import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QMessageBox, QFrame, QSplitter, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from utils.pdf_generator import generate_pdf_report
from data_processor import process_sleep_hrv_data
from .widgets import DataTableModel, ResultTableView


class WorkerSignals(QObject):
    """
    バックグラウンド処理ワーカー用のシグナル
    """
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)


class DataProcessWorker(QThread):
    """
    データ処理をバックグラウンドで実行するワーカー
    """
    def __init__(self, sleep_file, hrv_file):
        super().__init__()
        self.sleep_file = sleep_file
        self.hrv_file = hrv_file
        self.signals = WorkerSignals()
    
    def run(self):
        """
        スレッド実行時に呼び出されるメソッド
        """
        try:
            result = process_sleep_hrv_data(
                self.sleep_file, 
                self.hrv_file,
                self.signals.progress.emit
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class PdfExportWorker(QThread):
    """
    PDF出力をバックグラウンドで実行するワーカー
    """
    def __init__(self, file_path, result_data, autosleep_data, hrv_data):
        super().__init__()
        self.file_path = file_path
        self.result_data = result_data
        self.autosleep_data = autosleep_data
        self.hrv_data = hrv_data
        self.signals = WorkerSignals()
    
    def run(self):
        """
        スレッド実行時に呼び出されるメソッド
        """
        try:
            self.signals.progress.emit(10)
            generate_pdf_report(
                self.file_path,
                self.result_data,
                self.autosleep_data,
                self.hrv_data
            )
            self.signals.progress.emit(100)
            self.signals.finished.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ
    """
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.setWindowTitle("睡眠・HRVデータ分析")
        self.setGeometry(100, 100, 1000, 600)
        
        # データ保持用変数
        self.sleep_file = None
        self.hrv_file = None
        self.result_data = None
        self.autosleep_data = None
        self.hrv_data = None
        
        # UIの初期化
        self.init_ui()
        
        # ステータスバーの初期化
        self.statusBar().showMessage("準備完了")
    
    def init_ui(self):
        """
        UIコンポーネントの初期化
        """
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # コントロールエリア
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        
        # ファイル選択ボタン
        btn_select_sleep = QPushButton("AutoSleepファイル選択", self)
        btn_select_sleep.clicked.connect(self.select_sleep_file)
        control_layout.addWidget(btn_select_sleep)
        
        btn_select_hrv = QPushButton("HRVファイル選択", self)
        btn_select_hrv.clicked.connect(self.select_hrv_file)
        control_layout.addWidget(btn_select_hrv)
        
        # 実行ボタン
        btn_analyze = QPushButton("分析実行", self)
        btn_analyze.clicked.connect(self.analyze_data)
        control_layout.addWidget(btn_analyze)
        
        # PDF出力ボタン
        btn_export_pdf = QPushButton("PDF出力", self)
        btn_export_pdf.clicked.connect(self.export_pdf)
        control_layout.addWidget(btn_export_pdf)
        
        main_layout.addWidget(control_frame)
        
        # ステータス表示
        self.status_label = QLabel("ファイルを選択してください", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # プログレスバー
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 結果テーブル
        self.result_table = ResultTableView(self)
        self.table_model = DataTableModel()
        self.result_table.setModel(self.table_model)
        main_layout.addWidget(self.result_table)
    
    def select_sleep_file(self):
        """
        AutoSleepファイルの選択ダイアログを表示
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "AutoSleepファイル選択", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.sleep_file = file_path
            file_name = os.path.basename(file_path)
            self.status_label.setText(f"AutoSleepファイル: {file_name}")
            self.statusBar().showMessage(f"AutoSleepファイルを選択しました: {file_path}")
    
    def select_hrv_file(self):
        """
        HRVファイルの選択ダイアログを表示
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "HRVファイル選択", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.hrv_file = file_path
            file_name = os.path.basename(file_path)
            self.status_label.setText(f"HRVファイル: {file_name}")
            self.statusBar().showMessage(f"HRVファイルを選択しました: {file_path}")
    
    def analyze_data(self):
        """
        データ分析を実行
        """
        if not self.sleep_file or not self.hrv_file:
            QMessageBox.warning(self, "エラー", "両方のファイルを選択してください")
            return
        
        # プログレスバーの表示
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("分析中...")
        
        # バックグラウンドでのデータ処理
        self.worker = DataProcessWorker(self.sleep_file, self.hrv_file)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.finished.connect(self.process_complete)
        self.worker.signals.error.connect(self.process_error)
        self.worker.start()
    
    def update_progress(self, value):
        """
        進捗状況の更新
        """
        self.progress_bar.setValue(value)
    
    def process_complete(self, result):
        """
        データ処理完了時の処理
        """
        self.result_data, self.autosleep_data, self.hrv_data = result
        
        # テーブルモデルの更新
        self.table_model.setData(self.result_data)
        
        # カラム幅の調整
        for i in range(len(self.result_data.columns)):
            self.result_table.setColumnWidth(i, 150)
        
        # 処理完了表示
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"分析完了: {len(self.result_data)}件のデータを処理しました")
        self.statusBar().showMessage("分析完了")
    
    def process_error(self, error_msg):
        """
        データ処理エラー時の処理
        """
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "エラー", f"分析中にエラーが発生しました: {error_msg}")
        self.status_label.setText("エラーが発生しました")
        self.statusBar().showMessage("エラー")
    
    def export_pdf(self):
        """
        分析結果をPDFとして出力
        """
        if self.result_data is None or len(self.result_data) == 0:
            QMessageBox.warning(self, "エラー", "分析結果がありません。まず分析を実行してください。")
            return
        
        # 保存ファイル選択ダイアログ
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF出力先を選択", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            # プログレスバーの表示
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.status_label.setText("PDF出力中...")
            
            # バックグラウンドでのPDF生成
            self.pdf_worker = PdfExportWorker(
                file_path, 
                self.result_data,
                self.autosleep_data,
                self.hrv_data
            )
            self.pdf_worker.signals.progress.connect(self.update_progress)
            self.pdf_worker.signals.finished.connect(self.pdf_export_complete)
            self.pdf_worker.signals.error.connect(self.pdf_export_error)
            self.pdf_worker.start()
    
    def pdf_export_complete(self, result):
        """
        PDF出力完了時の処理
        """
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "成功", "PDFの出力が完了しました")
        self.status_label.setText("PDF出力完了")
        self.statusBar().showMessage("PDF出力完了")
    
    def pdf_export_error(self, error_msg):
        """
        PDF出力エラー時の処理
        """
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "エラー", f"PDF生成中にエラーが発生しました: {error_msg}")
        self.status_label.setText("PDF出力エラー")
        self.statusBar().showMessage("PDF出力エラー")