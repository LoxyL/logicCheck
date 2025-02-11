import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

class AIModelAPI:
    def __init__(self, api_key, base_url=None):
        client_params = {
            "api_key": api_key,
        }
        if base_url:
            client_params["base_url"] = base_url
            
        self.client = OpenAI(**client_params)
        
    def generate(self, prompt):
        try:
            config = load_config()
            response = self.client.chat.completions.create(
                model=config.get('MODEL_NAME', 'gpt-4'),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

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
        config = load_config()
        api_key = config['API_KEY']
        base_url = config['API_URL']

        if not api_key:
            raise ValueError("未能从配置文件中读取到API密钥")
            
        self.llm = AIModelAPI(api_key=api_key, base_url=base_url)
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