function addLikeEventListeners() {
  $('.like-button').on('click', function() {
    const postId = $(this).data('post-id');
    $.post(`/posts/like/${postId}`, function(response) {
    });
  });
}

function fetchPosts() {
  $.get("/posts", function(data) {
    let postsHtml = '';
    data.forEach(post => {
      postsHtml += `<h2>${post.title}</h2>`;
      postsHtml += `<p>By: ${post.username}</p>`;
      postsHtml += `<p>${post.description}</p>`;
      postsHtml += `<p>Likes: ${post.likes}</p>`;
      postsHtml += `<button class="like-button" data-post-id="${post._id}">Like</button>`;
      postsHtml += '<hr>';
    });
    $('#postsContainer').html(postsHtml);
    addLikeEventListeners();
  });
}

function task() {
  fetchPosts();// Fetch all posts on page load
  setInterval(fetchPosts, 5000)
  $('#createPostForm').submit(function(e) {
    e.preventDefault();
    $.post("/post", $(this).serialize(), function(data) {
      if (data.success) {
        alert('Post created successfully!');
        fetchPosts();
      } else {
        alert(data.error);
      }
    });
  });
}


const messages = document.getElementById('messages');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const socket = io.connect('https://appboard.live');

socket.addEventListener('open', (event) => {
  console.log('WebSocket connection established');
});

socket.addEventListener('message', (event) => {
  const message = event.data;
  const messageElement = document.createElement('div');
  messageElement.textContent = message;
  messages.appendChild(messageElement);
});

messageForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const message = messageInput.value;
  socket.send(message);
  messageInput.value = '';
});

//! ______________________________  Auction _______________________________
$(document).ready(function() {
  $('#upload-auction-form').submit(function(e) {
    e.preventDefault();
    var formData = new FormData(this);

    // AJAX request to server to submit auction item
    $.ajax({
      url: '/upload_auction_item',
      type: 'POST',
      data: formData,
      contentType: false,
      processData: false,
      success: function(response) {
        if (response.status === 'success') {
          // Handle success - close modal and reset form or give user feedback
          $('#auctionItemModal').modal('hide');
          $('#upload-auction-form')[0].reset();
          // Optionally, refresh the list of auction items or add the new item to the view
        } else {
          // Handle failure - display error message
          alert(response.error);
        }
      }
    });
  });

});

document.addEventListener('DOMContentLoaded', function() {
  var uploadButton = document.getElementById('upload-auction-item-btn');
  if (uploadButton) {
    uploadButton.addEventListener('click', function() {
      window.location.href = '/upload_auction';
    });
  }
});


socket.on('auction_winner', (data) => {

  let winnerHTML = `
    <div>
    ${data.username} won ${data.item} for $${data.finalPrice}
    </div>
`

  $('#auctionWinnersContainer').append(winnerHTML)

})


$(document).ready(function() {
  var auctionSocket = io.connect('/auction'); // Make sure the namespace matches your server setup

  auctionSocket.on('connect', function() {
    console.log('Connected to the auction namespace!');
  });

  auctionSocket.on('auction_winner', function(data) {
    var winnerHTML = '<div class="winner-entry">';
    winnerHTML += '<p><strong>' + data.username + '</strong> won <em>' + data.item + '</em> for $' + data.finalPrice + '</p>';
    winnerHTML += '</div>';

    // Append the new HTML to the auction winners container
    $('#auctionWinnersContainer').append(winnerHTML);
  });

  auctionSocket.emit('request_latest_auction_winners');
});
