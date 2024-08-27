// static/js/wizard_form.js

document.addEventListener('DOMContentLoaded', function() {
    const cruiseSessionCards = document.querySelectorAll('.cruise-session-card');
    const cabinCategoryCards = document.querySelectorAll('.cabin-category-card');
    const cruiseSessionInput = document.querySelector('select[name$="cruise_session"]');
    const cabinCategoryInput = document.querySelector('select[name$="cruise_category_price"]');

    if (cruiseSessionCards.length > 0 && cruiseSessionInput) {
        cruiseSessionCards.forEach(card => {
            card.addEventListener('click', function() {
                cruiseSessionCards.forEach(c => c.classList.remove('selected'));
                this.classList.add('selected');
                cruiseSessionInput.value = this.dataset.sessionId;
            });
        });
    }

    if (cabinCategoryCards.length > 0 && cabinCategoryInput) {
        cabinCategoryCards.forEach(card => {
            card.addEventListener('click', function() {
                cabinCategoryCards.forEach(c => c.classList.remove('selected'));
                this.classList.add('selected');
                cabinCategoryInput.value = this.dataset.categoryId;
            });
        });
    }
});