"""One explicit HTTPS request; no retries or credential logging."""
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MODEL = 'deepseek-flash'

SCHEMA = '''仅输出 JSON 对象：
{
  "basic_info": {
    "name": "",
    "phone": "",
    "email": "",
    "location_preference": "",
    "job_preference": ""
  },
  "education": [
    {
      "school": "",
      "major": "",
      "degree": "",
      "start_end": "",
      "courses": ""
    }
  ],
  "internships": [
    {
      "company": "",
      "department": "",
      "role": "",
      "start_end": "",
      "business_context": "",
      "responsibilities": ""
    }
  ],
  "projects": [
    {
      "name": "",
      "role": "",
      "start_end": "",
      "description": ""
    }
  ],
  "campus_experience": [
    {
      "name": "",
      "role": "",
      "start_end": "",
      "description": ""
    }
  ],
  "awards": [
    {
      "name": "",
      "level": "",
      "time": "",
      "description": ""
    }
  ],
  "skills": {
    "technical": "",
    "language": "",
    "certificates": "",
    "self_evaluation": ""
  },
  "application_answers": [
    {
      "question": "",
      "answer": ""
    }
  ],
  "questions": []
}
缺失字段填“待补充”。不要输出身份证号等敏感证件号码。不要新增事实。学生工作、社团、志愿者、校园活动放入 campus_experience；竞赛、奖项、荣誉放入 awards；自我评价放入 skills.self_evaluation。JD 只用于生成开放题草稿和待补充问题。application_answers 至少包含个人评价/自我介绍、岗位匹配理由两个常见网申草稿。'''


def check_result(data, resume):
    if not isinstance(data, dict):
        raise ValueError('返回内容不是结构化报告')

    required = [
        'basic_info',
        'education',
        'internships',
        'projects',
        'campus_experience',
        'awards',
        'skills',
        'application_answers',
        'questions',
    ]
    for name in required:
        if name not in data:
            raise ValueError('缺少报告字段：' + name)

    if not isinstance(data['basic_info'], dict):
        raise ValueError('基础信息格式错误')
    if not isinstance(data['education'], list):
        raise ValueError('教育经历格式错误')
    if not isinstance(data['internships'], list):
        raise ValueError('实习经历格式错误')
    if not isinstance(data['projects'], list):
        raise ValueError('项目经历格式错误')
    if not isinstance(data['campus_experience'], list):
        raise ValueError('学生工作格式错误')
    if not isinstance(data['awards'], list):
        raise ValueError('竞赛奖项格式错误')
    if not isinstance(data['skills'], dict):
        raise ValueError('技能信息格式错误')
    if not isinstance(data['application_answers'], list):
        raise ValueError('网申回答格式错误')
    if not isinstance(data['questions'], list) or any(not isinstance(q, str) for q in data['questions']):
        raise ValueError('待确认问题格式不正确')

    data['warnings'] = []
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
