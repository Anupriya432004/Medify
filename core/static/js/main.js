// Load initial all medicines by sending empty query
window.onload = () => {
    if (document.getElementById("resultsGrid")) searchMedicines("");
    startCarousel();
    if (document.body.dataset.authenticated === "true") refreshCartCount();
    const pendingCartItem = sessionStorage.getItem("pendingCartItem");
    if (pendingCartItem && document.body.dataset.authenticated === "true") {
        sessionStorage.removeItem("pendingCartItem");
        const medicine = JSON.parse(pendingCartItem);
        openModal(medicine.id, medicine.name, medicine.price);
    }
};

// Carousel Logic
let slideIndex = 0;
let slideInterval;
function startCarousel() {
    slideInterval = setInterval(() => { changeSlide(1); }, 5000);
}
function changeSlide(n) {
    showSlide(slideIndex += n);
}
function currentSlide(n) {
    showSlide(slideIndex = n);
    clearInterval(slideInterval);
    startCarousel();
}
function showSlide(n) {
    const slides = document.getElementsByClassName("carousel-slide");
    const dots = document.getElementsByClassName("dot");
    if (!slides.length) return;
    if (n >= slides.length) slideIndex = 0;
    if (n < 0) slideIndex = slides.length - 1;
    for (let i = 0; i < slides.length; i++) slides[i].classList.remove("active");
    for (let i = 0; i < dots.length; i++) dots[i].classList.remove("active");
    slides[slideIndex].classList.add("active");
    dots[slideIndex].classList.add("active");
}

function displayMedicines(medicines, title="Search Results") {
    document.getElementById("resultsTitle").innerText = title;
    const grid = document.getElementById("resultsGrid");
    
    if (medicines && medicines.length > 0) {
        let html = "";
        medicines.forEach(med => {
            html += `
                <div class="card">
                    <div class="card-img">
                        <img src="${med.image}" alt="${med.name}" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 4px;">
                    </div>
                    <div>
                        <div class="card-title">${med.name}</div>
                        <div class="card-desc">${med.description}</div>
                        <div class="card-price">₹${med.price}</div>
                    </div>
                    <button class="add-to-cart" onclick="openModal(${med.id}, '${med.name}', ${med.price})">ADD TO CART</button>
                </div>
            `;
        });
        grid.innerHTML = html;
    } else {
        grid.innerHTML = "<p>No medicines found for your query.</p>";
    }
}

function searchMedicines(forceQuery = null) {
    if (!document.getElementById("resultsGrid")) return;
    const query = forceQuery !== null ? forceQuery : document.getElementById("searchInput").value;
    const grid = document.getElementById("resultsGrid");
    grid.innerHTML = "<p>Searching...</p>";
    document.getElementById("aiBanner").style.display = "none";

    fetch(`/medicines/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => displayMedicines(data.medicines, query ? `Results for "${query}"` : "All Medicines"))
        .catch(e => { grid.innerHTML = "<p>Error loading catalog.</p>"; });
}

function startVoiceSearch() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Voice search not supported in this browser."); return; }
    
    const recognition = new SpeechRecognition();
    const voiceBtn = document.getElementById('voiceBtn');
    const searchInput = document.getElementById("searchInput");

    recognition.onstart = function() {
        voiceBtn.classList.add("recording");
        searchInput.placeholder = "Listening to your symptoms...";
        searchInput.value = "";
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        searchInput.value = transcript;
        callAIAssistant(transcript);
    };

    recognition.onend = function() {
        voiceBtn.classList.remove("recording");
        searchInput.placeholder = "Search for medicines or describe your symptoms...";
    };

    recognition.start();
}

function callAIAssistant(symptoms) {
    const grid = document.getElementById("resultsGrid");
    grid.innerHTML = "<p>Analyzing your symptoms...</p>";
    
    fetch(`/ai/recommend/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symptoms: symptoms })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const banner = document.getElementById("aiBanner");
            banner.style.display = "block";
            document.getElementById("aiAdvice").innerText = data.advice;
            document.getElementById("aiDisclaimer").innerText = `⚠️ ${data.disclaimer}`;
            
            displayMedicines(data.medicines, "Recommended Medicines");
        } else {
            grid.innerHTML = `<p style="color: red;">${data.error}</p>`;
        }
    })
    .catch(e => { grid.innerHTML = "<p>Service offline.</p>"; });
}

