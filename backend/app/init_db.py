"""数据库初始化与种子数据。对应文档 03 §3、文档 06 T-1.2。

首次启动时建表；若学科表为空，则预置两个学科及若干知识点、
笔记、题目、卡片与依赖关系，便于演示与验收（文档 07 手工清单）。
"""
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import json

from .db import Base, engine, SessionLocal
from . import models  # noqa: F401  确保全部模型注册到 metadata
from .services.numbering import parse_chapter_section


def init_db() -> None:
    """建表（幂等），并对已有表补齐新增列（轻量迁移，保留数据）。"""
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate() -> None:
    """用 ALTER TABLE 补齐新增列，并归一化题型（SQLite 无原生迁移，用此兼容）。"""
    insp = inspect(engine)
    with engine.connect() as conn:
        if insp.has_table("questions"):
            existing = {c["name"] for c in insp.get_columns("questions")}
            adds_questions = {
                "core_idea": "TEXT",
                "steps": "TEXT",
                "image_path": "TEXT",
                "source": "VARCHAR(20)",
                "number": "VARCHAR(50)",
                "chapter": "INTEGER",
                "section": "INTEGER",
                "traps": "TEXT",
            }
            for col, typ in adds_questions.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE questions ADD COLUMN {col} {typ}"))
            # 旧题型(single/multi/judge/subjective) 归一为 calculation（计算）
            conn.execute(text("UPDATE questions SET qtype='calculation' WHERE qtype NOT IN ('calculation','proof')"))
            conn.commit()
        if insp.has_table("math_entries"):
            existing_e = {c["name"] for c in insp.get_columns("math_entries")}
            adds_entry = {
                "solve_type": "VARCHAR(20)",
                "chapter": "INTEGER",
                "section": "INTEGER",
                "traps": "TEXT",
            }
            for col, typ in adds_entry.items():
                if col not in existing_e:
                    conn.execute(text(f"ALTER TABLE math_entries ADD COLUMN {col} {typ}"))
            conn.execute(text("UPDATE math_entries SET solve_type='calculation' WHERE solve_type IS NULL OR solve_type=''"))
            conn.commit()
        _backfill_chapters()


def _backfill_chapters() -> None:
    """从已有的 number（如 6.2.2）反推 chapter/section，补全历史数据。"""
    with SessionLocal() as db:
        for entry in db.query(models.MathEntry).filter(
            models.MathEntry.chapter.is_(None), models.MathEntry.number.isnot(None)
        ).all():
            ch, sec = parse_chapter_section(entry.number)
            if ch is not None:
                entry.chapter, entry.section = ch, sec
                db.add(entry)
        for q in db.query(models.Question).filter(
            models.Question.chapter.is_(None), models.Question.number.isnot(None)
        ).all():
            ch, sec = parse_chapter_section(q.number)
            if ch is not None:
                q.chapter, q.section = ch, sec
                db.add(q)
        db.commit()


