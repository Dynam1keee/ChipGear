$(document).ready(function() {
    $('#id_image').change(function() {
        $('#no-avatar-label').attr('class', 'd-none');
        var input = this;
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#user-avatar').attr('src', e.target.result);
            }
            reader.readAsDataURL(input.files[0]);
        }
    });
});
