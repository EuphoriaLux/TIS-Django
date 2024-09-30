$(document).ready(function() {
    var $header = $('header');
    var $menuJk = $('#menu-jk');
    var headerHeight = $header.outerHeight();

    function handleScroll() {
        if ($(window).scrollTop() > headerHeight) {
            $menuJk.addClass('fixed');
        } else {
            $menuJk.removeClass('fixed');
        }
    }

    // Run on page load
    handleScroll();

    // Run on scroll
    $(window).on('scroll', handleScroll);

    // Run on window resize
    $(window).on('resize', function() {
        headerHeight = $header.outerHeight();
        handleScroll();
    });

    $('.owl-carousel').owlCarousel({
        loop:true,
        margin:0,
        nav:true,
        autoplay: true,
        dots: true,
        autoplayTimeout: 5000,
        navText:['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>'],
        responsive:{
            0:{
                items:1
            },
            600:{
                items:1
            },
            1000:{
                items:1
            }
        }
    });
});
