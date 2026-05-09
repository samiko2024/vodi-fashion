document.addEventListener("DOMContentLoaded", () => {

    /* ===== MENU ===== */
    const menu = document.getElementById("menu");
    const bar = document.getElementById("bar");
    const closeMenu = document.getElementById("close-menu");
    const openMenu = document.getElementById("openMenu");

    if (bar && menu) {
        bar.addEventListener("click", () => menu.classList.add("active"));
    }

    if (openMenu && menu) {
        openMenu.addEventListener("click", () => menu.classList.add("active"));
    }

    if (closeMenu && menu) {
        closeMenu.addEventListener("click", () => menu.classList.remove("active"));
    }

    /* ===== CART ===== */
    const cart = document.querySelector(".cart");
    const cartIcon = document.getElementById("cart-icon");
    const cartClose = document.getElementById("cart-close");

    if (cartIcon && cart) {
        cartIcon.addEventListener("click", () => {
            cart.classList.add("active");
        });
    }

    if (cartClose && cart) {
        cartClose.addEventListener("click", () => {
            cart.classList.remove("active");
        });
    }

});

const addCartButtons = document.querySelectorAll(".add-cart");
addCartButtons.forEach(button => {
    button.addEventListener("click", event => {
        const productBox = event.target.closest(".product-box");
        addTocart(productBox);
    });
});
const cartContent = document.querySelector(".cart-content")


const addTocart = productBox => {
    const productImgSrc = productBox.querySelector("img").src;
    const productTitle = productBox.querySelector(".product-title").textContent;
    const productPrice = productBox.querySelector(".price").textContent;



    // 🔥 Auto-detect product type using product title
    const title = productTitle.toLowerCase();

    // dress keywords
    const dressKeywords = ["dress", "gown", "wear", "native", "agbada", "top", "senator", "kaftan", "set"];

    // shoe keywords
    const shoeKeywords = ["shoe", "sneaker", "slippers", "slides", "boots", "loafers", "trainers"];

    // cap keywords
    const capKeywords = ["cap", "hat", "face cap", "snapback"];

    let productType = "other";

    if (dressKeywords.some(word => title.includes(word))) {
        productType = "dress";
    } else if (shoeKeywords.some(word => title.includes(word))) {
        productType = "shoes";
    } else if (capKeywords.some(word => title.includes(word))) {
        productType = "cap";
    }


    // 🔥 Auto-build size options
    let sizeOptions = "<option>Your Size</option>";

    const sizeMap = {
        dress: ["XXL", "XL", "Large", "Medium", "Small"],
        shoes: [39, 40, 41, 43, 44, 45, 46],
        cap: [20, 24, 26, 28, 30, 32, 34],
    };

    if (sizeMap[productType]) {
        sizeMap[productType].forEach(size => {
            sizeOptions += `<option>${size}</option>`;
        });
    } else {
        sizeOptions += `<option>N/A</option>`;
    }

    // Prevent duplicates
    const cartItems = cartContent.querySelectorAll(".cart-product-title");
    for (item of cartItems) {
        if (item.textContent === productTitle) {
            alert("This item is already in the cart.");
            return;
        }
    }

    // Build cart card
    const cartBox = document.createElement("div");
    cartBox.classList.add("cart-box");
    cartBox.innerHTML = `
     <img src="${productImgSrc}" class="cart-img">
        <div class="cart-detail">
            <h2 class="cart-product-title">${productTitle}</h2>
            <span class="cart-price">${productPrice}</span>

            <div class="cart-quantity">
                <button id="decrement">-</button>
                <span class="number">1</span>
                <button id="increment">+</button>
            </div>

            <div class="product-size">
                <select>${sizeOptions}</select>
            </div>
        </div>
        <i class="ri-delete-bin-line cart-remove"></i>
    `;

    cartContent.appendChild(cartBox);

    // Remove item
    cartBox.querySelector(".cart-remove").addEventListener("click", () => {
        cartBox.remove();
        updateCartCount(-1);
        updateTotalPrice();
    });

    // Quantity buttons
    cartBox.querySelector(".cart-quantity").addEventListener("click", event => {
        const numberElement = cartBox.querySelector(".number");
        const decrementButton = cartBox.querySelector("#decrement");
        let quantity = parseInt(numberElement.textContent);

        if (event.target.id === "decrement" && quantity > 1) {
            quantity--;
            if (quantity === 1) decrementButton.style.color = "#999";
        } else if (event.target.id === "increment") {
            quantity++;
            decrementButton.style.color = "#333";
        }

        numberElement.textContent = quantity;
        updateTotalPrice();
    });

    updateCartCount(1);
    updateTotalPrice();
};


const updateTotalPrice = () => {
    const totalPriceElement = document.querySelector(".total-price");
    const cartBoxes = cartContent.querySelectorAll(".cart-box");
    let total =  0;
    cartBoxes.forEach(cartBox => {
        const priceElement = cartBox.querySelector(".cart-price");
        const quantityElement = cartBox.querySelector(".number");
        const price =  priceElement.textContent.replace("₦", "");
        const quantity = quantityElement.textContent;
        total += price * quantity;
    });
    totalPriceElement.textContent = `₦${total}`;
};

let cartItemCount = 0;
const updateCartCount = change => {
    const cartItemCountBadge = document.querySelector(".cart-item-count");
    cartItemCount += change;
    if (cartItemCount > 0) {
        cartItemCountBadge.style.visibility = "visible";
        cartItemCountBadge.textContent = cartItemCount;
    } else {
        cartItemCountBadge.style.visibility ="hidden";
        cartItemCountBadge.textContent = "";
    }
    

};

const buyNowButton = document.querySelector(".btn-buy")
buyNowButton.addEventListener("click", () => {
    const cartBoxes = cartContent.querySelectorAll(".cart-box");
    if (cartBoxes.length === 0) {
        alert("Your cart is empty, please add items to your cart before buying");
        return;
    }

    // Gather cart data
    const cartData = [];
    cartBoxes.forEach(cartBox => {
        const title = cartBox.querySelector(".cart-product-title").textContent;
        const price = cartBox.querySelector(".cart-price").textContent.replace("₦", "");
        const quantity = cartBox.querySelector(".number").textContent;
        const img = cartBox.querySelector(".cart-img").src;
        const sizeSelect = cartBox.querySelector("select");
        const size = sizeSelect ? sizeSelect.value : "Not selected";

        cartData.push({
            title: title,
            price: parseFloat(price),
            quantity: parseInt(quantity),
            size: size,
            image: img
        });
    });

    // Send to Flask backend
    fetch("/cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(cartData)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response from Flask:", data);
        alert("Thank you for your purchase!");


    // user clicks "Pay" button
    fetch('/paystack/initialize', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    if (data.authorization_url) {
      window.location.href = data.authorization_url;
    } else {
      alert('Error initializing payment');
    }
  });



        // Optionally clear cart visually
        cartBoxes.forEach(cartBox => cartBox.remove());
        cartItemCount = 0;
        updateCartCount(0);
        updateTotalPrice();
    })
    .catch(error => {
        console.error("Error sending cart data:", error);
    });
});

fetch("/cart/clear", { method: "POST" });



