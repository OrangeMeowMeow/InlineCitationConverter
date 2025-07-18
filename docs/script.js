// Initialize Pyodide
let pyodide;
let outputFileContent = "";
let pyodideInitialization;

async function initializePyodide() {
    console.log("Loading Pyodide...");
    pyodide = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
        stdout: console.log,
        stderr: console.error
    });
    
    // Load micropip for installing Python packages
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    
    // Install required packages
    console.log("Installing packages...");
    await micropip.install("bibtexparser");
    
    // Load our citation converter
    const response = await fetch('citation_converter.py');
    const converterCode = await response.text();
    await pyodide.runPythonAsync(converterCode);
    
    console.log("Pyodide initialized!");
}

// Start initialization
pyodideInitialization = initializePyodide().catch(err => {
    console.error("Pyodide initialization failed:", err);
});

// Handle form submission
document.getElementById('conversion-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading indicator
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('results').classList.add('d-none');
    
    try {
        // Wait for Pyodide to initialize
        await pyodideInitialization;
        
        // Read files
        const refsFile = document.getElementById('refs_file').files[0];
        const texFile = document.getElementById('tex_file').files[0];
        const bibFile = document.getElementById('bib_file').files[0];
        
        if (!refsFile || !texFile || !bibFile) {
            throw new Error('Please select all three files');
        }
        
        const refsText = await readFileAsText(refsFile);
        const texText = await readFileAsText(texFile);
        const bibText = await readFileAsText(bibFile);
        
        // Run conversion in Pyodide
        const converter = pyodide.globals.get('main');
        
        // CORRECTED: Properly handle asynchronous Python function
        const result = await converter(refsText, texText, bibText);
        const resultObj = result.toJs();

        // Properly access the nested dictionary
        outputFileContent = resultObj.output;
        const conversionMessages = resultObj.messages || [];
        
        // Display results
        showResults(conversionMessages);
    } catch (error) {
        console.error(error);
        alert(`Error: ${error.message}`);
    } finally {
        document.getElementById('loading').classList.add('d-none');
    }
});

// Helper function to read files
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

// Show conversion results
function showResults(messages) {
    const messagesElement = document.getElementById('messages');
    const downloadBtn = document.getElementById('download-btn');
    const resultsDiv = document.getElementById('results');
    
    if (messages && messages.length > 0) {
        messagesElement.classList.remove('d-none');
        messagesElement.innerHTML = `
            <h4 class="alert-heading">Conversion Notices</h4>
            <p>Some citations could not be automatically converted. Please review these messages:</p>
            <ul>${messages.map(msg => `<li>${msg}</li>`).join('')}</ul>
        `;
    } else {
        messagesElement.classList.add('d-none');
    }
    
    // Create download link
    downloadBtn.classList.remove('d-none');
    downloadBtn.href = URL.createObjectURL(new Blob([outputFileContent], {type: 'text/plain'}));
    downloadBtn.download = 'converted_document.tex';
    
    // Show results section
    resultsDiv.classList.remove('d-none');
}

// Reset form
document.getElementById('reset-btn').addEventListener('click', () => {
    document.getElementById('conversion-form').reset();
    document.getElementById('results').classList.add('d-none');
    document.getElementById('messages').classList.add('d-none');
    document.getElementById('download-btn').classList.add('d-none');
    outputFileContent = "";
});
