function addLikeEventListeners() {
    $('.like-button').on('click', function() {
        const postId = $(this).data('post-id');
        $.post(`/posts/like/${postId}`, function(response) {
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