from pathlib import Path
import streamlit as st
from core import input_id, report_text, validate_evidence
from examples import RESUME, JD, MATCHES, REWRITES, ANSWER, QUESTIONS
from live_analysis import analyze, MODEL
import json

st.set_page_config(page_title="CareerFit · 岗位适配助手", page_icon="🧭", layout="wide")
st.markdown("""<style>
.block-container {max-width:1180px;padding-top:2.5rem;}
h1 {letter-spacing:-1px;} .stButton button {border-radius:10px;}
[data-testid="stMetric"] {background:white;border:1px solid #e5eaf2;border-radius:14px;padding:16px;}
</style>""", unsafe_allow_html=True)

def load_example():
    st.session_state.resume = RESUME
    st.session_state.jd = JD
    st.session_state.pop("result_id", None)

def clear_inputs():
    st.session_state.resume = ""
    st.session_state.jd = ""
    st.session_state.pop("result_id", None)

def show_field_table(row):
    if not isinstance(row, dict):
        st.write(row)
        return
    labels = {
        "name": "姓名",
        "phone": "手机",
        "email": "邮箱",
        "location_preference": "期望地点",
        "job_preference": "求职方向",
        "school": "学校",
        "major": "专业",
        "degree": "学历",
        "start_end": "起止时间",
        "courses": "相关课程",
        "company": "公司",
        "department": "部门",
        "role": "角色/岗位",
        "business_context": "业务背景",
        "responsibilities": "工作内容",
        "description": "经历描述",
        "technical": "技能",
        "language": "语言能力",
        "certificates": "证书",
        "self_evaluation": "个人评价",
        "level": "级别",
        "time": "时间",
    }
    rows = [{"字段": labels.get(key, key), "内容": value or "待补充"} for key, value in row.items()]
    st.table(rows)

st.session_state.setdefault("resume", "")
st.session_state.setdefault("jd", "")

with st.sidebar:
    st.markdown("### 🧭 CareerFit")
    st.caption("把真实经历，表达给合适的岗位。")
    st.divider()
    st.markdown("**当前版本 · 示例 + 真实分析**")
    st.write("① 输入简历与岗位\n\n② 查阅匹配证据\n\n③ 检查改写与草稿")
    st.info("查看示例免费。真实分析仅在勾选确认并点击按钮后调用 DeepSeek，按用量计费。")
    with st.expander("开发路线"):
        st.write("已完成：输入界面、固定示例、原文引用检查、修改对照、下载报告。")
        st.write("已接入真实分析接口，尚待实际模型验收。暂不包含网站自动投递。")

st.caption("CAREERFIT / FROM EXPERIENCE TO OPPORTUNITY")
st.title("把简历内容，整理成网申材料。")
st.write("从简历中提取基础信息、教育经历、实习经历、项目经历和技能信息，再结合岗位 JD 生成可复制的填写草稿。")
st.caption("示例模式不上传输入；真实分析将发送两个输入框的内容到 DeepSeek。不预测录用概率。")

a,b,_ = st.columns([2,2,6])
a.button("载入虚构示例", on_click=load_example, use_container_width=True)
b.button("清空本次资料", on_click=clear_inputs, use_container_width=True)
left,right = st.columns(2, gap="large")
with left:
    st.subheader("01 你的简历")
    st.caption("可以更新和编辑。原始简历不会被改写结果覆盖。")
    resume = st.text_area("简历资料", key="resume", height=330, max_chars=20000, placeholder="粘贴教育、实习、项目与技能……")
with right:
    st.subheader("02 目标岗位")
    st.caption("粘贴完整岗位要求。当前版本不抓取网页。")
    jd = st.text_area("岗位描述（JD）", key="jd", height=330, max_chars=12000, placeholder="粘贴岗位职责、任职要求与到岗条件……")

is_example = resume.strip() == RESUME.strip() and jd.strip() == JD.strip()
if st.button("查看示例分析", type="primary", use_container_width=True):
    if not resume.strip() or not jd.strip():
        st.warning("请先载入虚构示例，或填写两个输入框。")
    elif not is_example:
        st.warning("固定示例仅对应内置资料。自定义资料请使用下方“真实分析”。")
    else:
        issues = validate_evidence(resume, MATCHES, REWRITES)
        if issues:
            st.error("示例引用校验未通过：" + "；".join(issues))
        else:
            st.session_state.result_id = input_id(resume, jd)

if st.session_state.get("result_id") and st.session_state.result_id != input_id(resume, jd):
    st.info("输入已变化，旧结果已隐藏。当前示例模式仅支持内置示例。")
