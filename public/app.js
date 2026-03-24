document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const excelInput = document.getElementById('excelFile');
    const photoInputs = [
        document.getElementById('photo1'),
        document.getElementById('photo2'),
        document.getElementById('photo3')
    ];
    const generateBtn = document.getElementById('generateBtn');
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const statusMessage = document.getElementById('statusMessage');

    // Drag and Drop styling & File select styling
    function setupFileUpload(inputElement) {
        const dropArea = inputElement.closest('.upload-area');
        const label = dropArea.querySelector('label');
        const originalText = label.innerText;

        inputElement.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const fileName = e.target.files[0].name;
                label.innerText = fileName.length > 20
                    ? fileName.substring(0, 20) + '...'
                    : fileName;
                dropArea.classList.add('file-selected');
            } else {
                label.innerText = originalText;
                dropArea.classList.remove('file-selected');
            }
        });

        // Add drag events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

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
            const dt = e.dataTransfer;
            const files = dt.files;
            inputElement.files = files;

            // Dispatch change event manually
            const event = new Event('change');
            inputElement.dispatchEvent(event);
        }, false);
    }

    setupFileUpload(excelInput);
    photoInputs.forEach(input => setupFileUpload(input));

    // Handle Generation
    generateBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        // Validate
        if (!excelInput.files[0]) {
            showStatus('Falta el archivo Excel obligatorio', 'error');
            return;
        }

        const projectTitle = document.getElementById('project_title').value;
        const gestorName = document.getElementById('gestor_name').value;

        if (!projectTitle || !gestorName) {
            showStatus('Por favor, rellena los textos obligatorios', 'error');
            return;
        }

        // Prepare FormData
        const formData = new FormData();
        formData.append('excelFile', excelInput.files[0]);

        if (photoInputs[0].files[0]) formData.append('photo1', photoInputs[0].files[0]);
        if (photoInputs[1].files[0]) formData.append('photo2', photoInputs[1].files[0]);
        if (photoInputs[2].files[0]) formData.append('photo3', photoInputs[2].files[0]);

        formData.append('project_title', projectTitle);
        formData.append('gestor_name', gestorName);
        formData.append('project_description', document.getElementById('project_description').value);

        // UI Loading State
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
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error en la generación');
            }

            // Download BLOB
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `Informe_Viabilidad_${projectTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            showStatus('¡Presentación generada y descargada con éxito!', 'success');
        } catch (error) {
            console.error(error);
            showStatus(error.message, 'error');
        } finally {
            // Restore UI
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
