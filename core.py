"""Local helpers; no network, storage of personal inputs, or model dependency."""
import hashlib
import json
from difflib import SequenceMatcher


def _compact(text):
    return "".join(str(text).split()).lower()


def evidence_in_resume(resume, quote, threshold=0.72):
    """Allow exact or high-similarity evidence matches after whitespace cleanup."""
    if not quote:
        return False
    if quote in resume:
        return True
    clean_resume = _compact(resume)
    clean_quote = _compact(quote)
    if not clean_quote:
        return False
    if clean_quote in clean_resume:
        return True
    if len(clean_quote) < 12:
        return False
    window = len(clean_quote)
    step = max(1, window // 4)
    best = 0
    for start in range(0, max(1, len(clean_resume) - window + 1), step):
        sample = clean_resume[start:start + window]
        best = max(best, SequenceMatcher(None, clean_quote, sample).ratio())
        if best >= threshold:
            return True
    return False


def input_id(resume, jd):
    return hashlib.sha256(json.dumps([resume, jd], ensure_ascii=False).encode()).hexdigest()


def validate_evidence(resume, matches, rewrites):
    """Exact source checks only, not proof that a generated claim is entailed."""
    issues = []
    for i, row in enumerate(matches, 1):
        quote = row.get("evidence", "")
        if quote and not evidence_in_resume(resume, quote):
            issues.append("匹配项 %s 的原文引用无法定位" % i)
    for i, row in enumerate(rewrites, 1):
        if not row.get("before") or not evidence_in_resume(resume, row["before"]):
            issues.append("改写项 %s 的原段落无法定位" % i)
        if not row.get("evidence") or not evidence_in_resume(resume, row["evidence"]):
            issues.append("改写项 %s 的依据无法定位" % i)
    return issues


def report_text(resume, jd, matches, rewrites, answer, questions):
    lines = ["# CareerFit 示例分析", "", "固定虚构示例，人工编写，非实时 AI 分析；改写尚需本人确认。", "", "## 岗位匹配"]
    for row in matches:
        lines += ["", "### " + row["requirement"], row["status"], "原文依据：" + (row["evidence"] or "未提供"), row["note"]]
    lines += ["", "## 改写对照"]
    for row in rewrites:
        lines += ["", "原文：" + row["before"], "建议：" + row["after"], "理由：" + row["why"]]
    lines += ["", "## 申请理由草稿", answer, "", "## 待补充信息"]
    lines += ["- " + q for q in questions]
    lines += ["", "## 本次输入简历", resume, "", "## 本次输入 JD", jd]
    return "\n".join(lines)
