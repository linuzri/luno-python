const config = require('./config.json');

function displayAccountId() {
    const accountId = config.luno_api_key; // Assuming 'account_id' is stored in 'luno_api_key'
    const accountIdElement = document.createElement('div');
    accountIdElement.textContent = `Account ID: ${accountId}`;
    accountIdElement.style.position = 'absolute';
    accountIdElement.style.top = '0';
    accountIdElement.style.width = '100%';
    accountIdElement.style.textAlign = 'center';
    accountIdElement.style.backgroundColor = '#f0f0f0';
    accountIdElement.style.padding = '10px';
    document.body.appendChild(accountIdElement);
}

window.onload = function() {
    displayAccountId();
}
