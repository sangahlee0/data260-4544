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

  return true;
}