(function($) {
    $("form#form-file-upload").on('submit', function(event) {
        event.preventDefault()
        // var form_data = new FormData($('#form-file-upload')[0])
        var terms = []
        var definitions = []
        var promises = []
        isError = false
        if (event.target[0].files.length > 5) {
            alert('No more than 5 files')
            return false
        }
        if (event.target[0].files.length <= 0) {
            alert('No files found')
            return false
        }
        $.each(event.target[0].files, (i, file) => {
            var form_data = new FormData();
            form_data.append('file', file);
            form_data.append('num_files', event.target[0].files.length)
            var req = $.ajax({
                type: 'POST',
                url: window.location.origin + '/upload',
                data: form_data,
                contentType: false,
                cache: false,
                processData: false,
                success: function(resp) {
                    terms = terms.concat(resp.terms)
                    definitions = definitions.concat(resp.definitions)
                    console.log('Added terms and definitions')
                },
                error: function(error) {
                    alert(error.responseText + "; for " + file.name)
                    isError = true
                    $('#submit_button').removeAttr('disabled')
                    $('#submit_button_vis').removeClass('disabled')
                    $('#submit_button_vis').css('cursor', 'pointer')

                    $('#my-file-selector').removeAttr('disabled')
                    $('#upload_button_vis').removeClass('disabled')
                    $('#upload_button_vis').css('cursor', 'pointer')
                },
                complete: function(resp) {
                    if(isError){
                        $('#quizlet_loader').attr('hidden', '');
                        $('#file-refresh').removeClass('disabled')
                    } 
                }
            });
            promises.push(req)
        });
        
        $('#quizlet_loader').removeAttr('hidden');
        $('#submit_button').prop('disabled', true)
        $('#submit_button_vis').addClass('disabled')
        $('#submit_button_vis').css('cursor', 'default')

        $('#my-file-selector').prop('disabled', true)
        $('#upload_button_vis').addClass('disabled')
        $('#upload_button_vis').css('cursor', 'default')
        $('#file-refresh').addClass('disabled')

        $.when.apply(null, promises).done(function(){
            if(!isError){
                var file_name = event.target[0].files.length > 1 ? event.target[0].files[0].name + ` + ${event.target[0].files.length - 1} file(s)` : event.target[0].files[0].name;
                if (file_name.length > 35) file_name = file_name.substring(0,15) + "..." + file_name.substring(file_name.length - 20, file_name.length);
                $.ajax({
                    type: 'POST',
                    url: window.location.origin + '/question_set',
                    data: JSON.stringify({"terms": terms, "definitions": definitions, "filename": file_name}),
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json',
                    success: function(resp) {
                        $('#quizlet_button').removeAttr('disabled');
                        $('#quizlet_button').css('opacity', '1.0');
                        $('#quizlet_form').attr('action', resp.url);
                        alert('Success!')
                    },
                    error: function(error) {
                        console.log(error)
                        alert(error.responseText)
                        isError = true
                        $('#submit_button').removeAttr('disabled')
                        $('#submit_button_vis').removeClass('disabled')
                        $('#submit_button_vis').css('cursor', 'pointer')

                        $('#my-file-selector').removeAttr('disabled')
                        $('#upload_button_vis').removeClass('disabled')
                        $('#upload_button_vis').css('cursor', 'pointer')
                    },
                    complete: function(resp) {
                        $('#quizlet_loader').attr('hidden', '');
                        $('#file-refresh').removeClass('disabled')
                    }
                });
            }
            
        });
    });

    $("#file-refresh").on('click', function(event){
        if(!$("#file-refresh").hasClass('disabled')){
            $('#quizlet_button').attr('disabled', '');
            $('#quizlet_button').css('opacity', '0.4');

            $('#upload-file-info').html('JPG, JPEG, PNG, and PDFs only');
            $('#file-refresh').attr('hidden', '');

            $('#submit_button').removeAttr('disabled')
            $('#submit_button_vis').removeClass('disabled')
            $('#submit_button_vis').css('cursor', 'pointer')

            $('#my-file-selector').removeAttr('disabled')
            $('#upload_button_vis').removeClass('disabled')
            $('#upload_button_vis').css('cursor', 'pointer')
        }
    });

    $("#my-file-selector").on('change', function(event){
        var file_name = event.target.files.length > 1 ? event.target.files[0].name + ` + ${event.target.files.length - 1} file(s)` : event.target.files[0].name;
        if (file_name.length > 35) file_name = file_name.substring(0,15) + "..." + file_name.substring(file_name.length - 20, file_name.length);
        $('#upload-file-info').html(file_name);
        $('#file-refresh').removeAttr('hidden');
    });
})(jQuery);