// Checkout & AI Validation Flow
let currentPrice = 0;
let isVerified = false;

function openModal(id, name, price) {
    if (document.body.dataset.authenticated !== "true") {
        sessionStorage.setItem("pendingCartItem", JSON.stringify({ id, name, price }));
        document.getElementById("authModal").style.display = "flex";
        return;
    }
    sessionStorage.removeItem("pendingCartItem");
    fetch("/orders/cart/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ medicine_id: id })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not add this medicine to your cart.");
        }
        updateCartCount(data.cart_count);
        openCheckoutModal(id, name, price);
    })
    .catch(error => {
        alert(error.message);
    });
}

function openCheckoutModal(id, name, price) {
    document.getElementById("checkoutModal").style.display = "flex";
    document.querySelector("#checkoutModal h2").innerText = "Patient Details & Checkout";
    document.getElementById("checkoutMedicineId").value = id;
    document.getElementById("checkoutMedicineName").value = name;
    currentPrice = price;
    isVerified = false;
    document.getElementById("aiCheckoutAdvice").style.display = "none";
    document.getElementById("proceedBtn").innerText = "Verify Profile with AI";
}

function getCookie(name) {
    const cookie = document.cookie
        .split("; ")
        .find(value => value.startsWith(`${name}=`));
    return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

function updateCartCount(count) {
    const cartCount = document.getElementById("cartCount");
    if (cartCount) cartCount.innerText = count;
}

function refreshCartCount() {
    fetch("/orders/cart/")
        .then(async response => {
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || "Could not load your cart.");
            }
            updateCartCount(data.cart_count);
        })
        .catch(error => console.error(error));
}

function openCart() {
    if (document.body.dataset.authenticated !== "true") {
        const authModal = document.getElementById("authModal");
        if (authModal) {
            authModal.style.display = "flex";
        } else {
            window.location.href = "/users/login/";
        }
        return;
    }

    document.getElementById("cartModal").style.display = "flex";
    loadCartItems();
}

function closeCart() {
    document.getElementById("cartModal").style.display = "none";
}

function loadCartItems() {
    const cartItems = document.getElementById("cartItems");
    cartItems.textContent = "Loading cart...";

    fetch("/orders/cart/")
        .then(async response => {
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || "Could not load your cart.");
            }
            renderCart(data);
        })
        .catch(error => {
            cartItems.textContent = error.message;
        });
}

function renderCart(data) {
    const cartItems = document.getElementById("cartItems");
    cartItems.replaceChildren();
    updateCartCount(data.cart_count);
    document.getElementById("cartTotal").textContent = data.total;
    document.getElementById("cartPayBtn").hidden = data.items.length === 0;

    if (!data.items.length) {
        const emptyMessage = document.createElement("p");
        emptyMessage.textContent = "Your cart is empty.";
        cartItems.appendChild(emptyMessage);
        return;
    }

    const list = document.createElement("ul");
    list.className = "cart-items-list";
    data.items.forEach(item => {
        const row = document.createElement("li");
        row.className = "cart-item";

        const details = document.createElement("div");
        details.className = "cart-item-details";
        const name = document.createElement("strong");
        name.textContent = item.name;
        const quantityAndPrice = document.createElement("span");
        quantityAndPrice.textContent =
            `Qty: ${item.quantity} × ₹${item.price} = ₹${item.subtotal}`;
        details.append(name, quantityAndPrice);

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "cart-remove-btn";
        removeButton.textContent = "Remove";
        removeButton.addEventListener("click", () => removeCartItem(item.id));

        row.append(details, removeButton);
        list.appendChild(row);
    });
    cartItems.appendChild(list);
}

