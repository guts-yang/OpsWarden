"""填写 测试文档.doc：各章节正文 + 2.4 用例表格 + 嵌入截图。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_cases_data import TEST_CASES, image_path

DOC_PATH = Path(__file__).resolve().parent.parent / "测试文档.doc"
OUT_PATH = DOC_PATH.parent / "测试文档_已填写_v3.doc"

WD_COLLAPSE_END = 0
IMG_WIDTH_CM = 15.5  # 适配 A4 页宽

SECTIONS: list[tuple[str, str]] = [
    (
        "1.1 编写目的",
        "本文档是 OpsWarden 运维数字员工平台的系统测试说明，用于指导测试人员进行功能验证、接口联调与验收。文档描述测试环境、测试策略、测试用例及测试过程记录，为课程设计交付与质量评估提供依据。",
    ),
    (
        "1.2 测试目标",
        "（1）验证用户认证与三级角色权限（admin / operator / user）是否正确生效；\n"
        "（2）验证 AI 问答核心流程：知识库命中、未命中降级、用户确认后建单；\n"
        "（3）验证工单全生命周期：创建、指派、处理、解决、回访、关闭及操作日志；\n"
        "（4）验证知识库 CRUD、工单回写知识库及向量化检索能力；\n"
        "（5）验证账号管理（创建、冻结/解冻、重置密码）与仪表盘统计功能；\n"
        "（6）验证 Docker 部署环境下前后端联调可用性。",
    ),
    (
        "1.3 测试环境",
        "【硬件环境】CPU x86_64 多核；内存 ≥ 8GB；硬盘 ≥ 10GB。\n"
        "【软件环境】Python 3.11 + FastAPI；PostgreSQL 16 + pgvector；Ollama qwen2.5:1.5b；Vue 3 + Vite 6。\n"
        "【访问地址】体验站 http://119.29.191.248:8080；本地前端 http://localhost:5173，后端 http://localhost:8000。\n"
        "【测试账号】admin / admin123；普通用户 dingkp；运维 Icy / lcy。",
    ),
    (
        "1.4 测试人员",
        "组长：廖晨扬（AI 问答 / RAG）；组员：吴雨彤（账号/工单/知识库）；组员：丁其彬（Docker 部署）；指导教师：苏锦钿。",
    ),
    (
        "1.5 参考材料",
        "README.md、docs/API_TESTING.md、docs/TECHNICAL.md、GitHub：https://github.com/guts-yang/OpsWarden。",
    ),
    (
        "2.1测试数据准备",
        "（1）管理员 admin；（2）operator 账号 lcy/运维张工；（3）user 账号 dingkp；"
        "（4）FAQ 约 100 条自动导入；（5）测试工单与知识库回写数据。",
    ),
    (
        "2.2测试策略",
        "黑盒测试 + 浏览器手工测试：逐模块验证登录、AI 问答、工单、知识库、账号、仪表盘。",
    ),
    (
        "2.3测试原则",
        "独立性、可重复性、完整性、安全性（鉴权/冻结/越权）、业务合规（未命中不静默建单）。",
    ),
    (
        "测试过程(dqb)",
        "测试时间：2026 年 6–7 月。方式：体验站 http://119.29.191.248:8080 手工测试。\n"
        "阶段一：环境与登录冒烟；阶段二：AI 问答命中/未命中/建单；阶段三：工单与知识库回写；"
        "阶段四：账号权限与仪表盘统计。全部 13 项用例通过。",
    ),
    (
        "4、结论(dqb)",
        "经测试，OpsWarden 各核心模块运行稳定，实现 RAG+Ollama 问答、工单闭环、知识库自学习、"
        "三级权限与统计仪表盘，达到可演示可交付标准。测试结论：通过。",
    ),
    (
        "5、其他(dqb)",
        "（1）日志：backend/app.log；（2）已知问题：短文本回写后检索分数可能低于阈值 0.65；"
        "（3）GitHub：https://github.com/guts-yang/OpsWarden。",
    ),
]


def _norm(text: str) -> str:
    return text.replace("\r", "").replace("\x07", "").strip()


def _insert_images(doc, rng, image_names: list[str]) -> None:
    wd_collapse_end = WD_COLLAPSE_END
    for name in image_names:
        path = image_path(name)
        if not path.exists():
            rng.InsertAfter(f"[缺少截图：{name}]\r")
            rng.Collapse(wd_collapse_end)
            continue
        rng.InsertAfter(f"截图（{name}）：\r")
        rng.Collapse(wd_collapse_end)
        pic = doc.InlineShapes.AddPicture(
            FileName=str(path.resolve()),
            LinkToFile=False,
            SaveWithDocument=True,
            Range=rng,
        )
        width_pt = IMG_WIDTH_CM * 28.3465
        if pic.Width > width_pt:
            ratio = width_pt / pic.Width
            pic.Width = width_pt
            pic.Height = pic.Height * ratio
        rng = pic.Range
        rng.Collapse(wd_collapse_end)
        rng.InsertAfter("\r")
        rng.Collapse(wd_collapse_end)


def _fill_test_cases_section(doc, heading_idx: int) -> None:
    rng = doc.Paragraphs(heading_idx).Range
    rng.Collapse(WD_COLLAPSE_END)

    for tc in TEST_CASES:
        rng.InsertAfter(f"\r{tc['id']} {tc['title']}\r")
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertAfter(f"目的：{tc['purpose']}\r")
        rng.Collapse(WD_COLLAPSE_END)

        steps = tc["steps"]
        table = doc.Tables.Add(rng, 1 + len(steps), 3)
        for col, header in enumerate(["步骤", "操作", "预期结果"], start=1):
            table.Cell(1, col).Range.Text = header
        for row, (step_no, action, expected) in enumerate(steps, start=2):
            table.Cell(row, 1).Range.Text = step_no
            table.Cell(row, 2).Range.Text = action
            table.Cell(row, 3).Range.Text = expected

        rng = table.Range
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertAfter(f"测试结果：{tc['result']}\r")
        rng.Collapse(WD_COLLAPSE_END)
        _insert_images(doc, rng, tc.get("images", []))

    print(f"filled: 2.4测试用例设计 (TC-01 ~ TC-{len(TEST_CASES):02d})")


def _fill_paragraphs(doc) -> None:
    headings = {h: c for h, c in SECTIONS}
    targets: list[tuple[int, str, str]] = []
    tc_heading_idx: int | None = None

    for i in range(1, doc.Paragraphs.Count + 1):
        title = _norm(doc.Paragraphs(i).Range.Text)
        if title == "2.4测试用例设计":
            tc_heading_idx = i
            continue
        if title in headings:
            targets.append((i, title, headings[title]))

    for i, title, body in reversed(targets):
        nxt = i + 1
        if nxt <= doc.Paragraphs.Count:
            try:
                doc.Paragraphs(nxt).Range.Text = body + "\r"
                print(f"filled: {title}")
            except Exception as exc:
                print(f"WARN: skip {title}: {exc}", file=sys.stderr)

    if tc_heading_idx is not None:
        for i in range(1, doc.Paragraphs.Count + 1):
            if _norm(doc.Paragraphs(i).Range.Text) == "2.4测试用例设计":
                _fill_test_cases_section(doc, i)
                break


def main() -> None:
    if not DOC_PATH.exists():
        raise SystemExit(f"文件不存在: {DOC_PATH}")

    import win32com.client

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(str(DOC_PATH.resolve()))
    try:
        _fill_paragraphs(doc)
        out = OUT_PATH
        if out.exists():
            try:
                out.unlink()
            except OSError:
                out = DOC_PATH.parent / "测试文档_已填写_v3_new.doc"
        doc.SaveAs2(str(out.resolve()), FileFormat=0)
        print(f"saved: {out}")
    finally:
        doc.Close(SaveChanges=False)
        word.Quit()


if __name__ == "__main__":
    main()
