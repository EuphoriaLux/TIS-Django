document.addEventListener('DOMContentLoaded', function() {
    let selectedSession = null;
    let selectedCategory = null;

    // Handle date selection
    document.querySelectorAll('.select-date-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const listItem = e.target.closest('li');
            selectedSession = listItem.dataset.sessionId;
            document.querySelectorAll('.date-list li').forEach(li => li.classList.remove('selected'));
            listItem.classList.add('selected');
            showStep(2);
        });
    });

    // Handle category selection
    document.querySelectorAll('.select-category-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const categoryCard = e.target.closest('.category-card');
            selectedCategory = categoryCard.dataset.categoryId;
            document.querySelectorAll('.category-card').forEach(card => card.classList.remove('selected'));
            categoryCard.classList.add('selected');
        });
    });

    // Handle step navigation
    document.getElementById('backToDate').addEventListener('click', () => {
        showStep(1);
    });

    document.getElementById('proceedToBooking').addEventListener('click', () => {
        if (selectedSession && selectedCategory) {
            // Redirect to booking page with selected session and category
            window.location.href = `${bookCruiseUrl}?session=${selectedSession}&category=${selectedCategory}`;
        } else {
            alert('Please select both a date and a cabin category before proceeding.');
        }
    });

    function showStep(stepNumber) {
        document.querySelectorAll('.step').forEach((step, index) => {
            step.classList.toggle('active', index + 1 <= stepNumber);
        });
        document.querySelectorAll('.step-content').forEach((content, index) => {
            content.classList.toggle('active', index + 1 === stepNumber);
        });
    }
});