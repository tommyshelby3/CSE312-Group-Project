const socket = io.connect('wss://appboard.live/auction', {
  transports: ['websocket'],
  secure: true,
});

console.log("Socket:", socket);

socket.addEventListener('open', () => {
  console.log('WebSocket connection established');
});

socket.on('connect', function() {
  console.log("Connected to server");
});


socket.on('my response', function(msg) {
  console.log("Received message:", msg);
  socket.emit('my response', { data: 'I\'m connected!' });
}
)

socket.on('new_bid', function(data) {
  if (data.auction_id) {
    // Update the UI with the new bid amount for the specific auction item
    $('#current-price-' + data.auction_id).text(data.new_price);
  }
});


socket.on('error', function(data) {
  if (data.error) {
    console.log(data)
    alert('Error: ' + data.error);
  }
});

socket.on('time_remaining_update', function(data) {
  console.log("Time Remaining Update:", data);
  if (data.auction_id) {
    // Update the UI with the new time remaining for the specific auction item
    $('#time-remaining-' + data.auction_id).text(data.time_remaining);
  }
});


function bid(auctionId) {
  const bidInputSelector = '#bid-input-' + auctionId;
  console.log("Selector:", bidInputSelector);
  const bidAmount = $(bidInputSelector).val();
  console.log("Bid Amount:", bidAmount);

  if (!bidAmount) {
    alert('Please enter a bid amount');
    return;
  }

  // Constructing the bid data
  const bidData = {
    type: 'bid',
    auction_id: auctionId,
    bid_amount: bidAmount
  };
  console.log("Bid Data:", bidData);
  socket.emit('bid', bidData);
  console.log("TEST");
}


socket.on('update_items', function(data) {
  console.log("Update Items:", data);
  var itemsHtml = '';
  data.auction_items.forEach(function(item) {
    itemsHtml += `
            <div class="auction-item">
                <h3>${item.title}</h3>
                <p>${item.description}</p>
                <img src="/static/images/${item.imagepath}" alt="Auction Item Image">
                <p>Current Price: $<span id="current-price-${item._id}">${item.price}</span></p>
                <p>Auction duration: ${item.duration}</p>
                <input type="number" id="bid-input-${item._id}" min="1" step="0.01" placeholder="Enter bid amount">
                <button class="btn btn-primary" onclick="bid('${item._id}')">Bid</button>
                <p>Time Remaining: <span id="time-remaining-${item._id}">calculating...</span></p>
            </div>`;
  });
  document.getElementById('auction-items').innerHTML = itemsHtml;
});



//! ______________________________  Auction _______________________________
$(document).ready(function() {
  // Ensure the bid function is accessible from any relevant event handlers
  window.bid = bid;
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