def seed_if_empty(db: Session) -> None:
    """若没有任何学科，则写入种子数据。"""
    if db.query(models.Subject).count() > 0:
        return

    math_analysis = models.Subject(name="数学分析", description="极限、微积分、级数、多元函数等")
    linear_algebra = models.Subject(name="高等代数/线性代数", description="矩阵、线性空间、多项式、特征值等")
    db.add_all([math_analysis, linear_algebra])
    db.commit()
    db.refresh(math_analysis)
    db.refresh(linear_algebra)

    # ---------- 数学分析 知识点 ----------
    kp_limit = models.KnowledgePoint(subject_id=math_analysis.id, name="极限的定义",
                                     description="$\\lim_{x\\to x_0} f(x)=A$ 的 $\\varepsilon$-$\\delta$ 语言")
    kp_conv_principle = models.KnowledgePoint(subject_id=math_analysis.id, name="柯西收敛准则",
                                              description="数列收敛充要条件：对任意 $\\varepsilon>0$，存在 $N$，当 $m,n>N$ 时 $|a_m-a_n|<\\varepsilon$")
    kp_derivative = models.KnowledgePoint(subject_id=math_analysis.id, name="导数与微分",
                                          description="$f'(x_0)=\\lim_{\\Delta x\\to0}\\frac{f(x_0+\\Delta x)-f(x_0)}{\\Delta x}$")
    kp_integral = models.KnowledgePoint(subject_id=math_analysis.id, name="定积分",
                                        description="黎曼和的极限：$\\int_a^b f(x)dx=\\lim_{\\lambda\\to0}\\sum f(\\xi_i)\\Delta x_i$")
    db.add_all([kp_limit, kp_conv_principle, kp_derivative, kp_integral])
    db.commit()
    for kp in (kp_limit, kp_conv_principle, kp_derivative, kp_integral):
        db.refresh(kp)

    # 依赖：极限 -> 导数 -> 定积分；极限 -> 柯西收敛准则
    db.add_all([
        models.KnowledgeRelation(source_id=kp_limit.id, target_id=kp_derivative.id),
        models.KnowledgeRelation(source_id=kp_derivative.id, target_id=kp_integral.id),
        models.KnowledgeRelation(source_id=kp_limit.id, target_id=kp_conv_principle.id),
    ])

    # ---------- 高等代数 知识点 ----------
    kp_matrix = models.KnowledgePoint(subject_id=linear_algebra.id, name="矩阵运算",
                                      description="矩阵加法、乘法、转置；$\\det(AB)=\\det A\\cdot\\det B$")
    kp_vector_space = models.KnowledgePoint(subject_id=linear_algebra.id, name="线性空间",
                                            description="向量空间的定义、基与维数")
    kp_eigen = models.KnowledgePoint(subject_id=linear_algebra.id, name="特征值与特征向量",
                                     description="$Av=\\lambda v$，特征多项式 $\\det(A-\\lambda I)=0$")
    db.add_all([kp_matrix, kp_vector_space, kp_eigen])
    db.commit()
    for kp in (kp_matrix, kp_vector_space, kp_eigen):
        db.refresh(kp)
    db.add(models.KnowledgeRelation(source_id=kp_matrix.id, target_id=kp_eigen.id))

    # ---------- 笔记 ----------
    note1 = models.Note(subject_id=math_analysis.id, title="极限的 ε-δ 定义笔记", content=(
        "# 极限的定义\n\n"
        "设函数 $f(x)$ 在 $x_0$ 的某去心邻域有定义。\n\n"
        "$\\lim_{x\\to x_0} f(x) = A$ 当且仅当：\n\n"
        "$$\\forall \\varepsilon > 0,\\ \\exists \\delta > 0,\\ 0<|x-x_0|<\\delta \\Rightarrow |f(x)-A|<\\varepsilon$$\n\n"
        "**要点**：$\\delta$ 依赖 $\\varepsilon$；思考时先给定误差，再找邻域半径。"
    ))
    note1.tags = [models.Tag(name="极限"), models.Tag(name="ε-δ")]
    note1.knowledge_points = [kp_limit]

    note2 = models.Note(subject_id=linear_algebra.id, title="特征值与特征向量", content=(
        "# 特征值与特征向量\n\n"
        "设 $A$ 为 $n$ 阶方阵，若存在非零向量 $v$ 与数 $\\lambda$ 使\n\n"
        "$$Av=\\lambda v$$\n\n"
        "则 $\\lambda$ 为**特征值**，$v$ 为对应**特征向量**。\n\n"
        "求法：解特征方程 $\\det(A-\\lambda I)=0$ 得特征值，再解 $(A-\\lambda I)v=0$ 得特征向量。"
    ))
    note2.knowledge_points = [kp_eigen]
    db.add_all([note1, note2])

    # ---------- 题目 ----------
    q1 = models.Question(
        subject_id=math_analysis.id, qtype="proof", difficulty=2,
        content="若 $\\lim_{x\\to x_0} f(x)$ 存在，则 $f$ 在 $x_0$ 处必定有定义。",
        answer="错",
        explanation="极限存在只要求 $f$ 在 $x_0$ 的去心邻域有定义，与 $x_0$ 处是否定义无关。",
    )
    q2 = models.Question(
        subject_id=linear_algebra.id, qtype="calculation", difficulty=3,
        content="求矩阵 $A=\\begin{pmatrix}2&1\\\\1&2\\end{pmatrix}$ 的特征值。",
        answer="$\\lambda_1=1,\\ \\lambda_2=3$",
        explanation="解特征方程 $\\det(A-\\lambda I)=\\lambda^2-4\\lambda+3=0$，得特征值 $1,3$。",
    )
    q3 = models.Question(
        subject_id=math_analysis.id, qtype="calculation", difficulty=3,
        content="计算定积分 $\\int_0^1 x^2\\,dx$。",
        answer="$\\frac{1}{3}$",
        explanation="$\\int_0^1 x^2 dx=[\\frac{x^3}{3}]_0^1=\\frac{1}{3}$。",
    )
    q1.knowledge_points = [kp_limit]
    q2.knowledge_points = [kp_eigen]
    q3.knowledge_points = [kp_integral]
    db.add_all([q1, q2, q3])

    # ---------- 卡片 ----------
    card1 = models.Card(
        subject_id=math_analysis.id, front="柯西收敛准则的内容是什么？",
        back="数列 $\\{a_n\\}$ 收敛 $\\iff$ 对任意 $\\varepsilon>0$，存在 $N$，当 $m,n>N$ 时 $|a_m-a_n|<\\varepsilon$。",
    )
    card2 = models.Card(
        subject_id=linear_algebra.id, front="什么是特征值？",
        back="若存在非零向量 $v$ 与数 $\\lambda$ 使 $Av=\\lambda v$，则 $\\lambda$ 为 $A$ 的特征值。",
    )
    card1.knowledge_points = [kp_conv_principle]
    card2.knowledge_points = [kp_eigen]
    db.add_all([card1, card2])

    db.commit()


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
