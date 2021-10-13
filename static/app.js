const likeBtn = document.querySelector('.btn-like');
const thumb = document.querySelector('.thumb');
const modal = document.getElementById("message-modal");
const msgBtn = document.getElementById("modal-btn");
const msgSpan = document.getElementsByClassName("close")[0];
const msgSubmitBtn = document.querySelector('#msg-submit-btn')
const msgText = document.querySelector('#message-text')

try {
    likeBtn.addEventListener('click', async function (e) {
        e.preventDefault()
        const msgId = e.target.closest('button').id
        console.log(msgId)
        const res = await axios.post('/users/like', {
            'msg_id': msgId
        })
        console.log('res', res.data)
        if (res.data === 'like added') {
            thumb.classList.remove('fa-thumbs-down')
            thumb.classList.add('fa-thumbs-up')
        }
        else {
            thumb.classList.remove('fa-thumbs-up')
            thumb.classList.add('fa-thumbs-down')
        }

    })
} catch {
    console.log('like btn not found')
}



// When the user clicks on the button, open the modal
msgBtn.addEventListener('click', function () {
    modal.style.display = "block";
});

// When the user clicks on <span> (x), close the modal
msgSpan.addEventListener('click', function () {
    modal.style.display = "none";
});

// When the user clicks anywhere outside of the modal, close it
window.addEventListener('click', function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
});

try {
    msgSubmitBtn.addEventListener('click', async function (e) {
        e.preventDefault()
        const msg = msgText.value
        try {
            const res = await axios.post('/messages/new', {
                'msg_text': msg
            })
            modal.style.display = "none";
        }
        catch {
            console.log('res failed')
        }
    })
} catch {
    console.log('submit btn not found')
}
