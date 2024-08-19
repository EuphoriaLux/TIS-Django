document.addEventListener('DOMContentLoaded', function() {
    let selectedCategoryId = null;
    const categoryCards = document.querySelectorAll('.category-card');
    const sessionSelect = document.getElementById('sessionSelect');
    const bookButtons = document.querySelectorAll('.book-btn');

    const descriptionDiv = document.querySelector('.cruise-description');
    if (descriptionDiv) {
        // Convert '##' to <h2> tags
        descriptionDiv.innerHTML = descriptionDiv.innerHTML.replace(/##\s(.*?)(\n|$)/g, '<h2>$1</h2>');
        
        // Convert '**' wrapped text to list items
        descriptionDiv.innerHTML = descriptionDiv.innerHTML.replace(/\*\*(.*?)\*\*/g, '<li>$1</li>');
        
        // Wrap lists in <ul> tags
        let content = descriptionDiv.innerHTML;
        content = content.replace(/(<li>.*?<\/li>\s*)+/g, function(match) {
            return '<ul>' + match + '</ul>';
        });
        descriptionDiv.innerHTML = content;
        
        // Create highlight boxes for sections starting with "Highlights" or "Experience"
        const paragraphs = descriptionDiv.getElementsByTagName('p');
        for (let p of paragraphs) {
            if (p.textContent.startsWith('Highlights') || p.textContent.startsWith('Experience')) {
                p.classList.add('highlight-box');
            }
        }
    }

    categoryCards.forEach(card => {
        const selectBtn = card.querySelector('.select-btn');
        selectBtn.addEventListener('click', function() {
            // Remove 'selected' class from all cards and buttons
            categoryCards.forEach(c => {
                c.classList.remove('selected');
                c.querySelector('.select-btn').classList.remove('selected');
                c.querySelector('.select-btn').textContent = 'Select Category';
            });
            
            // If clicking the same card, deselect it
            if (selectedCategoryId === card.dataset.categoryId) {
                selectedCategoryId = null;
                sessionSelect.style.display = 'none';
            } else {
                // Select the new card
                selectedCategoryId = card.dataset.categoryId;
                card.classList.add('selected');
                selectBtn.classList.add('selected');
                selectBtn.textContent = 'Selected';
                sessionSelect.style.display = 'block';
            }
        });
    });

    bookButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (selectedCategoryId) {
                const sessionId = this.dataset.sessionId;
                window.location.href = `${bookCruiseUrl}?category=${selectedCategoryId}&session=${sessionId}`;
            } else {
                alert('Please select a cabin category first.');
            }
        });
    });
});