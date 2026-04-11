// Toggle travel document fieldsets based on doc_type selection
(function() {
    'use strict';

    function toggleFieldsets() {
        // Find all doc_type selects in the form
        var docTypeSelects = document.querySelectorAll('select[id$="-doc_type"], select[name$="doc_type"]');
        
        docTypeSelects.forEach(function(select) {
            // Find the closest form fieldset (the container)
            var fieldset = select.closest('.formset');
            if (!fieldset) return;
            
            // Find all fieldsets within this form
            var fieldsets = fieldset.querySelectorAll('fieldset');
            
            // Get the current doc_type value
            var docType = select.value;
            
            fieldsets.forEach(function(fs) {
                var legend = fs.querySelector('legend');
                if (!legend) return;
                
                var legendText = legend.textContent || legend.innerText;
                
                if (legendText.indexOf('Visa Details') !== -1) {
                    fs.style.display = (docType === 'visa') ? 'block' : 'none';
                } else if (legendText.indexOf('Flight/Ticket Details') !== -1) {
                    fs.style.display = (docType === 'ticket') ? 'block' : 'none';
                } else if (legendText.indexOf('Hotel Details') !== -1) {
                    fs.style.display = (docType === 'hotel_voucher') ? 'block' : 'none';
                }
            });
            
            // Re-trigger change to update form layout
            // This is handled by the browser
        });
    }

    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', toggleFieldsets);
    } else {
        toggleFieldsets();
    }

    // Run on change
    document.addEventListener('change', function(e) {
        if (e.target.tagName === 'SELECT' && (e.target.id.indexOf('doc_type') !== -1 || e.target.name.indexOf('doc_type') !== -1)) {
            // Small delay to let the option actually change in the DOM
            setTimeout(toggleFieldsets, 10);
        }
    });

    // Also run when forms are added/removed (for dynamic forms)
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                toggleFieldsets();
            }
        });
    });

    // Observe the entire document for changes
    observer.observe(document.body, { childList: true, subtree: true });
})();