document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressSection = document.querySelector('.progress-section');
    const progressBar = document.querySelector('.progress');
    const errorList = document.querySelector('.error-list');

    uploadBtn.addEventListener('click', async function() {
        if (!fileInput.files[0]) {
            alert('请先选择文件');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        progressSection.style.display = 'block';
        progressBar.style.width = '0%';
        errorList.innerHTML = ''; // 清空之前的结果

        try {
            const response = await fetch('http://localhost:5000/check-document', {
                method: 'POST',
                body: formData
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const result = JSON.parse(line.slice(5));
                        displayResult(result);
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert('处理文档时发生错误');
        } finally {
            progressSection.style.display = 'none';
        }
    });

    function displayResult(result) {
        const segmentDiv = document.createElement('div');
        segmentDiv.className = 'segment-item';
        
        // 显示段落信息
        const segmentInfo = document.createElement('div');
        segmentInfo.className = 'segment-info';
        segmentInfo.innerHTML = `
            <h3>段落类型: ${result.segment.type || '普通段落'}</h3>
            <p>层级: ${result.segment.level || 'N/A'}</p>
            <p>原文:</p>
            <pre>${result.segment.text}</pre>
        `;
        segmentDiv.appendChild(segmentInfo);

        // 显示错误信息
        result.errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-item';
            errorDiv.innerHTML = `
                <h4>${error.type}</h4>
                <p>位置：${error.location}</p>
                <p>原文：${error.original}</p>
                <p>建议：${error.suggestion}</p>
            `;
            segmentDiv.appendChild(errorDiv);
        });

        errorList.appendChild(segmentDiv);
        // 滚动到最新结果
        segmentDiv.scrollIntoView({ behavior: 'smooth' });
    }
}); 