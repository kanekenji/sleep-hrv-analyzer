#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日付と時刻の処理用ユーティリティ
日本語を含む日時文字列を処理します
"""

import re
import logging
from datetime import datetime

def parse_japanese_datetime(datetime_str):
    """
    日本語を含む日時文字列をdatetimeオブジェクトに変換します
    例: "2025-03-02 午後9:56:00" → datetime
    
    引数:
        datetime_str (str): 変換する日時文字列
    
    戻り値:
        datetime: 変換された日時オブジェクト、変換失敗時はNone
    """
    if not datetime_str or not isinstance(datetime_str, str):
        return None
        
    try:
        # 日付部分と時間部分を分割
        date_part, time_part = datetime_str.split(' ')
        year, month, day = map(int, date_part.split('-'))
        
        # 時間部分を処理（午前/午後に対応）
        pattern = r'(午前|午後)(\d+):(\d+):(\d+)'
        match = re.match(pattern, time_part)
        
        if match:
            am_pm = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3))
            second = int(match.group(4))
            
            # 午後は12時間追加（ただし正午は除く）
            if am_pm == '午後' and hour != 12:
                hour += 12
            # 午前12時は0時
            elif am_pm == '午前' and hour == 12:
                hour = 0
            
            return datetime(year, month, day, hour, minute, second)
    
    except Exception as e:
        logging.error(f"日時解析エラー '{datetime_str}': {str(e)}")
        
    return None

def format_time_part(datetime_str):
    """
    日時文字列から時間部分のみを取得します
    
    引数:
        datetime_str (str): 元の日時文字列
    
    戻り値:
        str: 時間部分の文字列
    """
    parts = datetime_str.split(' ')
    if len(parts) > 1:
        return parts[1]
    return datetime_str

def get_date_string(dt, format='%Y/%m/%d'):
    """
    datetimeオブジェクトを指定形式の日付文字列に変換します
    
    引数:
        dt (datetime): 変換するdatetimeオブジェクト
        format (str): 日付フォーマット
    
    戻り値:
        str: フォーマットされた日付文字列
    """
    if dt is None:
        return ""
    return dt.strftime(format)

def convert_time_slot_to_hour(time_slot):
    """
    時間帯文字列から時刻（時）を抽出します
    例: "12 AM - 1 AM" → 0
    
    引数:
        time_slot (str): 時間帯文字列
    
    戻り値:
        int: 時刻（0-23）、変換失敗時は-1
    """
    match = re.match(r'(\d+)\s*(AM|PM)', time_slot)
    if match:
        hour = int(match.group(1))
        am_pm = match.group(2)
        
        # 12時間表記を24時間表記に変換
        if am_pm == 'PM' and hour != 12:
            hour += 12
        elif am_pm == 'AM' and hour == 12:
            hour = 0
            
        return hour
    
    return -1  # 変換失敗