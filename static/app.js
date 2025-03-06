function addOutput(command, result) {
    const outputContainer = document.getElementById('output');
    const entry = document.createElement('div');
    entry.className = 'output-entry';
    
    const commandSpan = document.createElement('span');
    commandSpan.className = 'command';
    commandSpan.textContent = command;
    
    const resultSpan = document.createElement('span');
    resultSpan.className = 'result';
    resultSpan.textContent = ' → ' + result;
    
    entry.appendChild(commandSpan);
    entry.appendChild(resultSpan);
    
    outputContainer.appendChild(entry);
    outputContainer.scrollTop = outputContainer.scrollHeight;
}

function clearOutput() {
    document.getElementById('output').innerHTML = '';
}

async function executeSet() {
    const name = document.getElementById('set-name').value.trim();
    const value = document.getElementById('set-value').value.trim();
    
    if (!name || !value) {
        alert('Both name and value are required for SET command');
        return;
    }
    
    try {
        const response = await fetch(`/set?name=${encodeURIComponent(name)}&value=${encodeURIComponent(value)}`);
        const result = await response.text();
        addOutput(`SET ${name} = ${value}`, result);
    } catch (error) {
        addOutput(`SET ${name} = ${value}`, `Error: ${error.message}`);
    }
}

async function executeGet() {
    const name = document.getElementById('get-name').value.trim();
    
    if (!name) {
        alert('Name is required for GET command');
        return;
    }
    
    try {
        const response = await fetch(`/get?name=${encodeURIComponent(name)}`);
        const result = await response.text();
        addOutput(`GET ${name}`, result);
    } catch (error) {
        addOutput(`GET ${name}`, `Error: ${error.message}`);
    }
}

async function executeUnset() {
    const name = document.getElementById('unset-name').value.trim();
    
    if (!name) {
        alert('Name is required for UNSET command');
        return;
    }
    
    try {
        const response = await fetch(`/unset?name=${encodeURIComponent(name)}`);
        const result = await response.text();
        addOutput(`UNSET ${name}`, result);
    } catch (error) {
        addOutput(`UNSET ${name}`, `Error: ${error.message}`);
    }
}

async function executeNumEqualTo() {
    const value = document.getElementById('numequalto-value').value.trim();
    
    if (!value) {
        alert('Value is required for NUMEQUALTO command');
        return;
    }
    
    try {
        const response = await fetch(`/numequalto?value=${encodeURIComponent(value)}`);
        const result = await response.text();
        addOutput(`NUMEQUALTO ${value}`, result);
    } catch (error) {
        addOutput(`NUMEQUALTO ${value}`, `Error: ${error.message}`);
    }
}

async function executeUndo() {
    try {
        const response = await fetch('/undo');
        const result = await response.text();
        addOutput('UNDO', result);
    } catch (error) {
        addOutput('UNDO', `Error: ${error.message}`);
    }
}

async function executeRedo() {
    try {
        const response = await fetch('/redo');
        const result = await response.text();
        addOutput('REDO', result);
    } catch (error) {
        addOutput('REDO', `Error: ${error.message}`);
    }
}

async function executeEnd() {
    if (!confirm('Are you sure you want to clear all data? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/end');
        const result = await response.text();
        addOutput('END', result);
    } catch (error) {
        addOutput('END', `Error: ${error.message}`);
    }
}
