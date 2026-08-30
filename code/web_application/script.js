// js function with arrow function syntax
const Validation = () => {
  // get the issue description field and check if it has more than 25 characters
  const issueDescr = document.getElementById("IssueDescription");

  if (issueDescr.value.trim().length <= 25) {
    alert("The issue description must contain more than 25 characters.");
    issueDescr.focus();
    return false;
  }

  // get all text fields and check if they have more than 25 characters
  const textFields = document.querySelectorAll(
    'input[type="text"], textarea'
  );

  for (const field of textFields) {
    if (field.value.trim().length <= 25) {
      alert("Each text field must contain more than 25 characters.");
      field.focus();
      return false;
    }
  }

  const terms = document.getElementById("terms");

  if (!terms.checked) {
    alert("Please indicate that you accept the Terms and Conditions.");
    terms.focus();
    return false;
  }

  // Collect values from the form fields and create a JSON object
  const value = {
    packageName: document.getElementById("packageName").value,
    vulnerabilityName: document.getElementById("vulnerabilityName").value,
    reporterEmail: document.getElementById("reporterEmail").value,
    severity: document.getElementById("severity").value,
    issueDescription: document.getElementById("issuedescrip").value,
    terms: document.getElementById("terms").checked};
    const jsonString = JSON.stringify(value);
    console.log(jsonString);

  // extract the primary field and email field from the parsed object 
  const parsedObject = JSON.parse(jsonString);
  // log their values in the console
  const { packageName, reporterEmail } = parsedObject;
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
  return false;
}

// Track how many times the form has been successfully submitted and log the submission count each time the form is submitted
const tracker = (() => {
  let count = 0;
  return function () {
    count++;
    console.log("Submission count:", count);
  };
})();