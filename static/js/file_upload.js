(function($) {
    $("form#form-file-upload").on('submit', function(event) {
        event.preventDefault()
        var form_data = new FormData($('#form-file-upload')[0])
        $.ajax({
            type: 'POST',
            url: window.location.origin + '/upload',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function(quizletUrl) {
                $('#quizlet_button').removeAttr('disabled');
                $('#quizlet_button').css('opacity', '1.0');
                $('#quizlet_form').attr('action', quizletUrl);
                alert('Success!')
            },
            error: function(error) {
                alert(error.responseText)
                $('#submit_button').removeAttr('disabled')
                $('#submit_button_vis').removeClass('disabled')
                $('#submit_button_vis').css('cursor', 'pointer')

                $('#my-file-selector').removeAttr('disabled')
                $('#upload_button_vis').removeClass('disabled')
                $('#upload_button_vis').css('cursor', 'pointer')
            },
            complete: function(resp) {
                $('#quizlet_loader').attr('hidden', '');
            }
        });
        $('#quizlet_loader').removeAttr('hidden');
        $('#submit_button').prop('disabled', true)
        $('#submit_button_vis').addClass('disabled')
        $('#submit_button_vis').css('cursor', 'default')

        $('#my-file-selector').prop('disabled', true)
        $('#upload_button_vis').addClass('disabled')
        $('#upload_button_vis').css('cursor', 'default')
    });
})(jQuery);