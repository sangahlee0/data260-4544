function checkFields() {
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
  //Add event listener to the form submission to convert
  const value = {
    packageName: document.getElementById("packageName").value,
    vulnerabilityName: document.getElementById("vulnerabilityName").value,
    reporterEmail: document.getElementById("reporterEmail").value,
    severity: document.getElementById("severity").value,
    issueDescription: document.getElementById("issuedescrip").value,
    terms: document.getElementById("terms").checked};
    const jsonString = JSON.stringify(value);
    console.log(jsonString);
    return false;
}