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
        const result = await converter(refsText, texText, bibText);
        
        // Convert Python tuple to JavaScript array
        const resultArray = result.toJs();
        
        // Extract output and messages
        outputFileContent = resultArray[0] || texText;
        const messages = JSON.parse(resultArray[1] || "[]");
        
        // Display results
        showResults(messages);
    } catch (error) {
        console.error(error);
        outputFileContent = texText || "";
        showResults([`Critical error: ${error.message}`]);
    } finally {
        document.getElementById('loading').classList.add('d-none');
    }
});

// Show conversion results
function showResults(messages) {
    const messagesElement = document.getElementById('messages');
    const downloadBtn = document.getElementById('download-btn');
    const resultsDiv = document.getElementById('results');
    
    if (messages && messages.length > 0) {
        messagesElement.classList.remove('d-none');
        messagesElement.innerHTML = `
            <h4 class="alert-heading">Conversion Notices</h4>
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
