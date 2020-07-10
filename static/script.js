$(function(){

})

function showStep(stepno){
    $('.step').removeClass("active");
    var element = document.getElementById(stepno);
    element.classList.add("active");
}

function addExposureRow(){
    $('#exposure-table tbody').append($('#exposure_row_hidden').val());
}