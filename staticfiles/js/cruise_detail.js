document.addEventListener('DOMContentLoaded', function() {
    let selectedSession = null;
    let selectedCabin = null;

    // Initialize image sliders
    $('.image-slider').slick({
        dots: true,
        infinite: true,
        speed: 500,
        fade: true,
        cssEase: 'linear'
    });

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

    // Handle cabin selection
    document.querySelectorAll('.select-cabin-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const cabinCard = e.target.closest('.cabin-card');
            selectedCabin = cabinCard.dataset.cabinId;
            document.querySelectorAll('.cabin-card').forEach(card => card.classList.remove('selected'));
            cabinCard.classList.add('selected');
        });
    });

    // Handle step navigation
    document.getElementById('backToDate').addEventListener('click', () => {
        showStep(1);
    });

    document.getElementById('proceedToBooking').addEventListener('click', () => {
        if (selectedSession && selectedCabin) {
            
            const bookingUrl = `${bookCruiseUrl}?session=${selectedSession}&cabin=${selectedCabin}`;
            window.location.href = bookingUrl;
        } else {
            alert('Please select both a date and a cabin type before proceeding.');
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

    // Handle comparison checkboxes
    document.querySelectorAll('.compare-check').forEach(checkbox => {
        checkbox.addEventListener('change', updateComparison);
    });

    function updateComparison() {
        const selectedCabins = Array.from(document.querySelectorAll('.compare-check:checked')).map(cb => cb.dataset.cabinId);
        
        if (selectedCabins.length > 1) {
            // Show comparison table
            document.getElementById('cabinComparison').style.display = 'block';
            
            // Update comparison table
            const comparisonTable = document.querySelector('.comparison-table');
            const headerRow = comparisonTable.querySelector('thead tr');
            const tbody = comparisonTable.querySelector('tbody');
            
            // Clear existing content
            headerRow.innerHTML = '<th>Feature</th>';
            tbody.innerHTML = '';
            
            // Add cabin names to header
            selectedCabins.forEach(cabinId => {
                const cabinName = document.querySelector(`.cabin-card[data-cabin-id="${cabinId}"] .cabin-name`).textContent;
                headerRow.innerHTML += `<th>${cabinName}</th>`;
            });
            
            // Add comparison data
            const features = ['Price', 'Description', 'Deck', 'Capacity'];
            features.forEach(feature => {
                let row = `<tr><td>${feature}</td>`;
                selectedCabins.forEach(cabinId => {
                    const cabinCard = document.querySelector(`.cabin-card[data-cabin-id="${cabinId}"]`);
                    switch(feature) {
                        case 'Price':
                            row += `<td>${cabinCard.querySelector('.cabin-price').textContent}</td>`;
                            break;
                        case 'Description':
                            row += `<td>${cabinCard.querySelector('.cabin-description').textContent}</td>`;
                            break;
                        case 'Deck':
                            row += `<td>${cabinCard.querySelector('.cabin-details li:nth-child(1)').textContent.replace('Deck:', '').trim()}</td>`;
                            break;
                        case 'Capacity':
                            row += `<td>${cabinCard.querySelector('.cabin-details li:nth-child(2)').textContent.replace('Capacity:', '').trim()}</td>`;
                            break;
                    }
                });
                row += '</tr>';
                tbody.innerHTML += row;
            });
        } else {
            // Hide comparison table if less than 2 cabins are selected
            document.getElementById('cabinComparison').style.display = 'none';
        }
    }
});