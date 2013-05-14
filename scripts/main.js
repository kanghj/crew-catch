// Toggle between hiding and showing 
$(document).ready(function(){
    $(".expand").click(function(){
	$(this).next().toggle();
    });
});

// Toggle between plus and minus icons
$(document).ready(function(){
    $(".icon-minus, .icon-plus").click(function(){
	$(this).toggleClass("icon-plus icon-minus");
    });
});

// Check all checkboxes
$(document).ready(function(){
    $("#checkall").change(function(){
	if($('#checkall').is(':checked')){
	    $('.Checkone').prop('checked', true);
	} else {
	    $('.checkone').prop('checked', false);
	}
    });
});

