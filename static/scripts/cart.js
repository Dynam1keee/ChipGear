$(document).ready(function () {
  $(document).on("click", ".add-to-cart", function (e) {
    e.preventDefault();
    var product_id = $(this).data("product-id");

    $.ajax({
      type: "POST",
      url: '/cart/cart_add/',
      data: {
        product_id: product_id,
        csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
      },
      success: function (data) {
        updateElements(data.cart_items_nav_html, '#goods-counter');
        updateElements(data.cart_items_nav_html, '#cart-container');
      },
      error: function (data) {
        console.log("Error");
      },
    });
  });


  $(document).on("click", ".remove-from-cart", function (e) {
    e.preventDefault();
    var cart_id = $(this).data("cart-id");
  
    $.ajax({
      type: "POST",
      url: '/cart/cart_remove/',
      data: {
        cart_id: cart_id,
        csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
      },
      success: function (data) {
        updateElements(data.cart_items_nav_html, '#goods-counter');
        updateElements(data.cart_items_nav_html, '#cart-container');
        if (document.location.pathname == '/user/users_cart/' || document.location.pathname == '/user/profile/') {
          updateElements(data.cart_items_html, '#cart-items-container');
        }
      },
      error: function (data) {
        console.log("Error");
      },
    });
  });


  $(document).on("click", ".decrement", function () {
    var url = $(this).data("cart-change-url");
    var cartID = $(this).data("cart-id");
    var $input = $(this).closest('.input-group').find('.quantity');
    var currentValue = parseInt($input.val());

    if (currentValue - 1 > 1) {
      $input.val(currentValue - 1);
      updateQuantity(cartID, currentValue - 1, -1, url);
      $(this).removeClass('disabled');
    } 
    if (currentValue == 2) {
      $input.val(currentValue - 1);
      updateQuantity(cartID, currentValue - 1, -1, url);
      $(this).addClass('disabled');
    }
  });


  $(document).on("click", ".increment", function () {
    var url = $(this).data("cart-change-url");
    var cartID = $(this).data("cart-id");
    var $input = $(this).closest('.input-group').find('.quantity');
    var currentValue = parseInt($input.val());

    $input.val(currentValue + 1);
    updateQuantity(cartID, currentValue + 1, 1, url);
    if (currentValue >= 1) {
      $(this).closest('.input-group').find('.decrement').removeClass('disabled');
    }
  });

  function updateQuantity(cartID, quantity, change, url) {
    $.ajax({
      type: "POST",
      url: url,
      data: {
        cart_id: cartID,
        quantity: quantity,
        csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
      },
      success: function (data) {
        updateElements(data.cart_items_nav_html, '#goods-counter');
        updateElements(data.cart_items_nav_html, '#cart-container');
        updateElements(data.cart_items_html, '.input-group .q-change');
        updateElements(data.cart_items_html, '.cart-price');
        updateElements(data.cart_items_html, '.total-price');
      },
      error: function (data) {
        console.log("Error");
      },
    });
  }

  function updateElements(html, selector) {
    var elementsArray = [];
    $(html).find(selector).each(function () { 
      elementsArray.push($(this).prop('outerHTML'));
    });
    $(selector).each(function (index) { 
      $(this).replaceWith(elementsArray[index]);
    });
  }
});