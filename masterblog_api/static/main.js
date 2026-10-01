/* 
Some changes made by ai. Following queries were used:
1: make the #sym:postDiv in a propper way with nested elements to make them contenteditable
when button "editPost" is clicked. when in edit mode, add button "save" which umdates
the post via the existing put route.
2: instead of this cumbersome inline building, extend index_csr.html with proper post
container thats populated and repeated.

*/
// Function that runs once the window is fully loaded
window.onload = function () {
    // Attempt to retrieve the API base URL from the local storage
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    // If a base URL is found in local storage, load the posts
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
}

// Function to fetch all the posts from the API and display them on the page
function loadPosts() {
    // Retrieve the base URL from the input field and save it to local storage
    var baseUrl = document.getElementById('api-base-url').value;
    localStorage.setItem('apiBaseUrl', baseUrl);

    // Use the Fetch API to send a GET request to the /posts endpoint
    fetch(baseUrl + '/posts')
        .then(response => response.json())  // Parse the JSON data from the response
        .then(data => {  // Once the data is ready, we can use it
            // Clear out the post container first
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = '';

            data.forEach(post => {
                postContainer.appendChild(createPostElement(post));
            });
        })
        .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
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
    return postDiv;
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
