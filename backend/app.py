from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from document_processor import DocumentProcessor
from ai_checker import AIChecker
import traceback
import json
import io
import os

# 修改静态文件夹的路径配置
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=static_folder)
CORS(app)

# 添加根路由，返回前端页面
@app.route('/')
def serve_frontend():
    print(f"Static folder path: {app.static_folder}")
    print(f"File exists: {os.path.exists(os.path.join(app.static_folder, 'index.html'))}")
    return send_from_directory(app.static_folder, 'index.html')

# 添加静态文件路由
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/check-document', methods=['POST'])
def check_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        # 获取API配置和模型选择
        api_base = request.headers.get('api-base')
        api_key = request.headers.get('api-key')
        model = request.headers.get('model', 'deepseek-ai/DeepSeek-V3')  # 默认模型

        if not api_base or not api_key:
            return jsonify({'error': '缺少API配置'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith(('.doc', '.docx')):
            return jsonify({'error': '仅支持.doc或.docx格式'}), 400

        # 在生成器函数之前读取文件内容
        file_content = file.read()

        def generate():
            try:
                doc_processor = DocumentProcessor()
                ai_checker = AIChecker()

                # 设置API配置
                doc_processor.set_api_config(api_base, api_key, model)
                ai_checker.set_api_config(api_base, api_key, model)

                # 使用文件内容的副本进行处理
                file_copy = io.BytesIO(file_content)
                segments = doc_processor.extract_text(file_copy)
                
                # AI检查并实时返回结果
                for result in ai_checker.check_content(segments):
                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"生成器内部错误: {str(e)}")
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        print("Error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8402) 