elif st.session_state.get("result_id"):
    st.divider()
    st.subheader("03 适配工作台")
    st.info("以下是内置资料对应的固定示例结果，不是 AI 实时生成。")
    c1,c2,c3 = st.columns(3)
    c1.metric("岗位要求", len(MATCHES))
    c2.metric("有直接证据", sum(m["status"] == "有直接证据" for m in MATCHES))
    c3.metric("待补充问题", len(QUESTIONS))
    st.caption("数量描述证据覆盖，不代表匹配分数或录用概率。")
    tabs = st.tabs(["网申基础资料", "岗位匹配", "简历改写对照", "网申回答草稿"])
    with tabs[0]:
        st.caption("以下资料按内置虚构简历人工整理，尚未接入自动提取。未提供的字段保持待补充。")
        st.markdown("#### 基本信息")
        st.table({"字段": ["姓名", "手机", "邮箱", "期望城市", "岗位方向", "可到岗时间"],
                  "内容": ["林夏（虚构示例）", "待补充", "待补充", "北京、上海", "新媒体运营、直播运营、用户运营", "待补充"]})
        st.markdown("#### 教育经历")
        st.table({"学校": ["示例大学"], "专业": ["新闻传播"], "学历": ["本科"], "起止时间": ["2023.09—2027.06"]})
        st.markdown("#### 实习经历")
        st.write("**青柚生活｜新媒体运营实习生｜2026.06—2026.08**")
        st.write(RESUME.split("2026.06—2026.08\n", 1)[1].split("\n\n", 1)[0])
        st.markdown("#### 项目经历")
        st.write("**校园音乐节宣传｜课程项目｜2026.03—2026.05**")
        st.write("负责活动预热推文和社群通知，设计报名提醒文案，协助完成现场志愿者沟通。")
        st.markdown("#### 技能")
        st.write("公众号排版；小红书内容运营；Excel 数据整理；基础海报制作。")
        st.caption("后续将支持从用户最新简历提取、多段教育与实习经历，以及逐项编辑确认。")
    with tabs[1]:
        for i,m in enumerate(MATCHES, 1):
            with st.container(border=True):
                st.markdown("**%s. %s** — %s" % (i, m["requirement"], m["status"]))
                if m["evidence"]:
                    st.caption("可定位的简历原文")
                    st.write(m["evidence"])
                st.write(m["note"])
        st.markdown("#### 需要你补充")
        for q in QUESTIONS:
            st.write("• " + q)
    with tabs[2]:
        st.caption("这是段落建议，不是已经核准的最终简历。保留原文，逐条检查。")
        for i,r in enumerate(REWRITES, 1):
            with st.container(border=True):
                st.markdown("**修改 %s**" % i)
                old,new = st.columns(2)
                old.caption("原文")
                old.write(r["before"])
                new.caption("建议改写")
                new.write(r["after"])
                st.caption("修改理由：" + r["why"])
        st.warning("原文引用匹配只能证明引用存在，不能自动证明每个改写结论都成立。")
    with tabs[3]:
        st.markdown("#### 为什么申请这个岗位？")
        st.caption("限200字示例 · 以字符数计算，包含标点")
        st.write(ANSWER)
        st.caption("当前 %s / 200 字符 · %s" % (len(ANSWER), "符合限制" if len(ANSWER)<=200 else "超过限制"))
        st.write("依据：内容发布、直播活动跟进、评论反馈整理和运营周报。未替用户承诺到岗时间。")
    st.download_button("下载本次示例报告 · Markdown", report_text(resume,jd,MATCHES,REWRITES,ANSWER,QUESTIONS), file_name="careerfit-demo-report.md", mime="text/markdown", use_container_width=True)
else:
    st.markdown("---")
    st.markdown("**先点击「载入虚构示例」，再点击「查看示例分析」。**")
    st.caption("也可以填写自己的资料，再使用下方真实分析。")

st.divider()
st.subheader("真实分析")
st.caption("模型：" + MODEL + " · 一次点击一次请求 · 不自动重试 · 输出最多5000 Token")
consent = st.checkbox("我同意将上方简历和岗位要求发送给 DeepSeek，了解本次调用可能产生费用。", key="live_consent")
if st.button("开始真实分析", disabled=not consent, type="primary"):
    st.session_state.pop("live_result", None)
    try:
        key = st.secrets.get("DEEPSEEK_API_KEY", "").strip()
        if not key or key == "在这里粘贴你的密钥":
            raise ValueError("请先在本地 secrets.toml 中配置密钥")
        with st.spinner("正在分析，请等待；不会自动重复请求……"):
            data, usage = analyze(resume, jd, key)
        st.session_state.live_result = (input_id(resume, jd), data, usage)
    except ValueError as exc:
        st.error(str(exc))
        st.caption("未自动重试。若请求已到达模型，格式或引用校验失败也可能计费。")
    except Exception:
        st.error("配置或请求异常。请检查本地配置；未自动重试。不要分享密钥或配置文件截图。")

