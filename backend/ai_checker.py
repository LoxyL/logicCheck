import json
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from .ai_model_api import AIModelAPI

load_dotenv()

def load_config():
    config = {}
    with open('backend/config.txt', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config

class AIChecker:
    def __init__(self):
        self.api_base = None
        self.api_key = None
        self.model = None
        self.prompt_template = PromptTemplate(
            input_variables=["text"],
            template=u"""请检查以下教育材料中的错误，仅关注：
1. 错别字
2. 严重的语句不通顺问题（仅标记真正难以理解或读起来很不通顺的句子，不要标记仅需优化的句子）

注意事项：
- 只有当句子读起来确实很困难，或者表达严重不清时，才标记为"语句不通顺"
- 对于可以理解但表达不够优美的句子，不要标记
- 错别字必须是确定的错误，不要标记可能的同音字或习惯用法
- 大部分文本可能不需要任何修改

文本内容:
\"{text}\"

如果发现错误，请以JSON数组格式返回，每个错误对象包含：
- type: 错误类型（"错别字"或"语句不通顺"）
- location: 错误位置
- original: 原文内容
- suggestion: 修改建议

如果没有发现需要修改的错误，请返回空数组 []。
"""
        )

    def set_api_config(self, api_base, api_key, model):
        """设置API配置"""
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
            
        self.llm = AIModelAPI(model=self.model, api_key=self.api_key, base_url=self.api_base)

    def check_content(self, text_segments):
        """处理分段后的文本，使用生成器实时返回结果"""
        for segment in text_segments:
            try:
                prompt = self.prompt_template.format(text=segment['text'])
                response = self.llm.generate(prompt)
                errors = self._parse_response(response)
                # 无论是否有错误都返回结果
                yield {
                    'segment': segment,
                    'errors': errors
                }
            except Exception as e:
                print(f"处理文本段落时出错: {str(e)}")
                continue
    
    def _split_text(self, text, chunk_size=1000):
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    def _parse_response(self, response):
        try:
            response = response.strip('```json').strip('```')
            errors = json.loads(response)
            if not isinstance(errors, list):
                return []

            return errors
        except json.JSONDecodeError:
            print("AI响应解析失败:", response)
            return []