#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
カスタムファイル解析モジュール
特殊形式のCSVファイルを解析します
"""

import re
import logging
import pandas as pd
from .date_utils import parse_japanese_datetime, get_date_string

def read_autosleep_data(file_path):
    """
    AutoSleepデータを読み込み、解析します
    
    引数:
        file_path (str): CSVファイルのパス
    
    戻り値:
        pandas.DataFrame: 処理されたデータフレーム
    """
    # 日本語列名の英語変換マップ
    column_map = {
        '就寝時間': 'Bedtime',
        '起床時間': 'Wakeup',
        '平均呼吸': 'Avg Breathing Rate',
        '睡眠': 'Sleep Duration'
    }
    
    # ファイル読み込み（エンコーディング自動検出）
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='shift-jis')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp932')
    
    # 必要な列のみを選択（存在する場合）
    required_columns = ['就寝時間', '起床時間', '平均呼吸', '睡眠']
    existing_columns = [col for col in required_columns if col in df.columns]
    
    # 最低限必要な列がなければエラー
    if '就寝時間' not in existing_columns or '起床時間' not in existing_columns:
        raise ValueError("必須列「就寝時間」または「起床時間」がCSVファイルに見つかりません")
    
    # 必要な列のみのデータフレームを作成
    selected_df = df[existing_columns].copy()
    
    # 日本語カラム名を英語に変換
    selected_df = selected_df.rename(columns=column_map)
    
    # 日時データの解析
    selected_df['Bedtime_dt'] = selected_df['Bedtime'].apply(parse_japanese_datetime)
    selected_df['Wakeup_dt'] = selected_df['Wakeup'].apply(parse_japanese_datetime)
    
    # 基準日（起床日）を計算 - 修正箇所：就寝日から起床日に変更
    selected_df['Date'] = selected_df['Wakeup_dt'].apply(lambda dt: get_date_string(dt))
    
    return selected_df

def parse_hrv_file(file_path):
    """
    特殊フォーマットのHRVデータファイルを解析します
    
    引数:
        file_path (str): HRVデータファイルのパス
    
    戻り値:
        dict: 日付ごとの時間帯別HRVデータ
    """
    hrv_data = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # ファイルが少なくとも2行あることを確認
            if len(lines) < 2:
                raise ValueError("HRVファイルの形式が不正です（ヘッダー行がありません）")
            
            # ヘッダー行から時間帯を抽出 (2行目)
            header = lines[1].strip()
            time_slots = [slot.strip() for slot in header.split(',')[1:]]
            
            # 各データ行を処理 (3行目以降)
            for i in range(2, len(lines)):
                line = lines[i].strip()
                if not line:
                    continue
                
                values = line.replace('"', '').split(',')
                date = values[0].strip()  # YYYY/MM/DD形式
                
                # 各時間帯のHRV値を抽出
                date_hrv = {}
                for j, value in enumerate(values[1:], 0):
                    if j < len(time_slots) and value.strip():
                        slot = time_slots[j]
                        
                        # 範囲値 "X - Y" の処理
                        if ' - ' in value:
                            parts = value.split(' - ')
                            if len(parts) == 2:
                                try:
                                    min_val = float(parts[0])
                                    max_val = float(parts[1])
                                    date_hrv[slot] = (min_val + max_val) / 2
                                except ValueError:
                                    pass
                        else:
                            try:
                                date_hrv[slot] = float(value)
                            except ValueError:
                                pass
                
                hrv_data[date] = date_hrv
    
    except Exception as e:
        logging.error(f"HRVファイル解析エラー: {str(e)}")
        raise
    
    return hrv_data

def filter_ascii_only(text):
    """
    テキストから非ASCII文字を削除します
    
    引数:
        text (str): 元のテキスト
        
    戻り値:
        str: ASCII文字のみのテキスト
    """
    if not isinstance(text, str):
        text = str(text)
    return ''.join(c for c in text if ord(c) < 128)