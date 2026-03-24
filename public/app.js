document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const statusMessage = document.getElementById('statusMessage');
    const excelInput = document.getElementById('excelFile');

    // Setup drag & drop for Excel
    setupFileUpload(excelInput);

    // Setup initial photo inputs
    document.querySelectorAll('.photo-list input[type="file"]').forEach(input => {
        setupFileUpload(input);
    });

    // "Add photo" buttons
    document.querySelectorAll('.btn-add-photo').forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.dataset.category;
            const list = document.getElementById(`${category}-list`);
            addPhotoSlot(list, category);
        });
    });

    function addPhotoSlot(container, category) {
        const wrapper = document.createElement('div');
        wrapper.className = 'upload-area photo-drop';

        const input = document.createElement('input');
        input.type = 'file';
        input.name = category;
        input.accept = 'image/*';

        const label = document.createElement('label');
        label.innerText = 'Haz clic o arrastra';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn-remove-photo';
        removeBtn.innerHTML = '✕';
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            wrapper.remove();
        });

        wrapper.appendChild(input);
        wrapper.appendChild(label);
        wrapper.appendChild(removeBtn);
        container.appendChild(wrapper);

        setupFileUpload(input);
    }

    function setupFileUpload(inputElement) {
        const dropArea = inputElement.closest('.upload-area');
        if (!dropArea) return;
        const label = dropArea.querySelector('label');
        if (!label) return;
        const originalText = label.innerText;

        inputElement.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const fileName = e.target.files[0].name;
                label.innerText = fileName.length > 25
                    ? fileName.substring(0, 22) + '...'
                    : fileName;
                dropArea.classList.add('file-selected');
            } else {
                label.innerText = originalText;
                dropArea.classList.remove('file-selected');
            }
        });

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.style.borderColor = 'var(--primary-color)', false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                if (!dropArea.classList.contains('file-selected')) {
                    dropArea.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                }
            }, false);
        });

        dropArea.addEventListener('drop', (e) => {
            inputElement.files = e.dataTransfer.files;
            inputElement.dispatchEvent(new Event('change'));
        }, false);
    }

    // Generate PDF
    generateBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        if (!excelInput.files[0]) {
            showStatus('Falta el archivo Excel obligatorio', 'error');
            return;
        }

        const projectTitle = document.getElementById('project_title').value;
        if (!projectTitle) {
            showStatus('Por favor, introduce el título del proyecto', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('excelFile', excelInput.files[0]);
        formData.append('project_title', projectTitle);

        // Text sections
        formData.append('text_resumen', document.getElementById('text_resumen').value);
        formData.append('text_estudio', document.getElementById('text_estudio').value);
        formData.append('text_gestor', document.getElementById('text_gestor').value);
        formData.append('text_riesgos', document.getElementById('text_riesgos').value);

        // Photos by category
        ['portada', 'fachada', 'interior'].forEach(category => {
            const inputs = document.querySelectorAll(`input[name="${category}"]`);
            let idx = 0;
            inputs.forEach(input => {
                if (input.files[0]) {
                    formData.append(`${category}_${idx}`, input.files[0]);
                    idx++;
                }
            });
        });

        // UI loading
        generateBtn.disabled = true;
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        statusMessage.classList.add('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMsg = 'Error en la generación';
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorMsg;
                } catch {
                    const txt = await response.text();
                    errorMsg = txt || errorMsg;
                }
                throw new Error(errorMsg);
            }

            // Descargar el PDF correctamente
            const arrayBuffer = await response.arrayBuffer();
            const blob = new Blob([arrayBuffer], { type: 'application/pdf' });
            const fileName = `Informe_Viabilidad_${projectTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.pdf`;
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName;
            a.style.display = 'none';
            document.body.appendChild(a);
            // setTimeout para compatibilidad con Safari
            setTimeout(() => {
                a.click();
                setTimeout(() => {
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }, 250);
            }, 0);

            showStatus('¡Presentación generada y descargada con éxito!', 'success');
        } catch (error) {
            console.error(error);
            showStatus(error.message, 'error');
        } finally {
            generateBtn.disabled = false;
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message status-${type}`;
        statusMessage.classList.remove('hidden');
    }
});
