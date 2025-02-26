document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInfo = document.querySelector('.file-info');
    const fileName = document.querySelector('.file-name');
    const progressSection = document.querySelector('.progress-section');
    const progressBar = document.querySelector('.progress');
    const errorList = document.querySelector('.error-list');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const errorOnlyBtn = document.getElementById('errorOnlyBtn');
    
    // 添加文件队列管理
    let fileQueue = [];
    let isProcessing = false;
    let showErrorOnly = false;

    // 将所有与后端通信的URL从5000端口改为8402端口
    const backendUrl = 'http://localhost:8402';  // 或者直接使用相对路径 '/'

    // 拖放文件处理
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-color)';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        handleFileSelect(e.dataTransfer.files);
        // console.log(e.dataTransfer.files);
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files);
    });

    // 修改文件选择处理函数
    function handleFileSelect(files) {
        const validFiles = Array.from(files).filter(file => {
            if (!file.name.endsWith('.doc') && !file.name.endsWith('.docx')) {
                alert(`文件 ${file.name} 不是Word文档，已跳过`);
                return false;
            }
            return true;
        });

        if (validFiles.length === 0) return;

        fileQueue.push(...validFiles);
        // 确保文件信息区域可见
        fileInfo.style.display = 'block';
        // 更新文件名显示为队列中的文件数量
        fileName.textContent = `已选择 ${fileQueue.length} 个文件`;
        updateFileQueueDisplay();
        uploadBtn.disabled = false;
    }

    // 修改文件队列显示功能
    function updateFileQueueDisplay() {
        const queueList = document.createElement('div');
        queueList.className = 'file-queue';
        
        if (fileQueue.length === 0) {
            fileInfo.style.display = 'none';
            return;
        }
        
        fileQueue.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-queue-item';
            fileItem.innerHTML = `
                <span class="queue-file-name">${file.name}</span>
                <div class="queue-file-actions">
                    ${index === 0 && isProcessing ? '<span class="processing">处理中...</span>' : ''}
                    <button class="remove-file" data-index="${index}" ${index === 0 && isProcessing ? 'disabled' : ''}>
                        删除
                    </button>
                </div>
            `;
            queueList.appendChild(fileItem);
        });

        const oldQueue = document.querySelector('.file-queue');
        if (oldQueue) {
            oldQueue.replaceWith(queueList);
        } else {
            fileInfo.appendChild(queueList);
        }

        // 添加删除文件的事件监听
        queueList.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                if (!isProcessing || index !== 0) {
                    fileQueue.splice(index, 1);
                    if (fileQueue.length === 0) {
                        uploadBtn.disabled = true;
                        fileInfo.style.display = 'none';
                    } else {
                        fileName.textContent = `已选择 ${fileQueue.length} 个文件`;
                    }
                    updateFileQueueDisplay();
                }
            });
        });
    }

    // 过滤器处理
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterResults(btn.dataset.type);
        });
    });

    // 添加仅显示错误按钮的事件监听
    errorOnlyBtn.addEventListener('click', () => {
        showErrorOnly = !showErrorOnly;
        errorOnlyBtn.classList.toggle('active');
        filterResults(document.querySelector('.filter-btn.active').dataset.type);
    });

    // 修改过滤结果函数
    function filterResults(type) {
        const segments = document.querySelectorAll('.segment-item');
        segments.forEach(segment => {
            const errors = segment.querySelectorAll('.error-item');
            const hasErrors = errors.length > 0;
            const hasMatchingErrors = Array.from(errors).some(error => 
                type === 'all' || error.dataset.type === type
            );

            if (showErrorOnly && !hasErrors) {
                segment.style.display = 'none';
            } else if (type === 'all') {
                segment.style.display = 'block';
            } else {
                segment.style.display = hasMatchingErrors ? 'block' : 'none';
            }

            // 根据过滤类型显示/隐藏具体的错误项
            errors.forEach(error => {
                error.style.display = 
                    (type === 'all' || error.dataset.type === type) ? 'block' : 'none';
            });
        });
    }

    // 修改上传和处理逻辑
    async function processNextFile() {
        if (fileQueue.length === 0 || isProcessing) return;

        const apiBase = localStorage.getItem('apiBase');
        const apiKey = localStorage.getItem('apiKey');
        const selectedModel = document.getElementById('modelSelect').value;
        
        if (!apiBase || !apiKey) {
            alert('请先在设置中配置API信息');
            openSettings();
            return;
        }

        isProcessing = true;
        const currentFile = fileQueue[0];
        updateFileQueueDisplay();

        const formData = new FormData();
        formData.append('file', currentFile);

        progressSection.style.display = 'block';
        // 添加文件分隔标记
        if (errorList.children.length > 0) {
            const separator = document.createElement('div');
            separator.className = 'file-separator';
            separator.innerHTML = `<span>文件分隔线</span>`;
            errorList.appendChild(separator);
        }
        
        // 禁用上传按钮
        uploadBtn.disabled = true;
        uploadBtn.style.opacity = '0.7';

        try {
            const response = await fetch(`${backendUrl}/check-document`, {
                method: 'POST',
                headers: {
                    'api-base': apiBase,
                    'api-key': apiKey,
                    'model': selectedModel
                },
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
                        if (result.error) {
                            alert(`处理文件 ${currentFile.name} 时发生错误: ${result.error}`);
                        } else {
                            displayResult(result, currentFile.name);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert(`处理文件 ${currentFile.name} 时发生错误`);
        } finally {
            fileQueue.shift();
            isProcessing = false;
            updateFileQueueDisplay();
            
            if (fileQueue.length > 0) {
                // 如果队列中还有文件，继续处理
                processNextFile();
            } else {
                // 如果队列为空，恢复按钮状态
                progressSection.style.display = 'none';
                uploadBtn.disabled = false;
                uploadBtn.style.opacity = '1';
            }
        }
    }

    // 修改上传按钮事件处理
    uploadBtn.addEventListener('click', () => {
        if (fileQueue.length === 0) {
            alert('请先选择文件');
            return;
        }
        if(!uploadBtn.disabled){
            processNextFile();
        }
        uploadBtn.disabled = true;
        uploadBtn.style.opacity = '0.7';
    });

    // 修改显示结果函数
    function displayResult(result, filename) {
        const segmentDiv = document.createElement('div');
        segmentDiv.className = 'segment-item';
        if (result.errors.length === 0) {
            segmentDiv.classList.add('no-errors');
        }
        
        const segmentInfo = document.createElement('div');
        segmentInfo.className = 'segment-info';
        segmentInfo.innerHTML = `
            <h3>文件: ${filename}</h3>
            <h4>段落类型: ${result.segment.type || '普通段落'}</h4>
            <p>层级: ${result.segment.level || 'N/A'}</p>
            <p>原文:</p>
            <pre>${result.segment.text}</pre>
        `;
        segmentDiv.appendChild(segmentInfo);

        if (result.errors.length === 0) {
            const noErrorDiv = document.createElement('div');
            noErrorDiv.className = 'no-error-message';
            noErrorDiv.textContent = '✓ 该段落未发现错误';
            segmentDiv.appendChild(noErrorDiv);
        } else {
            result.errors.forEach(error => {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-item';
                errorDiv.dataset.type = error.type.toLowerCase().includes('逻辑') ? 'logic' :
                                      error.type.toLowerCase().includes('别字') ? 'typo' : 'grammar';
                errorDiv.innerHTML = `
                    <h4>${error.type}</h4>
                    <p>位置：${error.location}</p>
                    <p>原文：${error.original}</p>
                    <p>建议：${error.suggestion}</p>
                `;
                segmentDiv.appendChild(errorDiv);
            });
        }

        if (!showErrorOnly || result.errors.length > 0) {
            errorList.appendChild(segmentDiv);
            segmentDiv.scrollIntoView({ behavior: 'smooth' });
        }
    }

    // 添加设置相关函数
    function openSettings() {
        const modal = document.getElementById('settingsModal');
        const apiBase = localStorage.getItem('apiBase') || '';
        const apiKey = localStorage.getItem('apiKey') || '';
        
        document.getElementById('apiBase').value = apiBase;
        document.getElementById('apiKey').value = apiKey;
        modal.style.display = 'block';
    }

    function closeSettings() {
        const modal = document.getElementById('settingsModal');
        modal.style.display = 'none';
    }

    function saveSettings() {
        const apiBase = document.getElementById('apiBase').value.trim();
        const apiKey = document.getElementById('apiKey').value.trim();
        
        localStorage.setItem('apiBase', apiBase);
        localStorage.setItem('apiKey', apiKey);
        closeSettings();
    }

    // 修改原有的API调用函数，使用localStorage中的配置
    async function callAPI(endpoint, data) {
        const apiBase = localStorage.getItem('apiBase');
        const apiKey = localStorage.getItem('apiKey');
        
        if (!apiBase || !apiKey) {
            alert('请先在设置中配置API信息');
            openSettings();
            return;
        }

        try {
            const response = await fetch(`${apiBase}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API调用错误:', error);
            throw error;
        }
    }

    // 设置按钮和模态框
    const settingsBtn = document.querySelector('.settings-btn');
    const settingsModal = document.getElementById('settingsModal');
    const saveSettingsBtn = document.querySelector('.button-group button:first-child');
    const cancelSettingsBtn = document.querySelector('.button-group button:last-child');

    // 打开设置
    settingsBtn.addEventListener('click', () => {
        const apiBase = localStorage.getItem('apiBase') || '';
        const apiKey = localStorage.getItem('apiKey') || '';
        
        document.getElementById('apiBase').value = apiBase;
        document.getElementById('apiKey').value = apiKey;
        settingsModal.style.display = 'block';
    });

    // 保存设置
    saveSettingsBtn.addEventListener('click', () => {
        const apiBase = document.getElementById('apiBase').value.trim();
        const apiKey = document.getElementById('apiKey').value.trim();
        
        if (!apiBase || !apiKey) {
            alert('请填写完整的API配置信息');
            return;
        }
        
        localStorage.setItem('apiBase', apiBase);
        localStorage.setItem('apiKey', apiKey);
        settingsModal.style.display = 'none';
    });

    // 取消设置
    cancelSettingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    // 点击模态框外部关闭
    window.addEventListener('click', (event) => {
        if (event.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    // 自定义下拉菜单
    const modelSelect = document.getElementById('modelSelect');
    const selectButton = document.querySelector('.model-select-button');
    const dropdown = document.querySelector('.model-select-dropdown');
    const options = document.querySelectorAll('.model-option');

    // 点击按钮显示/隐藏下拉列表
    selectButton.addEventListener('click', () => {
        dropdown.classList.toggle('active');
        selectButton.classList.toggle('active');
    });

    // 选择选项
    options.forEach(option => {
        option.addEventListener('click', () => {
            const value = option.dataset.value;
            const text = option.textContent;

            // 更新原生select的值
            modelSelect.value = value;

            // 更新按钮文本
            selectButton.textContent = text;

            // 更新选中状态
            options.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');

            // 关闭下拉列表
            dropdown.classList.remove('active');
            selectButton.classList.remove('active');
        });
    });

    // 点击外部关闭下拉列表
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.model-select-wrapper')) {
            dropdown.classList.remove('active');
            selectButton.classList.remove('active');
        }
    });
}); 