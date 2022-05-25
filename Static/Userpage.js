$(document).ready(function(){
    $('.show-popup').click(function(){
        $('.popup').fadeIn();
    });

    $('.popup').click(function(){
        $(this).fadeOut();

    });

    $('.popup .inner').click(function(e){
        e.stopPropagation();
    });

    });


    