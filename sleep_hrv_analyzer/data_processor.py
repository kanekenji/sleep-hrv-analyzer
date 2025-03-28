#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
睡眠・HRVデータの処理モジュール
AutoSleepとHRVデータを統合し、分析結果を生成します
微分積分アプローチを用いて日中HRV平均値を計算
"""

import logging
import pandas as pd
from utils.file_parser import read_autosleep_data, parse_hrv_file
from utils.date_utils import convert_time_slot_to_hour, format_time_part

def calculate_daytime_hrv_integral(hrv_data, wakeup_datetime, next_bedtime_datetime=None):
    """
    起床時間から次の就寝時間までの日中HRV平均値を微分積分アプローチで計算します
    
    引数:
        hrv_data (dict): 時間帯別HRV値
        wakeup_datetime (datetime): 起床時間
        next_bedtime_datetime (datetime, optional): 次の就寝時間、Noneの場合は制限なし
    
    戻り値:
        float: 日中のHRV平均値、データがない場合はNone
    """
    if not hrv_data or wakeup_datetime is None:
        return None
    
    wakeup_hour = wakeup_datetime.hour
    next_bedtime_hour = 23  # デフォルトは23時（日の終わり）
    
    if next_bedtime_datetime:
        # 次の就寝時間が設定されている場合
        next_bedtime_hour = next_bedtime_datetime.hour
    
    # 起床時間以降かつ次の就寝時間より前の時間帯のHRV値を時間順にソート
    daytime_data = []
    
    for time_slot, hrv_value in hrv_data.items():
        hour = convert_time_slot_to_hour(time_slot)
        if hour >= 0 and hour >= wakeup_hour and hour < next_bedtime_hour:
            daytime_data.append((hour, hrv_value))
    
    # 時間順にソート
    daytime_data.sort(key=lambda x: x[0])
    
    if len(daytime_data) < 2:
        # データポイントが1つ以下の場合は通常の平均値を返す
        if daytime_data:
            return daytime_data[0][1]
        return None
    
    # 積分計算
    total_integral = 0
    total_time = 0
    
    for i in range(len(daytime_data) - 1):
        start_hour, start_value = daytime_data[i]
        end_hour, end_value = daytime_data[i+1]
        
        # 時間区間
        time_interval = end_hour - start_hour
        
        # この時間区間が有効かどうかをチェック
        if time_interval <= 0:
            continue
        
        # 台形積分: (start_value + end_value) / 2 * time_interval
        segment_integral = (start_value + end_value) / 2 * time_interval
        
        total_integral += segment_integral
        total_time += time_interval
    
    # 平均値計算
    if total_time > 0:
        return round(total_integral / total_time, 2)
    
    return None

def process_sleep_hrv_data(sleep_file_path, hrv_file_path, progress_callback=None):
    """
    AutoSleepとHRVデータを統合処理し、分析結果を生成します
    
    引数:
        sleep_file_path (str): AutoSleepファイルのパス
        hrv_file_path (str): HRVファイルのパス
        progress_callback (function): 進捗状況通知コールバック
    
    戻り値:
        tuple: (結果データフレーム, AutoSleepデータ, HRVデータ)
    """
    if progress_callback:
        progress_callback(10)
    
    try:
        # AutoSleepデータの読み込み
        logging.info("AutoSleepデータを読み込んでいます...")
        sleep_data = read_autosleep_data(sleep_file_path)
        logging.info(f"AutoSleepデータを読み込みました: {len(sleep_data)}レコード")
        
        if progress_callback:
            progress_callback(30)
        
        # HRVデータの読み込み
        logging.info("HRVデータを読み込んでいます...")
        hrv_data = parse_hrv_file(hrv_file_path)
        logging.info(f"HRVデータを読み込みました: {len(hrv_data)}日分")
        
        if progress_callback:
            progress_callback(50)
        
        # 結果データフレームの準備
        result_df = pd.DataFrame(columns=[
            'Date', 'Bedtime', 'Wakeup',
            'Daytime HRV Avg (ms)', 'Avg Breathing Rate',
            'Sleep Duration (HH:MM:SS)'
        ])
        
        # 各睡眠レコードを処理
        for i, (_, sleep_record) in enumerate(sleep_data.iterrows()):
            # 進捗状況更新
            if progress_callback and len(sleep_data) > 0:
                progress_value = 50 + int((i / len(sleep_data)) * 40)
                progress_callback(min(progress_value, 90))
            
            # 就寝・起床時間の取得
            bedtime_dt = sleep_record.get('Bedtime_dt')
            wakeup_dt = sleep_record.get('Wakeup_dt')
            
            if bedtime_dt is None or wakeup_dt is None:
                logging.warning(f"レコード {i+1}: 日時解析エラー、スキップします")
                continue
            
            # 起床日のHRVデータを取得
            wakeup_date = wakeup_dt.strftime('%Y/%m/%d')
            wakeup_hrv = hrv_data.get(wakeup_date, {})
            
            # 次のレコードがあれば、その就寝時間を取得
            next_bedtime_dt = None
            if i + 1 < len(sleep_data):
                next_record = sleep_data.iloc[i + 1]
                next_bedtime_dt = next_record.get('Bedtime_dt')
            
            # 日中HRV平均値を計算（微分積分アプローチを使用）
            avg_daytime_hrv = calculate_daytime_hrv_integral(wakeup_hrv, wakeup_dt, next_bedtime_dt)
            
            # 結果に新しい行データを追加
            new_row = pd.DataFrame({
                'Date': [sleep_record['Date']],  # すでに起床日が入っています（file_parser.pyの修正により）
                'Bedtime': [format_time_part(sleep_record['Bedtime'])],
                'Wakeup': [format_time_part(sleep_record['Wakeup'])],
                'Daytime HRV Avg (ms)': 
                    [str(avg_daytime_hrv) if avg_daytime_hrv is not None else 'N/A'],
                'Avg Breathing Rate': [sleep_record.get('Avg Breathing Rate', 'N/A')],
                'Sleep Duration (HH:MM:SS)': [sleep_record.get('Sleep Duration', 'N/A')]
            })
            result_df = pd.concat([result_df, new_row], ignore_index=True)
        
        if progress_callback:
            progress_callback(95)
        
        return result_df, sleep_data, hrv_data
    
    except Exception as e:
        logging.error(f"データ処理エラー: {str(e)}")
        raise
    