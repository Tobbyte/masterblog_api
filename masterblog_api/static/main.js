/* 
Some changes made by ai. Following queries were used:
1: make the #sym:postDiv in a propper way with nested elements to make them contenteditable
when button "editPost" is clicked. when in edit mode, add button "save" which umdates
the post via the existing put route.
2: instead of this cumbersome inline building, extend index_csr.html with proper post
container thats populated and repeated.
3: see pagination in backend_app.py and add appropriate pagination button to html and use in main.js
4: see like_post route in backend_app.py and implement functionality and style like in intex_ssr.html
*/
let currentPage = 1;

// Function that runs once the window is fully loaded
window.onload = function () {
    // Attempt to retrieve the API base URL from the local storage
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    // If a base URL is found in local storage, load the posts
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }

    document.getElementById('previous-page').addEventListener('click', () => {
        loadPosts(currentPage - 1);
    });
    document.getElementById('next-page').addEventListener('click', () => {
        loadPosts(currentPage + 1);
    });
}

// Function to fetch all the posts from the API and display them on the page
function loadPosts(page = 1) {
    // Retrieve the base URL from the input field and save it to local storage
    var baseUrl = document.getElementById('api-base-url').value;
    localStorage.setItem('apiBaseUrl', baseUrl);

    // Use the Fetch API to send a GET request to the /posts endpoint
    fetch(`${baseUrl}/posts?page=${page}`, {
        credentials: 'include'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Unable to load posts (${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            const posts = Array.isArray(data) ? data : data.posts;
            currentPage = data.page || page;

            // Clear out the post container first
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = '';

            posts.forEach(post => {
                postContainer.appendChild(createPostElement(post));
            });

            updatePagination(data);
        })
        .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    const previousButton = document.getElementById('previous-page');
    const nextButton = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    const totalPages = data.total_pages || 1;

    pagination.hidden = totalPages <= 1;
    previousButton.disabled = currentPage <= 1;
    nextButton.disabled = currentPage >= totalPages;
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
}

function createPostElement(post) {
    const template = document.getElementById('post-template');
    const postDiv = template.content.firstElementChild.cloneNode(true);
    postDiv.className = 'post';
    postDiv.dataset.postId = post.id;

    const author = postDiv.querySelector('.post-author');
    author.textContent = post.author || 'n.n.';
    const title = postDiv.querySelector('.post-title');
    title.textContent = post.title;
    const content = postDiv.querySelector('.post-content');
    content.textContent = post.content;

    const deleteButton = postDiv.querySelector('.delete-button');
    deleteButton.addEventListener('click', () => deletePost(post.id));

    const editButton = postDiv.querySelector('.edit-button');
    editButton.addEventListener('click', () => editPost(post.id));

    const saveButton = postDiv.querySelector('.save-button');
    saveButton.addEventListener('click', () => savePost(post.id));

    const likeButton = postDiv.querySelector('.like-button');
    const likeCount = postDiv.querySelector('.like-count');
    likeCount.textContent = Array.isArray(post.liked_by)
        ? post.liked_by.length
        : 0;
    likeButton.setAttribute('aria-pressed', 'false');
    likeButton.addEventListener('click', () => likePost(post.id));
    return postDiv;
}

function likePost(postId) {
    const baseUrl = document.getElementById('api-base-url').value;

    fetch(`${baseUrl}/posts/${postId}/like`, {
        method: 'POST',
        credentials: 'include'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Unable to update like (${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            const postDiv = document.querySelector(`[data-post-id="${postId}"]`);
            const likeButton = postDiv.querySelector('.like-button');
            const likeCount = postDiv.querySelector('.like-count');
            likeButton.textContent = data.liked ? '💔' : '❤️';
            likeButton.setAttribute('aria-pressed', data.liked);
            likeCount.textContent = data.like_count;
        })
        .catch(error => console.error('Error:', error));
}

function editPost(postId) {
    const postDiv = document.querySelector(`[data-post-id="${postId}"]`);
    if (!postDiv || postDiv.dataset.editing === 'true') {
        return;
    }

    postDiv.dataset.editing = 'true';
    const author = postDiv.querySelector('.post-author');
    const title = postDiv.querySelector('.post-title');
    const content = postDiv.querySelector('.post-content');

    [author, title, content].forEach(field => {
        field.contentEditable = 'true';
        field.classList.add('edit-field');
        field.spellcheck = true;
    });

    const editButton = postDiv.querySelector('.edit-button');
    const saveButton = postDiv.querySelector('.save-button');
    editButton.hidden = true;
    saveButton.hidden = false;
    title.focus();
}

function savePost(postId) {
    const postDiv = document.querySelector(`[data-post-id="${postId}"]`);
    if (!postDiv) {
        return;
    }

    const baseUrl = document.getElementById('api-base-url').value;
    const postData = {
        author: postDiv.querySelector('.post-author').textContent.trim(),
        title: postDiv.querySelector('.post-title').textContent.trim(),
        content: postDiv.querySelector('.post-content').textContent.trim()
    };

    fetch(`${baseUrl}/posts/${postId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Unable to update post (${response.status})`);
            }
            return response.json();
        })
        .then(() => loadPosts())
        .catch(error => console.error('Error:', error));
}

// Function to send a POST request to the API to add a new post
function addPost() {
    // Retrieve the values from the input fields
    var baseUrl = document.getElementById('api-base-url').value;
    var postAuthor = document.getElementById('author').value;
    var postTitle = document.getElementById('post-title').value;
    var postContent = document.getElementById('post-content').value;

    // Use the Fetch API to send a POST request to the /posts endpoint
    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ author: postAuthor, title: postTitle, content: postContent })
    })
        .then(response => response.json())  // Parse the JSON data from the response
        .then(post => {
            console.log('Post added:', post);
            loadPosts(); // Reload the posts after adding a new one
        })
        .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}

// Function to send a DELETE request to the API to delete a post
function deletePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;

    // Use the Fetch API to send a DELETE request to the specific post's endpoint
    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
        .then(response => {
            console.log('Post deleted:', postId);
            loadPosts(); // Reload the posts after deleting one
        })
        .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}
