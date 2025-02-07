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
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

class AIChecker:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE_URL")
        api_key = "hk-piidk61000036048c6e26ccd2f9cba72db0ca084190047f5"
        base_url = "https://api.openai-hk.com/v1"

        if not api_key:
            raise ValueError("请设置OPENAI_API_KEY环境变量")
            
        self.llm = AIModelAPI(api_key=api_key, base_url=base_url)
        self.prompt_template = PromptTemplate(
            input_variables=["text"],
            template=u"请检查以下教育材料中的错误，包括:\n"
                    u"1. 逻辑错误\n"
                    u"2. 错别字\n"
                    u"3. 语句不通顺\n\n"
                    u"文本内容:\n"
                    u"\"{text}\"\n\n"
                    u"请以JSON数组格式返回发现的错误，每个错误对象包含type(错误类型)、"
                    u"location(错误位置)、original(原文内容)、suggestion(修改建议)字段。"
        )

    def check_content(self, text_segments):
        """处理分段后的文本，使用生成器实时返回结果"""
        for segment in text_segments:
            try:
                prompt = self.prompt_template.format(text=segment['text'])
                response = self.llm.generate(prompt)
                errors = self._parse_response(response)
                if errors:
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