function checkoutCart() {
    const payButton = document.getElementById("cartPayBtn");
    payButton.disabled = true;

    fetch("/orders/cart/")
        .then(async response => {
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || "Could not load your cart.");
            }
            if (!data.items.length) {
                renderCart(data);
                throw new Error("Your cart is empty.");
            }

            const options = {
                key: "rzp_test_TSNJSF0X6kqf1b",
                amount: Math.round(Number(data.total) * 100),
                currency: "INR",
                name: "Medify",
                description: "Medicine Cart Purchase",
                prefill: {
                    name: document.body.dataset.userName || ""
                },
                theme: { color: "#d32f2f" },
                handler: function (payment) {
                    fetch("/orders/create/", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            cart_checkout: true,
                            patient_name: document.body.dataset.userName || "Customer",
                            payment_id: payment.razorpay_payment_id
                        })
                    })
                    .then(async response => {
                        const order = await response.json();
                        if (!response.ok || !order.success) {
                            throw new Error(order.error || "Could not record the order.");
                        }
                        updateCartCount(order.cart_count);
                        closeCart();
                        alert(`Payment successful! Payment ID: ${payment.razorpay_payment_id}`);
                    })
                    .catch(error => {
                        alert(`Payment completed, but the order could not be recorded: ${error.message}`);
                    })
                    .finally(() => {
                        payButton.disabled = false;
                    });
                },
                modal: {
                    ondismiss: function () {
                        payButton.disabled = false;
                    }
                }
            };

            closeCart();
            const razorpay = new Razorpay(options);
            razorpay.on("payment.failed", function (payment) {
                alert(`Payment failed: ${payment.error.description}`);
                payButton.disabled = false;
            });
            razorpay.open();
        })
        .catch(error => {
            alert(error.message);
            payButton.disabled = false;
        });
}

function removeCartItem(itemId) {
    fetch("/orders/cart/", {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not remove this item.");
        }
        renderCart(data);
    })
    .catch(error => {
        alert(error.message);
    });
}

function closeAuthModal() {
    document.getElementById("authModal").style.display = "none";
    sessionStorage.removeItem("pendingCartItem");
}

function closeModal() {
    document.getElementById("checkoutModal").style.display = "none";
}

function verifyAndCheckout() {
    const btn = document.getElementById("proceedBtn");
    const name = document.getElementById("patientName").value;
    const diabetes = document.getElementById("hasDiabetes").checked;
    const thyroid = document.getElementById("hasThyroid").checked;
    const other = document.getElementById("otherConditions").value;
    const medName = document.getElementById("checkoutMedicineName").value;

    if (!name) { alert("Please enter Patient Name"); return; }

    if (!isVerified) {
        // Step 1: Verify with AI
        btn.innerText = "Verifying...";
        btn.disabled = true;

        // Simulating the AI verification response.
        setTimeout(() => {
            const adviceBox = document.getElementById("aiCheckoutAdvice");
            adviceBox.style.display = "block";
            
            let advice = `<strong>Medical Note:</strong> For ${medName}, please take 1 dose after meals. `;
            if (diabetes && medName.includes("Syrup")) {
                advice += `<br><span style="color:red;">⚠️ WARNING: Since you have Diabetes, please ensure this syrup is sugar-free.</span>`;
            } else if (diabetes) {
                advice += `Safe for diabetic patients if taken as prescribed.`;
            } else if (thyroid) {
                advice += `Does not interfere with thyroid medication. Take normally.`;
            } else {
                advice += `Standard dosage applies. No contraindications found with your profile.`;
            }
            
            adviceBox.innerHTML = advice;
            btn.innerText = `Pay ₹${currentPrice} securely`;
            btn.disabled = false;
            isVerified = true;
        }, 1500);

    } else {
        // Step 2: Razorpay Fake Payment
        const options = {
            "key": "rzp_test_TSNJSF0X6kqf1b", 
            "amount": currentPrice * 100, 
            "currency": "INR",
            "name": "Medify",
            "description": "Medicine Purchase",
            "handler": function (response){
                // Save Order to Backend MySQL
                fetch('/orders/create/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        medicine_id: document.getElementById("checkoutMedicineId").value,
                        patient_name: name,
                        amount: currentPrice,
                        payment_id: response.razorpay_payment_id
                    })
                }).then(async orderResponse => {
                    const order = await orderResponse.json();
                    if (!orderResponse.ok || !order.success) {
                        throw new Error(order.error || "Could not record the order.");
                    }
                    alert(`Payment Successful & Order Recorded! Razorpay Payment ID: ${response.razorpay_payment_id}`);
                    updateCartCount(order.cart_count);
                    closeModal();
                }).catch(error => {
                    alert(`Payment completed, but the order could not be recorded: ${error.message}`);
                });
            },
            "prefill": { "name": name, "email": "user@medify.com" },
            "theme": { "color": "#d32f2f" }
        };
        const rzp1 = new Razorpay(options);
        rzp1.on('payment.failed', function (response){
            alert("Payment Failed! Reason: " + response.error.description);
        });
        rzp1.open();
    }
}
