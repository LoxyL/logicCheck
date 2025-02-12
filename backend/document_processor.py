from docx import Document
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from openai import OpenAI
import re
import json
from ai_model_api import AIModelAPI

class DocumentProcessor:
    def __init__(self):
        self.api_base = None
        self.api_key = None
        self.model = None
        
        # 更新分析提示，要求更精确的结构分析
        self.structure_prompt = PromptTemplate(
            input_variables=["text"],
            template=(
                "请详细分析以下教育材料的文本结构，需要精确到字符级别的分析。\n\n"
                "文本内容:\n{text}\n\n"
                "请返回JSON格式的分析结果，包含以下信息：\n"
                "1. doc_type: 文档类型（例如：题目解析集/要点总结/知识点讲解等）\n"
                "2. structure: 文档结构分析，包含：\n"
                "   - segments: 分段标记列表，每个标记包含：\n"
                "     * pattern: 分段标记的正则表达式\n"
                "     * type: 标记类型（如：序号/标题/小节等）\n"
                "     * level: 层级（1为最高层，数字越大层级越低）\n"
                "3. special_markers: 特殊标记列表（如：例题/解答/证明等）\n\n"
                "示例返回格式：\n"
                "{{\n"
                '    "doc_type": "题目解析集",\n'
                '    "structure": {{\n'
                '        "segments": [\n'
                '            {{"pattern": "^\\\\d+\\\\.", "type": "题目", "level": 1}},\n'
                '            {{"pattern": "^\\\\(\\\\d+\\\\)", "type": "小问", "level": 2}},\n'
                '            {{"pattern": "^[A-Z]\\\\.", "type": "选项", "level": 3}}\n'
                '        ]\n'
                '    }},\n'
                '    "special_markers": ["解答：", "解析：", "证明："]\n'
                "}}\n"
            )
        )

    def set_api_config(self, api_base, api_key, model):
        """设置API配置"""
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        
        self.llm = AIModelAPI(model=self.model, api_key=self.api_key, base_url=self.api_base)

    def extract_text(self, file):
        doc = Document(io.BytesIO(file.read()))
        
        # 保留段落格式信息
        paragraphs_info = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                paragraphs_info.append({
                    'text': paragraph.text,
                    'style': paragraph.style.name,
                    'indent': paragraph.paragraph_format.first_line_indent,
                    'alignment': paragraph.paragraph_format.alignment
                })
        
        # 合并文本用于结构分析
        text_content = '\n'.join(p['text'] for p in paragraphs_info)
        
        # 分析文档结构
        structure = self._analyze_structure(text_content)
        
        # 使用结构信息进行精确分段
        segments = self._advanced_split(paragraphs_info, structure)
        
        return segments

    def _analyze_structure(self, text_sample):
        """使用AI分析文档结构"""
        try:
            prompt = self.structure_prompt.format(text=text_sample)
            response = self.llm.generate(prompt)
            
            response_text = response.strip('```json').strip('```')
            structure = json.loads(response_text)
            print("文档结构分析结果:", json.dumps(structure, ensure_ascii=False, indent=2))
            return structure
            
        except Exception as e:
            print(f"结构分析失败: {str(e)}")
            return self._get_default_structure()

    def _get_default_structure(self):
        """返回默认的文档结构"""
        return {
            "doc_type": "general",
            "structure": {
                "segments": [
                    {"pattern": r"^\d+\.", "type": "序号", "level": 1},
                    {"pattern": r"^\n\s*\n", "type": "段落", "level": 1}
                ]
            },
            "special_markers": []
        }

    def _advanced_split(self, paragraphs_info, structure):
        """使用结构信息进行高级分段"""
        segments = []
        current_segment = {
            'content': [],
            'level': 0,
            'type': None
        }
        
        for para in paragraphs_info:
            text = para['text'].strip()
            if not text:
                continue
                
            # 检查是否匹配任何分段模式
            matched = False
            for segment_info in structure['structure']['segments']:
                pattern = segment_info['pattern']
                if re.match(pattern, text):
                    # 保存当前段落（如果有）
                    if current_segment['content']:
                        segments.append({
                            'text': '\n'.join(current_segment['content']),
                            'level': current_segment['level'],
                            'type': current_segment['type']
                        })
                    
                    # 开始新段落
                    current_segment = {
                        'content': [text],
                        'level': segment_info['level'],
                        'type': segment_info['type']
                    }
                    matched = True
                    break
            
            # 检查特殊标记
            for marker in structure['special_markers']:
                if text.startswith(marker):
                    if current_segment['content']:
                        segments.append({
                            'text': '\n'.join(current_segment['content']),
                            'level': current_segment['level'],
                            'type': current_segment['type']
                        })
                    current_segment = {
                        'content': [text],
                        'level': 1,
                        'type': 'special'
                    }
                    matched = True
                    break
            
            # 如果没有匹配任何模式，添加到当前段落
            if not matched:
                current_segment['content'].append(text)
        
        # 添加最后一个段落
        if current_segment['content']:
            segments.append({
                'text': '\n'.join(current_segment['content']),
                'level': current_segment['level'],
                'type': current_segment['type']
            })
        
        print(segments)
        return segments 