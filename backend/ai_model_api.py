from openai import OpenAI

class AIModelAPI:
    def __init__(self, model, api_key, base_url=None):
        self.model = model
        client_params = {
            "api_key": api_key,
        }
        if base_url:
            client_params["base_url"] = base_url
            
        self.client = OpenAI(**client_params)
        
    def generate(self, prompt, temperature=0):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}") 