
document.body.classList.add('loading'); // Spinner ochilganda
document.body.classList.remove('loading'); // Spinner yopilganda
document.getElementById('reloadPage').addEventListener('click', function() {
    location.reload();
});
// WebSocketni serverga ulash
const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${protocol}://${window.location.host}/ws/messages/`);
document.getElementById('editMessageModal').addEventListener('click', function() {
    location.reload();
});
document.addEventListener('DOMContentLoaded', function () {
    const editBtn = document.getElementById('editMessageModal');
    if (editBtn) {
        editBtn.addEventListener('click', function() {
            location.reload();
        });
    }

    const reloadOchirish = document.getElementById('reload_ochirish');
    const reloadMessage = document.getElementById('reload_message');

    if (reloadOchirish) {
        reloadOchirish.addEventListener('click', function () {
            location.reload();
        });
    }

    if (reloadMessage) {
        reloadMessage.addEventListener('click', function () {
            location.reload();
        });
    }
});

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'message') {
        const messageList = document.getElementById("messages");
        const li = document.createElement("div");
        li.classList.add("message");
        li.id = `msg-${data.id}`;
        li.innerHTML = `${data.message}`;

        if (!data.taken_by) {
            li.innerHTML += `<button class="reload_message" onclick="takeMessage(${data.id}, this)">
                                Olindi <i class="fa-solid fa-check"></i>
                             </button>`;
        } else {
            li.innerHTML += `<b>(Olingan: ${data.taken_by})</b>`;
        }

        messageList.prepend(li);

        // FontAwesome ikonlarni yangilash
        if (window.FontAwesome && window.FontAwesome.dom) {
            window.FontAwesome.dom.i2svg();
        }
    } else if (data.type === 'delete') {
        // Xabarni o‘chirish
        const elem = document.getElementById(`msg-${data.id}`);
        if (elem) elem.remove();
    } else if (data.type === 'taken') {
        const elem = document.getElementById(`msg-${data.id}`);
        if (elem) {
            elem.innerHTML = ` ${data.message} <b>(Olingan: ${data.taken_by})</b>`;
            elem.innerHTML += `<button onclick="deleteMessage(${data.id})" class="btn delete-btn">🗑️ O‘chirish</button>`;
        }
    }
};

function takeMessage(id, button) {
    socket.send(JSON.stringify({
        action: 'take',
        id: id
    }));
}

// CSRF token olish
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Cookie nomini topish
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


const csrftoken = getCookie('csrftoken');

        // Modalni ochish
function openMessageModal(messageId) {
    const messageDiv = document.getElementById(`my-msg-${messageId}`);
    const modal = document.getElementById("message-modal");
    const modalText = document.getElementById("modal-text");

    // Form ichidagi textarea ni to‘g‘ri olish
    const textarea = messageDiv.querySelector("textarea");
    if (textarea) {
        modalText.value = textarea.value;
    } else {
        console.error("Textarea topilmadi.");
        return;
    }

    modal.style.display = "block";
    modal.dataset.messageId = messageId;
}

// Modalni yopish
function closeMessageModal() {
    const modal = document.getElementById("message-modal");
    modal.style.display = "none";
}
window.onload = function () {
    const button = document.getElementById("sendButton");
    const lastSent = localStorage.getItem('lastSentTime');
    const now = new Date().getTime();

    if (lastSent && now - lastSent < 2 * 60 * 1000) {
        const secondsLeft = Math.ceil((2 * 60 * 1000 - (now - lastSent)) / 1000);
        button.disabled = true;
        button.innerText = `Yuborildi... (${secondsLeft} soniya kuting)`;

        setTimeout(() => {
            button.disabled = false;
            button.innerText = "Yuborish";
        }, 2 * 60 * 1000 - (now - lastSent));
    }
};

document.getElementById("sendButton").addEventListener("click", function () {
    const now = new Date().getTime();
    localStorage.setItem('lastSentTime', now.toString());
});

// Modalda tahrirlash
function editMessageModal() {
    const modal = document.getElementById("message-modal");
    const messageId = modal.dataset.messageId;
    const messageText = document.getElementById("modal-text").value;

    fetch(`/edit_message/${messageId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            text: messageText
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            console.log("Xabar tahrirlandi:", data);
            closeMessageModal();
        } else {
            console.error("Xabar tahrirlanmadi:", data.error);
        }
    })
    .catch(err => {
        console.error("Xatolik:", err);
    });
}

// Modalda o'chirish
function deleteMessageModal() {
    const modal = document.getElementById("message-modal");
    const messageId = modal.dataset.messageId;

    fetch(`/delete_message/${messageId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            console.log("Xabar o'chirildi:", data);
            closeMessageModal();
            const elem = document.getElementById(`msg-${messageId}`);
            if (elem) elem.remove();
        } else {
            console.error("Xabar o'chirilmagan:", data.error);
        }
    })
    .catch(err => {
        console.error("Xatolik:", err);
    });
}

fetch('send_to_groups/<int:msg_id>/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken // agar CSRF himoyasi ishlatilsa
    },
    body: '' // kerak bo‘lsa ma’lumot yuborish mumkin
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));

function showLoading() {
        const button = document.getElementById("sendButton");
        const spinner = document.getElementById("page-spinner");

        // Tugma bloklanadi
        button.disabled = true;

        // Tugma matni o‘zgaradi
        button.innerText = "⏳ Yuborilmoqda...";

        // Spinner ko‘rinadi
        spinner.style.display = "block";

        return true; // form yuborilishi davom etadi
    }

    // Bu qism foydali: sahifa reload bo‘lsa, tugma holati tiklanadi
    window.addEventListener("pageshow", function () {
        const button = document.getElementById("sendButton");
        const spinner = document.getElementById("page-spinner");

        button.disabled = false;
        button.innerText = "Yuborish";
        spinner.style.display = "none";
    });
