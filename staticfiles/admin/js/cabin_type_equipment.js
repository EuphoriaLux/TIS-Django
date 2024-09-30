(function($) {
    $(document).ready(function() {
        var $equipmentSelect = $('#id_equipment');
        var $descriptionDiv = $('<div id="equipment-description"></div>');
        
        $equipmentSelect.after($descriptionDiv);

        $equipmentSelect.on('change', function() {
            var selectedOption = $(this).find('option:selected');
            var description = selectedOption.data('description');
            $descriptionDiv.text(description || '');

            // Update the inline formset
            updateInlineFormset();
        });

        // Initialize with the description of the first selected item
        $equipmentSelect.trigger('change');

        // Add custom styling
        $equipmentSelect.css({
            'width': '100%',
            'height': '200px',
            'margin-bottom': '10px'
        });

        $descriptionDiv.css({
            'margin-top': '5px',
            'padding': '5px',
            'border': '1px solid #ddd',
            'background-color': '#f9f9f9'
        });

        function updateInlineFormset() {
            var selectedEquipment = $equipmentSelect.val() || [];
            
            // Hide all inline forms initially
            $('.inline-related').not('.empty-form').hide();

            // Show and update relevant inline forms
            selectedEquipment.forEach(function(equipmentId) {
                var $inlineForm = $('.inline-related').not('.empty-form').filter(function() {
                    return $(this).find('select[name$="-equipment"]').val() === equipmentId;
                });

                if ($inlineForm.length) {
                    $inlineForm.show();
                } else {
                    // If no existing form, add a new one
                    var $emptyForm = $('.empty-form').clone(true);
                    $emptyForm.removeClass('empty-form');
                    $emptyForm.find('select[name$="-equipment"]').val(equipmentId);
                    $emptyForm.show();
                    $('.inline-related').last().after($emptyForm);
                }
            });

            // Update form indices
            $('.dynamic-cabintypeequipment').each(function(index) {
                $(this).find('input, select, textarea').each(function() {
                    var name = $(this).attr('name');
                    if (name) {
                        name = name.replace(/cabintypeequipment_set-\d+/, 'cabintypeequipment_set-' + index);
                        $(this).attr('name', name);
                    }
                });
            });
        }
    });
})(django.jQuery);