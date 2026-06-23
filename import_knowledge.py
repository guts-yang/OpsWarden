import os
import requests
import re
import json

# API配置
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
LOGIN_URL = f"{BASE_URL}/auth/login"
KNOWLEDGE_URL = f"{BASE_URL}/knowledge"

# 管理员凭据（从环境变量读取，勿硬编码密码）
USERNAME = os.getenv("IMPORT_USERNAME", "admin")
PASSWORD = os.getenv("IMPORT_PASSWORD", "")

# 获取认证token
def get_auth_token():
    response = requests.post(LOGIN_URL, json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text[:200]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"解析后的数据: {data}")
        # 尝试多种可能的token字段名
        token = data.get("access_token") or data.get("data", {}).get("access_token")
        if token:
            return token
        else:
            print(f"未找到access_token字段，完整数据: {data}")
            return None
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

# 解析Markdown文件
def parse_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    knowledge_items = []
    current_category = ""
    
    # 按分类分割内容（匹配 ## 分类名（共N条）格式）
    sections = re.split(r'(## .+（共 \d+ 条）\r?\n)', content)
    
    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break
            
        # 分类标题在奇数索引，内容在偶数索引
        category_match = re.search(r'## (.+)（共 \d+ 条）', sections[i])
        if category_match:
            current_category = category_match.group(1)
        else:
            current_category = "未知分类"
            
        section = sections[i + 1]
        
        # 提取问题条目（用---分割）
        questions = re.split(r'\r?\n---\r?\n', section)
        
        for question_block in questions:
            if not question_block.strip():
                continue
                
            # 提取问题编号
            qid_match = re.search(r'\*\*Q(\d+)\*\*', question_block)
            if not qid_match:
                continue
                
            # 提取问题内容
            question_match = re.search(r'\*\*问题：\*\* (.+)', question_block)
            solution_match = re.search(r'\*\*解决方案：\*\*\r?\n(.+)', question_block, re.DOTALL)
            
            if question_match and solution_match:
                knowledge_items.append({
                    "category": current_category,
                    "qid": qid_match.group(1),
                    "question": question_match.group(1).strip(),
                    "solution": solution_match.group(1).strip()
                })
    
    return knowledge_items

# 导入知识库条目
def import_knowledge_items(token, items):
    headers = {"Authorization": f"Bearer {token}"}
    
    success_count = 0
    error_count = 0
    
    for item in items:
        # 清理分类名称，去掉数字前缀（如"一、"、"八、"等）
        clean_category = re.sub(r'^[一二三四五六七八九十]+、', '', item['category'])
        
        # 构建知识库条目数据
        knowledge_data = {
            "question": f"{item['question']}",
            "solution": item['solution'],
            "category": clean_category,
            "tags": clean_category,
            "doc_id": "OpsWarden_FAQ",
            "page_index": int(item['qid'])
        }
        
        response = requests.post(KNOWLEDGE_URL, json=knowledge_data, headers=headers)
        
        if response.status_code == 200:
            print(f"✓ 成功导入: {item['category']} - Q{item['qid']}")
            success_count += 1
        else:
            print(f"✗ 导入失败: {item['category']} - Q{item['qid']} - {response.status_code}")
            error_count += 1
    
    return success_count, error_count

# 主函数
def main():
    if not PASSWORD:
        print("错误：请设置环境变量 IMPORT_PASSWORD（管理员登录密码）")
        return

    file_path = os.getenv(
        "IMPORT_KB_FILE",
        os.path.join(os.path.dirname(__file__), "backend/knowledge_base/OpsWarden_FAQ.md"),
    )
    
    print("开始解析Markdown知识库文件...")
    knowledge_items = parse_markdown_file(file_path)
    print(f"解析完成，共发现 {len(knowledge_items)} 个知识条目")
    
    if len(knowledge_items) == 0:
        print("警告：未解析到任何知识条目，请检查文件格式")
        return
    
    print("获取认证token...")
    token = get_auth_token()
    if not token:
        print("认证失败，无法继续导入")
        return
    
    print("开始导入知识库条目...")
    success_count, error_count = import_knowledge_items(token, knowledge_items)
    
    print(f"\n导入完成！成功: {success_count}, 失败: {error_count}")

if __name__ == "__main__":
    main()