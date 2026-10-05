"""One explicit HTTPS request; no retries or credential logging."""
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from core import validate_evidence

MODEL = 'deepseek-flash'

SCHEMA = '''仅输出 JSON 对象：
{"profile":[{"section":"基本信息/教育经历/实习经历/项目经历/技能","field":"字段名称（多段经历注明序号）","value":"内容或待补充","evidence":"简历逐字原文；待补充时为空"}],
"matches":[{"requirement":"岗位要求","status":"有直接证据/部分证据/未找到证据/需要确认","evidence":"逐字原文或空字符串","note":"理由"}],
"rewrites":[{"before":"简历中连续原文","after":"改写建议","evidence":"简历逐字原文","why":"修改理由"}],
"answer":"为什么申请该岗位的草稿，不超过200字符（含标点）",
"questions":["待确认问题"]}
所有字段必填，列表无内容可为空。基础资料覆盖学校、学历、专业、日期、各段实习和项目。缺失电话和邮箱填待补充，不输出证件号码。不要省略经历，不新增事实。最多改写3段。'''


def check_result(data, resume):
    if not isinstance(data, dict):
        raise ValueError('返回内容不是结构化报告')
    fields = {'profile': ('section','field','value','evidence'), 'matches': ('requirement','status','evidence','note'), 'rewrites': ('before','after','evidence','why')}
    for name, keys in fields.items():
        rows = data.get(name)
        if not isinstance(rows, list):
            raise ValueError('缺少报告字段：' + name)
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in keys):
                raise ValueError('报告字段格式错误：' + name)
    if not isinstance(data.get('answer'), str) or len(data['answer']) > 200:
        raise ValueError('回答格式不正确或超过200字符')
    if not isinstance(data.get('questions'), list) or any(not isinstance(q, str) for q in data['questions']):
        raise ValueError('待确认问题格式不正确')
    issues = validate_evidence(resume, data['matches'], data['rewrites'])
    for row in data['profile']:
        if row['value'] != '待补充' and not row['evidence']:
            issues.append('基础资料缺少原文依据')
        if row['evidence'] and row['evidence'] not in resume:
            issues.append('基础资料引用无法定位')
    for row in data['matches']:
        if row['status'] not in ('有直接证据','部分证据','未找到证据','需要确认'):
            issues.append('匹配状态不正确')
        if row['status'] in ('有直接证据','部分证据') and not row['evidence']:
            issues.append('匹配结论缺少依据')
    if issues:
        raise ValueError('；'.join(issues))
    return data


def analyze(resume, jd, key):
    if not resume.strip() or not jd.strip() or len(resume)>20000 or len(jd)>12000:
        raise ValueError('请填写简历与岗位要求，并保持在输入长度限制内')
    rules = (Path(__file__).parent / 'prompts' / 'analysis.md').read_text()
    payload = {'model': MODEL, 'messages': [{'role':'system','content':rules+'\n'+SCHEMA}, {'role':'user','content':json.dumps({'resume':resume,'jd':jd}, ensure_ascii=False)}], 'thinking':{'type':'disabled'}, 'response_format':{'type':'json_object'}, 'max_tokens':5000, 'stream':False}
    request = Request('https://api.deepseek.com/chat/completions', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json','Authorization':'Bearer '+key}, method='POST')
    try:
        with urlopen(request, timeout=90) as response:
            raw = json.load(response)
    except HTTPError as exc:
        messages = {401:'密钥无效，请在本地检查配置',402:'账户余额不足，请到开放平台查看余额',429:'请求受限，请稍后手动再试'}
        raise ValueError(messages.get(exc.code, '服务请求失败，状态码 %s' % exc.code)) from None
    except (URLError, TimeoutError, OSError):
        raise ValueError('连接失败或超时，未自动重试；可先查看平台用量，确认是否已计费') from None
    try:
        choice = raw['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('报告未完整生成，可能已产生费用；未自动重试')
        data = check_result(json.loads(choice['message']['content']), resume)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ValueError('模型返回格式异常，可能已产生费用；未自动重试') from None
    return data, raw.get('usage', {})
