from typing import Dict, List
from pathlib import Path
import json
import sqlite3
import pandas as pd
import logging

from .errors import *

# 设置日志配置
logging.basicConfig(level=logging.INFO)

def _get_xlsx_data(file_path: Path) -> Dict[str, str]:
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # 检查是否存在"题目"和"答案"列
        if '题目' not in df.columns or '答案' not in df.columns:
            raise UnexpectedFormatValueError("'题目' 或 '答案' 列不存在")
        
        # 过滤掉包含NaN值的行
        df.dropna(subset=['题目', '答案'], inplace=True)
        
        # 将DataFrame转换为字典
        qa_dict = df.set_index('题目')['答案'].to_dict()
        
        return qa_dict
    
    except Exception as e:
        logging.error(f"An error occurred while processing {file_path}: {e}")
        raise

def _get_txt_data(file_path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    with open(file_path, encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    if len(lines) % 2 != 0:
        raise UnexpectedFormatValueError(
            "txt非空行数应为偶数"
        )
    for i in range(0, len(lines), 2):
        line_question = lines[i]
        line_answer = lines[i + 1]
        # 检查行是否以正确的前缀开始
        if not (line_question.startswith("题目 ") and line_answer.startswith("答案 ")):
            raise UnexpectedFormatValueError(
                f"第{i+1}行或第{i+2}行格式不正确：\n{line_question}\n{line_answer}"
            )
        question = line_question.replace("题目 ", "")
        answer = line_answer.replace("答案 ", "")
        # 确保题目和答案都不为空
        if not question or not answer:
            raise UnexpectedFormatValueError(
                f"第{i+1}行或第{i+2}中，题目或答案为空:\n{line_question}\n{line_answer}"
            )
        result[question] = answer

    return result

def _get_json_data(file_path: Path) -> Dict[str, str]:
    try:
        with open(file_path, encoding='utf-8') as f:
            file_data = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {file_path}: {e}")
        raise
    
    if not isinstance(file_data, dict):
        raise UnexpectedFormatValueError(f"JSON格式不正确，应该为键值对")
    
    return file_data

def _get_db_data(db_path: Path) -> Dict[str, str]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # 检查表是否存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions';")
        table_exists = cur.fetchone()
        if not table_exists:
            raise UnexpectedFormatValueError("Table 'questions' does not exist in the database.")
        
        # 检查列是否存在
        cur.execute("PRAGMA table_info(questions);")
        columns = [column[1] for column in cur.fetchall()]
        if 'question' not in columns or 'answer' not in columns:
            raise UnexpectedFormatValueError("Columns 'question' and/or 'answer' do not exist in the 'questions' table.")
        
        # 执行查询
        cur.execute("SELECT question, answer FROM questions")
        
        # 提取结果
        rows = cur.fetchall()
        qa_dict = {row[0]: row[1] for row in rows}
        
    finally:
        conn.close()
    
    return qa_dict

def get_file_data(file_path: Path) -> Dict[str, str]:
    if not file_path.exists():
        raise FileNotFoundError(f"无法找到文件 {file_path}")
    suffix = file_path.suffix.lower()
    if suffix == ".xlsx":
        return _get_xlsx_data(file_path)
    elif suffix == ".txt":
        return _get_txt_data(file_path)
    elif suffix == ".json":
        return _get_json_data(file_path)
    elif suffix == ".db":
        return _get_db_data(file_path)
    else:
        raise UnsupportedFileTypeError(f"不支持的文件格式: {suffix}")