live = st.session_state.get("live_result")
if live and live[0] != input_id(resume, jd):
    st.info("资料已更新，旧的真实分析结果已隐藏。")
elif live:
    _, data, usage = live
    warnings = data.get("warnings", [])
    if warnings:
        st.warning("真实分析已返回，部分字段或证据需要人工核对。")
        with st.expander("查看需核对项"):
            for item in warnings:
                st.write("• " + item)
    else:
        st.success("真实分析已返回；仍需本人核对事实及填写内容。")
    st.caption("输入 Token：%s · 输出 Token：%s；实际费用请查看 DeepSeek 账单。" % (usage.get('prompt_tokens','未返回'), usage.get('completion_tokens','未返回')))
    info_tab, edu_tab, exp_tab, project_tab, campus_tab, award_tab, skill_tab, answer_tab = st.tabs(["基础信息", "教育经历", "实习经历", "项目经历", "学生工作", "竞赛奖项", "技能语言", "网申回答"])
    with info_tab:
        info = data.get("basic_info", {})
        rows = [{"字段": k, "内容": v} for k, v in info.items()]
        st.table(rows or [{"字段": "暂无", "内容": "待补充"}])
    with edu_tab:
        for i, row in enumerate(data.get("education", []), 1):
            with st.container(border=True):
                st.markdown("**教育经历 %s**" % i)
                show_field_table(row)
        if not data.get("education"):
            st.info("未提取到教育经历。")
    with exp_tab:
        for i, row in enumerate(data.get("internships", []), 1):
            with st.container(border=True):
                st.markdown("**实习经历 %s**" % i)
                show_field_table(row)
        if not data.get("internships"):
            st.info("未提取到实习经历。")
    with project_tab:
        for i, row in enumerate(data.get("projects", []), 1):
            with st.container(border=True):
                st.markdown("**项目经历 %s**" % i)
                show_field_table(row)
        if not data.get("projects"):
            st.info("未提取到项目经历。")
    with campus_tab:
        for i, row in enumerate(data.get("campus_experience", []), 1):
            with st.container(border=True):
                st.markdown("**学生工作/校园经历 %s**" % i)
                show_field_table(row)
        if not data.get("campus_experience"):
            st.info("未提取到学生工作或校园经历。")
    with award_tab:
        for i, row in enumerate(data.get("awards", []), 1):
            with st.container(border=True):
                st.markdown("**竞赛/奖项 %s**" % i)
                show_field_table(row)
        if not data.get("awards"):
            st.info("未提取到竞赛或奖项。")
    with skill_tab:
        show_field_table(data.get("skills", {}) or {"技能": "待补充"})
        st.markdown("#### 需要补充")
        for question in data.get("questions", []):
            st.write("• " + question)
    with answer_tab:
        answers = data.get("application_answers", [])
        for i, row in enumerate(answers, 1):
            with st.container(border=True):
                st.markdown("**回答草稿 %s**" % i)
                st.caption(row.get("question", "网申问题"))
                st.write(row.get("answer", ""))
        if not answers:
            st.info("未生成开放题草稿。")
    st.download_button("下载真实分析结果（JSON）", json.dumps(data, ensure_ascii=False, indent=2), file_name="careerfit-analysis.json", mime="application/json")

st.divider()
st.subheader("04 网申填写 · 功能预告")
st.text_input("目标岗位网申链接", placeholder="粘贴公司官网的岗位申请页面链接", key="application_url")
st.button("一键填写网申（尚未接入）", disabled=True, use_container_width=True)
st.caption("当前仅预留入口，填写链接不会访问网站或发送资料。后续计划：登录官网 → 自动填写 → 本人核对 → 确认提交。具体网站支持情况需逐站验证。")

with st.expander("这个项目怎样工作？"):
    st.write("当前：固定虚构资料 → 读取人工示例结果 → 原文引用校验 → 页面展示与导出。")
    st.write("真实分析：用户简历 + JD → 一次模型调用 → 结构检查与引用校验 → 用户审核。")
    st.caption("引用检查只能确认原文存在，不能证明模型理解或改写完全正确。")
