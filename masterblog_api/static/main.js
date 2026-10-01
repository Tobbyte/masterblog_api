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

            // Build each post from nested elements so its fields can be edited safely.
            data.forEach(post => {
                postContainer.appendChild(createPostElement(post));
            });
        })
        .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}

function createPostElement(post) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post';
    postDiv.dataset.postId = post.id;

    const heading = document.createElement('h2');
    const author = document.createElement('span');
    author.className = 'post-author';
    author.textContent = post.author || 'n.n.';
    const title = document.createElement('span');
    title.className = 'post-title';
    title.textContent = post.title;
    heading.append(author, ': ', title);

    const content = document.createElement('p');
    content.className = 'post-content';
    content.textContent = post.content;

    const actions = document.createElement('div');
    actions.className = 'post-actions';

    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.textContent = 'Delete';
    deleteButton.addEventListener('click', () => deletePost(post.id));

    const editButton = document.createElement('button');
    editButton.type = 'button';
    editButton.className = 'edit-button';
    editButton.textContent = 'Edit';
    editButton.addEventListener('click', () => editPost(post.id));

    actions.append(deleteButton, editButton);
    postDiv.append(heading, content, actions);
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
    const saveButton = document.createElement('button');
    saveButton.type = 'button';
    saveButton.className = 'save-button';
    saveButton.textContent = 'Save';
    saveButton.addEventListener('click', () => savePost(postId));
    editButton.replaceWith(saveButton);
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
