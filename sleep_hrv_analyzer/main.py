#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
睡眠・HRVデータ分析アプリケーション
AutoSleepとHRVデータを分析し、結果を表示・出力します
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

# ロギング設定
def setup_logging():
    """
    ロギングの設定を行います
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    # ログディレクトリがなければ作成
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'app.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("アプリケーション起動")

def main():
    """
    アプリケーションのメインエントリーポイント
    """
    # ロギングの設定
    setup_logging()
    
    # PyQtアプリケーションの作成
    app = QApplication(sys.argv)
    
    # フォント設定（日本語対応）
    try:
        # 日本語対応フォントを設定
        from PyQt5.QtGui import QFont
        default_font = QFont("Hiragino Sans", 10)
        app.setFont(default_font)
        logging.info("日本語対応フォントを設定しました")
    except Exception as e:
        logging.warning(f"フォント設定エラー: {str(e)}")
    
    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()
    
    # アプリケーションの実行
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()