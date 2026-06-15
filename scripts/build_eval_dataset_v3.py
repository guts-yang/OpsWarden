#!/usr/bin/env python3
"""Build RAG eval dataset v3: expanded KB + multi-type queries.

Usage (from repo root):
    python scripts/build_eval_dataset_v3.py
    python scripts/build_eval_dataset_v3.py --paraphrase-per-faq 4 --kb-variants 3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
SCRIPTS = ROOT / "scripts"
OUTPUT_DIR = ROOT / "scripts" / "eval_datasets"
OUTPUT_QUERIES = OUTPUT_DIR / "faq_eval_v3.json"
OUTPUT_KB = OUTPUT_DIR / "faq_eval_kb_v3.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from app.rag.faq_loader import FAQ_PATH, _parse_faq  # noqa: E402
from build_eval_dataset_v2 import (  # noqa: E402
    NEGATIVE_QUERIES,
    paraphrase_a,
    paraphrase_b,
    _strip_question_prefix,
)

NEAR_MISS_NEGATIVES = [
    "运维门户登录一直转圈",
    "VPN 连上了但内网打不开",
    "工单提交了没人处理",
    "知识库搜不到我的问题",
    "RAG 回答和文档不一致",
    "账号权限审批卡在第二步",
    "重置密码短信收不到",
    "新员工账号邮件没收到",
    "数据库连接池满了怎么办",
    "服务器 CPU 飙高怎么排查",
    "日志在哪里下载",
    "监控告警邮件太多",
    "备份任务失败了",
    "SSL 证书过期提醒",
    "Docker 容器起不来",
    "K8s Pod 一直 Pending",
    "Redis 内存满了",
    "Nginx 502 错误",
    "GitLab CI 跑失败",
    "Jenkins 构建超时",
    "堡垒机登录被拒绝",
    "跳板机密钥过期",
    "域账号同步失败",
    "LDAP 认证报错",
    "邮件服务器退信",
    "DNS 解析慢",
    "防火墙端口不通",
    "负载均衡健康检查失败",
    "对象存储上传失败",
    "消息队列积压严重",
    "微服务调用超时",
    "API 网关 429 限流",
    "Prometheus 指标缺失",
    "Grafana 面板空白",
    "ELK 日志搜不到",
    "CMDB 资产信息不对",
    "变更窗口怎么申请",
    "紧急变更谁审批",
    "值班电话是多少",
    "运维 SLA 是多少",
    "Incident 怎么升级",
    "Postmortem 模板在哪",
    "Runbook 怎么写",
    "SOP 文档过期了",
    "合规审计材料在哪",
    "等保测评怎么配合",
    "漏洞扫描报告怎么看",
    "补丁安装窗口",
    "灾备演练怎么参加",
    "RTO RPO 标准是什么",
    "双活切换演练",
    "机房进出登记",
    "U 位怎么申请",
    "机柜电源跳闸",
    "UPS 告警处理",
    "空调漏水报修",
    "办公网 WiFi 密码",
    "访客 WiFi 怎么连",
    "打印机驱动安装",
    "扫描仪共享设置",
    "视频会议卡顿",
    "Teams 消息发不出",
    "Slack 频道找不到",
    "Jira 工单字段填什么",
    "Confluence 页面权限",
    "SharePoint 上传限制",
    "OneDrive 同步冲突",
    "Outlook 日历不同步",
    "企业微信扫码失败",
    "钉钉审批流卡住",
    "飞书机器人怎么配",
    "OA 流程退回重提",
    "HR 系统打不开",
    "财务报销系统维护",
    "采购系统供应商录入",
    "合同管理系统登录",
    "资产盘点系统条码",
    "门禁卡丢了补办",
    "工牌照片更新",
    "班车改线通知",
    "食堂充值失败",
    "停车位被占",
    "快递柜满了",
    "会议室预订冲突",
    "投影幕布降不下来",
    "白板笔没水了",
    "茶水间咖啡机故障",
    "健身房器械维修",
    "母婴室怎么预约",
    "医务室几点开门",
    "心理咨询怎么约",
    "员工体检报告在哪",
    "商业保险理赔流程",
    "子女教育补贴申请",
    "租房补贴材料",
    "交通补贴标准",
    "通讯补贴报销",
    "加班餐怎么订",
    "打车报销上限",
    "出差机票改签",
    "酒店超标怎么办",
    "签证邀请函申请",
    "护照借出流程",
    "外籍员工工作许可",
    "实习生账号开通",
    "外包人员权限申请",
    "第三方 VPN 接入",
    "供应商远程桌面",
    "客户演示环境申请",
    "测试环境数据脱敏",
    "生产只读账号申请",
    "数据库慢查询分析",
    "索引优化谁负责",
    "表结构变更审批",
    "数据导出合规审查",
    "PII 字段怎么识别",
    "日志脱敏规则",
    "密钥轮换周期",
    "证书自动续期失败",
    "HSM 设备告警",
    "WAF 误拦截怎么办",
    "DDoS 攻击应急响应",
    "钓鱼邮件举报",
    "U 盘禁用策略",
    "屏幕水印怎么关",
    "DLP 告警处理",
    "零信任客户端安装",
    "MFA 设备丢失",
    "硬件 Token 补办",
    "生物识别录入失败",
    "单点登录跳转错误",
    "OAuth 回调域名配置",
    "API Key 泄露轮换",
    "Webhook 签名验证",
    "Rate limit 白名单",
    "IP 封禁怎么解",
    "Geo blocking 例外",
    "CDN 缓存刷新",
    "静态资源 404",
    "前端发布回滚",
    "蓝绿部署切换",
    "金丝雀发布比例",
    "Feature flag 怎么开",
    "A/B 实验配置",
    "埋点数据缺失",
    "用户行为分析权限",
    "数据仓库查询排队",
    "BI 报表导出 Excel",
    "ETL 任务失败重跑",
    "数据血缘怎么查",
    "主数据不一致",
    "MDM 设备注册",
    "EMM 应用推送",
    "Mobile SSO 配置",
    "App 崩溃日志上传",
    "Push 通知收不到",
    "SDK 集成文档",
    "开放平台 API 配额",
    "Sandbox 环境申请",
    "Webhook 重试策略",
    "消息幂等怎么保证",
    "分布式事务失败",
    "缓存穿透怎么处理",
    "热点 Key 问题",
    "分库分表路由",
    "读写分离延迟",
    "主从切换影响",
    "Binlog 同步延迟",
    "CDC 任务卡住",
    "Flink 作业重启",
    "Spark 内存溢出",
    "Airflow DAG 失败",
    "调度依赖怎么配",
    "Cron 表达式写法",
    "时区问题导致漏跑",
    "批处理窗口冲突",
    "实时链路延迟高",
    "Kafka 消费 lag",
    "RocketMQ 顺序消息",
    "RabbitMQ 队列堆积",
    "Pulsar 租户配额",
    "Zookeeper 选举失败",
    "Etcd 集群不健康",
    "Consul 服务发现异常",
    "Nacos 配置不生效",
    "Apollo 灰度发布",
    "Spring Cloud 熔断",
    "Service Mesh  sidecar",
    "Istio 流量镜像",
    "Envoy 访问日志",
    "Linkerd 指标缺失",
    "Helm Chart 版本冲突",
    "Operator CRD 升级",
    "CR 状态 Pending",
    "PV 挂载失败",
    "StorageClass 变更",
    "CSI 驱动报错",
    "Snapshot 备份恢复",
    "Velero 迁移集群",
    "Harbor 镜像扫描",
    "Trivy 漏洞报告",
    "SBOM 怎么生成",
    "Supply chain 安全",
    "SAST 扫描误报",
    "DAST 扫描授权",
    "IAST 探针安装",
    "Pen test 报告解读",
    "Bug bounty 流程",
    "Responsible disclosure",
    "Security champion 培训",
    "Phishing simulation",
    "Security awareness 考试",
    "Compliance training 逾期",
    "Background check 状态",
    "NDA 签署链接",
    "IP assignment 协议",
    "Open source 合规审查",
    "License 冲突检测",
    "Third party 组件升级",
    "EOL 软件清单",
    "Technical debt 登记",
    "Architecture review 申请",
    "Design doc 模板",
    "RFC 评论权限",
    "ADR 怎么写",
    "Tech radar 更新",
    "Innovation day 提案",
    "Hackathon 报名",
    "Patent 申报流程",
    "Paper 发表审批",
    "Conference 出差申请",
    "Training budget 使用",
    "Certification 报销",
    "AWS/Azure/GCP 账号",
    "Cloud cost 优化",
    "Reserved instance 购买",
    "Spot 实例中断",
    "S3 桶公开访问",
    "IAM 权限最小化",
    "Cross account 角色",
    "Landing zone 配置",
    "Control tower 告警",
    "Organization SCP",
    "Tag 策略强制",
    "Budget alert 阈值",
    "FinOps 报表权限",
    "Green IT 指标",
    "Carbon footprint 报告",
    "ESG 数据填报",
    "Sustainability 目标",
    "Remote work 设备寄送",
    "BYOD 政策例外",
    "Asset return 流程",
    "Equipment refresh 周期",
    "Laptop 电池膨胀",
    "Dock 站不识别",
    "外接显示器无信号",
    "键盘个别键失灵",
    "Touchpad 手势失效",
    "Webcam 隐私盖",
    "Headset 蓝牙配对",
    "Noise cancel 不工作",
    "Standing desk 调节",
    "Ergonomic 评估预约",
    "Eye exam 补贴",
    "Blue light 眼镜报销",
    "Office chair 更换",
    "Monitor arm 安装",
    "Cable management 请求",
    "Power strip 不够",
    "UPS 个人工位",
    "Surge protector 更换",
    "Ethernet 口损坏",
    "USB hub 供电不足",
    "Thunderbolt 认证失败",
    "HDMI 转接无输出",
    "USB-C 充电慢",
    "Firmware 更新失败",
    "BIOS 密码重置",
    "BitLocker 恢复密钥",
    "FileVault 解锁",
    "Disk encryption 豁免",
    "Secure boot 冲突",
    "TPM 不可用",
    "Virtualization 未启用",
    "Hyper-V 与 VMware 冲突",
    "WSL2 网络异常",
    "Docker Desktop 许可",
    "Colima 替代方案",
    "Dev container 构建慢",
    "Codespaces 配额",
    "GitHub Copilot 开通",
    "Cursor 企业版申请",
    "IDE 插件白名单",
    "Maven 私服认证",
    "NPM registry 代理",
    "PyPI 镜像配置",
    "Go module proxy",
    "Rust crate 源",
    "NuGet 包还原失败",
    "Gradle 依赖冲突",
    "SBT 编译 OOM",
    "Xcode 签名证书",
    "Android keystore 备份",
    "iOS provisioning profile",
    "TestFlight 邀请",
    "Play Console 权限",
    "App Store 审核被拒",
    "Firebase 配置错误",
    "Crashlytics 符号表",
    "Analytics 采样率",
    "Remote config 不生效",
    "A/B test 样本不足",
    "Feature rollout 回滚",
    "Dark mode 样式 bug",
    "Accessibility 审计",
    "Localization 翻译流程",
    "RTL 布局问题",
    "Font 子集化",
    "CDN 字体加载失败",
    "CORS 预检失败",
    "Cookie SameSite",
    "CSRF token 过期",
    "XSS 过滤误伤",
    "Content Security Policy",
    "Subresource Integrity",
    "HTTP/3 兼容性",
    "QUIC 被防火墙拦",
    "IPv6 双栈问题",
    "MTU 黑洞检测",
    "Traceroute 中断",
    "Packet loss 排查",
    "Latency 抖动",
    "Jitter buffer 配置",
    "QoS 标记优先级",
    "SD-WAN 链路切换",
    "MPLS 专线故障",
    "Internet breakout 策略",
    "Split tunnel VPN",
    "Full tunnel 性能",
    "Always-on VPN 冲突",
    "Per-app VPN iOS",
    "Certificate pinning 更新",
    "Mobile device compliance",
    "Jailbreak root 检测",
    "MDM wipe 远程擦除",
    "Lost device 报告",
    "Stolen laptop 流程",
    "Insurance claim IT",
    "Forensics 镜像申请",
    "Legal hold 数据保留",
    "eDiscovery 导出",
    "Litigation hold 解除",
    "Records retention 政策",
    "Archive 访问权限",
    "Tape backup 恢复",
    "Cold storage 取回",
    "Glacier 检索费用",
    "Cross region replication",
    "Multi AZ 部署",
    "Active active 数据库",
    "Split brain 处理",
    "Quorum 节点丢失",
    "Raft 日志损坏",
    "Paxos 理解",
    "Consensus 延迟",
    "Leader election 频繁",
    "Follower lag 过大",
    "Read your writes",
    "Monotonic reads",
    "Causal consistency",
    "Eventual consistency 窗口",
    "Conflict resolution CRDT",
    "Last write wins 风险",
    "Vector clock 调试",
    "Saga 补偿事务",
    "Outbox pattern 实现",
    "Inbox dedup",
    "Idempotency key 设计",
    "Retry backoff jitter",
    "Circuit breaker 阈值",
    "Bulkhead 隔离",
    "Timeout cascade",
    "Graceful shutdown",
    "Health check 探针",
    "Liveness vs readiness",
    "Startup probe 慢",
    "PreStop hook 超时",
    "Pod disruption budget",
    "Cluster autoscaler",
    "Node pool 升级",
    "Kernel CVE 补丁",
    "Container runtime 切换",
    "CRI-O vs containerd",
    "gVisor 兼容性",
    "Kata containers",
    "Falco 告警规则",
    "OPA Gatekeeper 策略",
    "Kyverno 验证失败",
    "Pod security standards",
    "Seccomp profile",
    "AppArmor 配置",
    "SELinux 上下文",
    "Capabilities drop",
    "Privileged container 审批",
    "HostPath 挂载风险",
    "HostNetwork 例外",
    "HostPID 调试",
    "Sysctl 参数调整",
    "Huge pages 配置",
    "CPU manager static",
    "Topology manager",
    "NUMA 亲和性",
    "GPU 调度 MIG",
    "NVIDIA driver 版本",
    "CUDA OOM",
    "ML model serving 延迟",
    "Batch inference 队列",
    "Feature store 同步",
    "Model registry 权限",
    "Experiment tracking",
    "Hyperparameter tuning 资源",
    "Notebook 内核崩溃",
    "JupyterHub 登录",
    "VS Code Server 端口",
    "Remote SSH 断连",
    "Port forwarding 冲突",
    "Tunnel 不稳定",
    "Bastion 会话录制",
    "Command approval 工作流",
    "Just in time access",
    "PAM 密码 vault",
    "Secrets rotation Lambda",
    "KMS key 权限",
    "Envelope encryption",
    "BYOK 客户密钥",
    "HSM 分区配额",
    "PKCS11 库路径",
    "mTLS 双向认证",
    "Client cert 续期",
    "OCSP stapling 失败",
    "Certificate transparency",
    "DNSSEC 配置",
    "DMARC 报告解读",
    "SPF 记录冲突",
    "DKIM 签名失败",
    "Email authentication",
    "Phishing simulation 结果",
    "Security scorecard",
    "Vendor risk assessment",
    "Third party SOC2",
    "Data processing agreement",
    "Privacy impact assessment",
    "GDPR 数据主体请求",
    "CCPA opt out",
    "Cookie consent banner",
    "Tracking pixel 合规",
    "Analytics opt in",
    "Data minimization 审查",
    "Purpose limitation",
    "Storage limitation",
    "Accuracy 数据更正",
    "Integrity confidentiality",
    "Accountability 记录",
    "DPO 联系方式",
    "Breach notification 72h",
    "Incident severity 分级",
    "War room 桥接号",
    "Status page 更新",
    "Customer comms 模板",
    "Root cause 5 whys",
    "Blameless postmortem",
    "Action item 跟踪",
    "Error budget 消耗",
    "SLO burn rate",
    "Toil 减少目标",
    "On-call compensation",
    "Pager rotation 换班",
    "Escalation policy PagerDuty",
    "Maintenance window 通知",
    "Change advisory board",
    "Standard change 预批准",
    "Emergency change 记录",
    "Rollback plan 模板",
    "Verification step 遗漏",
    "Communication plan 缺失",
    "Stakeholder sign off",
    "Release notes 发布",
    "Version numbering semver",
    "Deprecation timeline",
    "Sunset API 通知",
    "Migration guide 链接",
    "Breaking change 公告",
    "Compatibility matrix",
    "Support lifecycle EOL",
    "Extended support 费用",
    "Premium support 升级",
    "TAM 联系方式",
    "Success plan 季度 review",
    "QBR 材料准备",
    "ROI 计算模板",
    "TCO 分析报告",
    "Benchmark 对比",
    "Reference architecture",
    "Well architected review",
    "Cost optimization pillar",
    "Reliability pillar",
    "Performance efficiency",
    "Security pillar",
    "Operational excellence",
    "Sustainability pillar",
]


def paraphrase_c(question: str) -> str:
    """Rule C: omit subject, colloquial '咋整'."""
    core = _strip_question_prefix(question).rstrip("？?")
    if len(core) > 12:
        parts = re.split(r"[，,；;、]", core)
        core = parts[0].strip()
    if not core:
        return question
    return f"{core}咋整"


def paraphrase_d(question: str) -> str:
    """Rule D: longer oral with '有没有办法'."""
    core = _strip_question_prefix(question).rstrip("？?")
    if not core:
        return question
    return f"想问下{core}有没有办法处理？"


def variant_question(question: str, variant_idx: int) -> str:
    core = _strip_question_prefix(question).rstrip("？?")
    suffixes = ["（口语版）", "——简要问法", "·运维同事常问"]
    if variant_idx == 0:
        return f"关于{core}的问题"
    if variant_idx == 1:
        return f"{core}{suffixes[variant_idx % len(suffixes)]}？"
    return paraphrase_a(question)


def variant_solution(solution: str, variant_idx: int) -> str:
    repl = [
        ("步骤", "流程"),
        ("登录", "登入"),
        ("点击", "选择"),
        ("可按以下步骤", "建议按如下流程"),
        ("联系运维", "联系运维同事"),
        ("运维门户", "运维平台"),
    ]
    text = solution.strip()
    for old, new in repl:
        if variant_idx % 2 == 0:
            text = text.replace(old, new, 1)
        else:
            text = text.replace(old, new)
    if variant_idx == 2:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if len(lines) > 4:
            text = "\n".join(lines[:3] + ["（其余步骤同标准流程）"] + lines[-1:])
    return text


def hard_confusion_query(question: str, sibling_question: str) -> str:
    """Short ambiguous query blending sibling phrasing with target topic."""
    target_core = _strip_question_prefix(question).rstrip("？?")
    sib_core = _strip_question_prefix(sibling_question).rstrip("？?")
    if len(target_core) > 10:
        target_core = target_core[:10].rstrip("的、与及和")
    if len(sib_core) > 8:
        sib_core = sib_core[:8].rstrip("的、与及和")
    patterns = [
        f"{sib_core}相关，但其实是{target_core}？",
        f"跟{sib_core}有点像，{target_core}怎么弄？",
        f"{target_core}（不是{sib_core}）",
        f"请问{sib_core}还是{target_core}？",
    ]
    return patterns[hash(question + sibling_question) % len(patterns)]


def build_kb_v3(parsed: list[dict], kb_variants: int) -> list[dict]:
    rows: list[dict] = []
    kb_id = 1
    for idx, item in enumerate(parsed, start=1):
        q = item["question"].strip()
        s = item["solution"].strip()
        cat = item["category"]
        rows.append(
            {
                "kb_id": kb_id,
                "page_index": idx,
                "parent_page_index": None,
                "is_canonical": True,
                "variant_id": None,
                "category": cat,
                "question": q,
                "solution": s,
            }
        )
        kb_id += 1
        for v in range(kb_variants):
            rows.append(
                {
                    "kb_id": kb_id,
                    "page_index": idx,
                    "parent_page_index": idx,
                    "is_canonical": False,
                    "variant_id": f"v{idx}_{v}",
                    "category": cat,
                    "question": variant_question(q, v),
                    "solution": variant_solution(s, v),
                }
            )
            kb_id += 1
    return rows


def build_queries_v3(
    parsed: list[dict],
    *,
    paraphrase_per_faq: int,
    hard_confusion: int,
    negative: int,
) -> list[dict]:
    by_cat: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for idx, item in enumerate(parsed, start=1):
        by_cat[item["category"]].append((idx, item))

    rows: list[dict] = []
    paraphrase_fns = [paraphrase_a, paraphrase_b, paraphrase_c, paraphrase_d]

    for idx, item in enumerate(parsed, start=1):
        q = item["question"].strip()
        cat = item["category"]
        sol = item["solution"]
        base = {
            "page_index": idx,
            "category": cat,
            "question": q,
            "solution": sol,
        }
        rows.append({**base, "query": q, "split": "exact", "paraphrase_id": None})

        seen: set[str] = {q}
        pid = 0
        for fn in paraphrase_fns:
            if pid >= paraphrase_per_faq:
                break
            pq = fn(q)
            if pq in seen:
                continue
            seen.add(pq)
            pid += 1
            rows.append(
                {
                    **base,
                    "query": pq,
                    "split": "paraphrase",
                    "paraphrase_id": f"p{idx}_{chr(96 + pid)}",
                }
            )

    # hard_confusion: pick FAQs spread across categories
    step = max(1, len(parsed) // max(hard_confusion, 1))
    hard_indices = list(range(1, len(parsed) + 1, step))[:hard_confusion]
    for idx in hard_indices:
        item = parsed[idx - 1]
        cat = item["category"]
        siblings = [x for x in by_cat[cat] if x[0] != idx]
        if not siblings:
            continue
        sib_idx, sib_item = siblings[(idx + hard_confusion) % len(siblings)]
        hq = hard_confusion_query(item["question"], sib_item["question"])
        rows.append(
            {
                "query": hq,
                "page_index": idx,
                "split": "hard_confusion",
                "paraphrase_id": f"h{idx}",
                "category": cat,
                "question": item["question"],
                "solution": item["solution"],
                "confusion_sibling_page": sib_idx,
            }
        )

    neg_pool = list(dict.fromkeys(NEGATIVE_QUERIES + NEAR_MISS_NEGATIVES))
    for i, nq in enumerate(neg_pool[:negative], start=1):
        rows.append(
            {
                "query": nq,
                "page_index": None,
                "split": "negative",
                "paraphrase_id": f"n{i}",
                "category": None,
                "question": None,
                "solution": None,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RAG eval dataset v3")
    parser.add_argument("--paraphrase-per-faq", type=int, default=4)
    parser.add_argument("--kb-variants", type=int, default=3)
    parser.add_argument("--hard-confusion", type=int, default=80)
    parser.add_argument("--negative", type=int, default=100)
    args = parser.parse_args()

    if not FAQ_PATH.exists():
        raise FileNotFoundError(FAQ_PATH)

    parsed = _parse_faq(FAQ_PATH.read_text(encoding="utf-8"))
    kb = build_kb_v3(parsed, args.kb_variants)
    queries = build_queries_v3(
        parsed,
        paraphrase_per_faq=args.paraphrase_per_faq,
        hard_confusion=args.hard_confusion,
        negative=args.negative,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_KB.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_QUERIES.write_text(json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8")

    n_canonical = sum(1 for r in kb if r["is_canonical"])
    n_variants = len(kb) - n_canonical
    counts = defaultdict(int)
    for r in queries:
        counts[r["split"]] += 1

    print(f"Wrote KB {len(kb)} rows to {OUTPUT_KB}")
    print(f"  canonical={n_canonical} variants={n_variants}")
    print(f"Wrote {len(queries)} queries to {OUTPUT_QUERIES}")
    for split in ("exact", "paraphrase", "hard_confusion", "negative"):
        print(f"  {split}={counts[split]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
