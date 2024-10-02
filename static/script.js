// Function to send interaction data to the server
function sendInteraction() {
    const userInput = document.getElementById('userInput').value;

    // Ensure that user input is not empty
    if (userInput.trim() === '') {
        alert('Please enter a response before sending.');
        return;
    }

    fetch('/interact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_input: userInput })
    })
    .then(response => response.json())
    .then(data => {
        // Display DM Action in the game display
        const gameDisplay = document.getElementById('gameDisplay');
        gameDisplay.innerHTML += `<p>${data.dm_action}</p>`;
        gameDisplay.scrollTop = gameDisplay.scrollHeight; // Scroll to the bottom of the game display

        // Update other elements
        document.getElementById('dmAction').innerText = data.dm_action;
        document.getElementById('feedbackScore').innerText = data.feedback_score.toFixed(2);
        document.getElementById('updatedRewards').innerText = JSON.stringify(data.updated_rewards);

        // Clear the user input field
        document.getElementById('userInput').value = '';
    })
    .catch(error => console.error('Error:', error));
}

// Function to clear the game display
function clearGameDisplay() {
    document.getElementById('gameDisplay').innerHTML = '';
}
