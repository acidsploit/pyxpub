$(document).ready(function(){
  $.getJSON( "http://localhost:8080/api/payment?amount=0.0023&label=SHOP:1Wed2B44", function( data ) {
    var items = [];
    var payment = data['payment'];
    $.each( payment, function( key, val ) {
      items.push( "<li id='" + key + "'>" + val + "</li>" );
    });
  
    $( "<ul/>", {
      "class": "my-new-list",
      html: items.join( "" )
    }).appendTo( "body" );
  });
}); 
