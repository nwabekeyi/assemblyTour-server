document.addEventListener('DOMContentLoaded', function() {
    function toggleGalleryFields() {
        var mediaType = document.querySelector('select[name="media_type"]').value;
        var mediaRow = document.querySelector('#id_media').closest('.form-row');
        var urlRow = document.querySelector('#id_url').closest('.form-row');
        var thumbnailRow = document.querySelector('#id_thumbnail').closest('.form-row');
        var urlInput = document.querySelector('#id_url');
        var mediaInput = document.querySelector('#id_media');

        if (!mediaType) {
            mediaType = 'image';
        }

        if (mediaType === 'image') {
            mediaRow.style.display = '';
            thumbnailRow.style.display = '';
            urlRow.style.display = 'none';
            urlInput.disabled = true;
            urlInput.value = '';
        } else {
            mediaRow.style.display = 'none';
            thumbnailRow.style.display = 'none';
            urlRow.style.display = '';
            urlInput.disabled = false;
            mediaInput.value = '';
        }
    }

    toggleGalleryFields();

    document.querySelector('select[name="media_type"]').addEventListener('change', toggleGalleryFields);

    document.querySelector('#id_url').addEventListener('input', function() {
        if (document.querySelector('select[name="media_type"]').value !== 'image') {
            this.disabled = false;
        }
    });

    document.querySelector('#id_media').addEventListener('change', function() {
        if (document.querySelector('select[name="media_type"]').value !== 'image') {
            this.value = '';
        }
    });
});
