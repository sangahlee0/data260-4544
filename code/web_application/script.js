// Base API URL
const API_URL = '/api/vulnerabilities';

// js function with arrow function syntax
const Validation = () => {
    // get the issue description field and check if it has more than 25 characters
    const issueDescr = document.getElementById("IssueDescription");

    if (issueDescr.value.trim().length <= 25) {
        alert("The description must contain more than 25 characters.");
        issueDescr.focus();
        return false;
    }

    const terms = document.getElementById("terms");

    if (!terms.checked) {
        alert("Please accept the Terms and Conditions.");
        terms.focus();
        return false;
    }
    
    // Collect values from the form fields and create a JSON object
    const value = {
        packageName: document.getElementById("PackageName").value,
        vulnerabilityName: document.getElementById("VulnerabilityName").value,
        reporterEmail: document.getElementById("ReporterEmail").value,
        severity: document.getElementById("Severity").value,
        issueDescription: document.getElementById("IssueDescription").value,
        terms: document.getElementById("terms").checked
    };
    const jsonString = JSON.stringify(value);
    console.log(jsonString);

    // extract the primary field and email field from the parsed object 
    const parsedObject = JSON.parse(jsonString);
    // log their values in the console
    const {packageName, reporterEmail} = parsedObject;
    console.log(packageName, reporterEmail);

    // Use spread operator
    // Add a new field submissionDate with the current date and time to the parsed object
    const updatedpObject = {
        ...parsedObject,
        submissionDate: new Date().toISOString()
    };

    // Log the updated parsed object in the console
    console.log(updatedpObject);

    // closure to track the number of times the form has been submitted successfully
    tracker();
    return true;
}

// Track how many times the form has been successfully submitted and log the submission count each time the form is submitted
const tracker = (() => {
    let count = 0;
    return function () {
        count++;
        console.log("Submission count:", count);
    };
})();

// Display list of records that have been added
const displayVulnerabilities = (vulnerabilities) => {
    const listEl = document.getElementById("feedbackList");
    const emptyEl = document.getElementById("emptyState");
    
    // Clear the list before displaying new records
    listEl.innerHTML = '';

    if (vulnerabilities.length === 0) {
        emptyEl.hidden = false;
        return;
    }
    emptyEl.hidden = true;

    vulnerabilities.forEach(v => {
        const li = document.createElement('li');
        li.textContent = `${v.package_name} — ${v.vulnerability_name} (${v.severity})`;
        listEl.appendChild(li);
    });
}

// Calls get request to the API to fetch all vulnerabilities and display them in the list
const loadVulnerabilities = async (search='') => {
    const loadingEl = document.getElementById("loadingState");
    const emptyEl = document.getElementById("emptyState");
    const errorEl = document.getElementById("errorState");

    loadingEl.hidden = false;
    emptyEl.hidden = true;
    errorEl.hidden = true;

    try {
        const response = await fetch(`${API_URL}?search=${encodeURIComponent(search)}`);
        if (!response.ok) throw new Error('Failed to fetch vulnerabilities');
        const vulnerabilities = await response.json();
        loadingEl.hidden = true;
        displayVulnerabilities(vulnerabilities);
    // Catch errors that occur during the fetch request and display message
    } catch (error) {
        console.error('Error loading vulnerabilities:', error);
        loadingEl.hidden = true;
        errorEl.hidden = false;
    }
}

// Runs existing validation function, sends the new vulnerability to the API, then resets the form and refreshes the list
const submitVulnerability = async (event) => {
    // Prevent the default form submission behavior
    event.preventDefault();
    // Run the existing validation function
    if (!Validation()) return;

    const data = {
        package_name: document.getElementById("PackageName").value,
        vulnerability_name: document.getElementById("VulnerabilityName").value,
        reporter_email: document.getElementById("ReporterEmail").value,
        severity: document.getElementById("Severity").value,
        issue_description: document.getElementById("IssueDescription").value
    };

    try {
        // Send a POST request to the API with the new vulnerability data
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to submit vulnerability');
        const newVulnerability = await response.json();
        console.log('New vulnerability submitted:', newVulnerability);

        // Reset the form after successful submission
        document.getElementById("vulnerabilityForm").reset();
        // Refresh the list of vulnerabilities
        loadVulnerabilities();
    } catch (error) {
        console.error('Error in submitting vulnerability:', error);
        document.getElementById("errorState").hidden = false;
    }
}

// Update existing record in the list of vulnerabilities
async function updateVulnerability() {
    const packageName = document.getElementById('PackageName').value.trim();
    const vulnerabilityName = document.getElementById('VulnerabilityName').value.trim();
    const emailInput = document.getElementById('ReporterEmail').value.trim();
    const severityInput = document.getElementById('Severity').value;
    const descriptionInput = document.getElementById('IssueDescription').value.trim();

    if (!packageName || !vulnerabilityName) {
        alert('Please enter both Package Name and new Vulnerability Name');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/1`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                package_name: packageName,
                vulnerability_name: vulnerabilityName,
                reporter_email: emailInput,
                severity: severityInput,
                issue_description: descriptionInput
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update vulnerability');
        }
        
        await loadVulnerabilities();
        alert(`Vulnerability ID 1 updated successfully`);
    } catch (error) {
        console.error('Error updating vulnerability:', error);
        alert('Failed to update vulnerability: ' + error.message);
    }
}

// Delete the record with the highest ID in the list of vulnerabilities
async function deleteHighestID() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Failed to fetch vulnerabilities');
        const vulnerabilities = await response.json();

        // Check whether list of vulnerabilities is empty before attempting to delete the highest ID
        if (vulnerabilities.length === 0) {
            alert('No vulnerabilities to delete');
            return;
        }

        const highestID = Math.max(...vulnerabilities.map(v => v.id));

        if (!confirm(`Are you sure you want to delete Vulnerability ID ${highestID}?`)) {
            return;
        }

        const deleteResponse = await fetch(`${API_URL}/${highestID}`, {
            method: 'DELETE'
        });

        if (!deleteResponse.ok) {
            const error = await deleteResponse.json();
            throw new Error(error.detail || 'Failed to delete vulnerability');
        }

        console.log(`Deleted Vulnerability ID ${highestID}`);
        await loadVulnerabilities();
        alert(`Vulnerability ID ${highestID} deleted successfully`);
    } catch (error) {
        console.error('Error deleting vulnerability:', error);
        alert('Failed to delete vulnerability: ' + error.message);
    }
}

// Load vulnerabilities when the page loads
window.addEventListener('DOMContentLoaded', loadVulnerabilities);

// Attach the submit event listener to the form
document.getElementById("vulnerabilityForm").addEventListener("submit", submitVulnerability);
// Attach the click event listener to the update button
document.getElementById("updateButton").addEventListener("click", updateVulnerability);
// Attach the click event listener to the delete button
document.getElementById("deleteButton").addEventListener("click", deleteHighestID);


// Attach the click event listener to the search button
document.getElementById("searchButton").addEventListener("click", async () => {
    const searchValue = document.getElementById("searchInput").value.trim();
    if (!searchValue) {
        alert("Please input a search.");
        return;
    }
    
    await loadVulnerabilities(searchValue);
});
// Attach the click event listener to the clear search button
document.getElementById("clearSearchButton").addEventListener("click", () => {
    document.getElementById("searchInput").value = '';
    loadVulnerabilities();
});
