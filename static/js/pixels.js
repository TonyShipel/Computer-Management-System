document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('image-gen-form');
    const generateBtn = document.getElementById('generate-btn');
    const generatedImage = document.getElementById('generated-image');
    const loadingPlaceholder = document.getElementById('loading-placeholder');
    const btnSpinner = generateBtn.querySelector('.spinner-border');
    const btnText = generateBtn.querySelector('.btn-text');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        generateBtn.disabled = true;
        btnSpinner.classList.remove('d-none');
        btnText.textContent = 'Генерация...';
        loadingPlaceholder.classList.remove('d-none');
        generatedImage.classList.add('d-none');

        try {
            const prompt = document.getElementById('prompt').value;
            const style = document.getElementById('style').value;

            const response = await fetch('/api/generate-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt, style })
            });

            const data = await response.json();

            if (response.ok) {
                // Add timestamp to prevent browser caching
                const timestamp = new Date().getTime();
                generatedImage.src = `${data.image_url}?t=${timestamp}`;
                generatedImage.classList.remove('d-none');
                
                // Add load event listener to ensure image is loaded
                generatedImage.onload = function() {
                    loadingPlaceholder.classList.add('d-none');
                };
                
                generatedImage.onerror = function() {
                    alert('Ошибка загрузки изображения');
                    loadingPlaceholder.classList.add('d-none');
                };
            } else {
                throw new Error(data.error || 'Ошибка при генерации изображения');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Произошла ошибка при генерации изображения');
            loadingPlaceholder.classList.add('d-none');
        } finally {
            // Reset button state
            generateBtn.disabled = false;
            btnSpinner.classList.add('d-none');
            btnText.textContent = 'Сгенерировать';
        }
    });
}); 