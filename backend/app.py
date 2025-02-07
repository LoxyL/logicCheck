from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from document_processor import DocumentProcessor
from ai_checker import AIChecker
import traceback
import json
import io

app = Flask(__name__)
CORS(app)

@app.route('/check-document', methods=['POST'])
def check_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
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
    app.run(debug=True) 