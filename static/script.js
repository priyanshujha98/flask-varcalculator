$(document).ready(function () {
    $('form').on('submit', function (e) {
        e.preventDefault();
    });
});

function showStep(stepno){
    $('.step').removeClass("active");
    var element = document.getElementById(stepno);
    element.classList.add("active");
}

function toggleCreditCardForm() {
    if($('#payment input[type=radio][name=payment_method]:checked').val() === 'credit-card') {
        $('#cc_form').removeClass('d-none')
    } else {
        $('#cc_form').addClass('d-none')
    }
}

function addExposureRow(){
    $('#exposure-table tbody').append($('#exposure_row_hidden').val());
}