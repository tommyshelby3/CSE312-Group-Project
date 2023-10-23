function addLikeEventListeners() {
    // This selects all buttons with the class 'like-btn' and attaches a click event listener to them.
    $('.like-btn').on('click', function() {
        // Retrieve the post ID from the data attribute.
        const postId = $(this).data('post-id');

        // Here, you'd send a request to the server to update the like count for this post.
        // The specifics would depend on how your server is set up to receive these requests.
        $.post(`/posts/${postId}/like`, function(response) {
            // Handle the response. For example, you might update the number of likes in the post's HTML,
            // or if the server sends back the total number of likes, you could update with that number.
            console.log('Post liked:', response);
        });
    });
}

function fetchPosts() {                     
    $.get("/posts", function (data) {
        let postsHtml = '';
        data.forEach(post => {
            postsHtml += `<h2>${post.title}</h2>`;
            postsHtml += `<p>By: ${post.username}</p>`;
            postsHtml += `<p>${post.description}</p>`;
            // Adding a "Like" button with a data attribute for the post's unique identifier
            postsHtml += `<button class="like-btn" data-post-id="${post.id}">Like</button>`;
            postsHtml += '<hr>';
        });
        $('#postsContainer').html(postsHtml);

        // After the HTML is generated and added to the DOM, add click event listeners to the like buttons.
        addLikeEventListeners();
    });
}

function task() {
    fetchPosts();                       // Fetch all posts on page load

    
    setInterval(fetchPosts, 5000)
    $('#createPostForm').submit(function (e) {
        e.preventDefault();
        $.post("/post", $(this).serialize(), function (data) {
            if (data.success) {
                alert('Post created successfully!');
                fetchPosts();
            } else {
                alert(data.error);
            }
        });
    });
}