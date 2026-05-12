#!/usr/bin/env python3
"""
OpsWarden FAQ 知识库批量导入脚本
从 Markdown 文件导入 FAQ 数据到数据库
"""

import re
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import get_db
from app.models.knowledge import KBEntry
from datetime import datetime

# 数据库连接配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/opswarden")

def parse_faq_markdown(file_path):
    """解析 FAQ Markdown 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按分类分割
    sections = re.split(r'^##\s+(.+)$', content, flags=re.MULTILINE)
    
    faq_list = []
    current_category = None
    
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            category = sections[i].strip()
            # 清理分类名称：去掉序号和括号内容
            category = re.sub(r'^[一二三四五六七八九十]+、', '', category)  # 去掉中文序号
            category = re.sub(r'（共\s*\d+\s*条）', '', category)  # 去掉括号内容
            category = category.strip()
            section_content = sections[i + 1].strip()
            
            # 提取问题和解决方案 - 使用 **QXXX** 格式
            items = re.split(r'^\*\*Q\d+\*\*', section_content, flags=re.MULTILINE)
            
            for j in range(1, len(items)):
                item_content = items[j].strip()
                
                # 提取问题
                question_match = re.search(r'\*\*问题：\*\*(.+?)(?=\*\*解决方案：\*\*|$)', item_content, re.DOTALL)
                # 提取解决方案
                solution_match = re.search(r'\*\*解决方案：\*\*(.+?)(?=---|$)', item_content, re.DOTALL)
                
                if question_match and solution_match:
                    question = question_match.group(1).strip()
                    solution = solution_match.group(1).strip()
                    
                    faq_list.append({
                        'category': category,
                        'question': question,
                        'solution': solution,
                        'source': 'manual',
                        'match_score': 0.9
                    })
    
    return faq_list

def batch_import_faq(file_path, batch_size=50):
    """批量导入 FAQ 数据"""
    print(f"开始导入 FAQ 数据: {file_path}")
    
    # 解析 Markdown 文件
    faq_list = parse_faq_markdown(file_path)
    print(f"解析到 {len(faq_list)} 条 FAQ 数据")
    
    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # 清空现有数据
        db.query(KBEntry).delete()
        db.commit()
        print("已清空现有知识库数据")
        
        # 批量导入
        imported_count = 0
        for i in range(0, len(faq_list), batch_size):
            batch = faq_list[i:i + batch_size]
            
            for faq in batch:
                entry = KBEntry(
                    category=faq['category'],
                    question=faq['question'],
                    solution=faq['solution'],
                    source=text("'manual'::kb_source"),
                    match_score=faq['match_score'],
                    doc_id='legacy',
                    page_index=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(entry)
                imported_count += 1
            
            db.commit()
            print(f"已导入 {imported_count}/{len(faq_list)} 条数据")
        
        print(f"✅ 成功导入 {imported_count} 条 FAQ 数据")
        return imported_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ 导入失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # FAQ 文件路径
    faq_file = "/app/backend/knowledge_base/OpsWarden_FAQ.md"
    
    if not os.path.exists(faq_file):
        print(f"❌ FAQ 文件不存在: {faq_file}")
        sys.exit(1)
    
    # 执行导入
    batch_import_faq(faq_file)
