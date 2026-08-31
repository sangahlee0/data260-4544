# Domain Schema: Open-Source Package Vulnerabilities

## Overview
This document defines the schema, field types, and allowed category values for the **Open-Source Package Vulnerabilities** domain entity used in HW01.

---

## Entity Fields

1. **Primary Field**
   - **ID / Name:** `PackageName`
   - **Type:** Text string
   - **Requirement:** Required, non-empty. Automatically focuses on page load (`autofocus`).
   - **Description:** The name of the affected open-source package (e.g., `numpy`, `lodash`).

2. **Secondary Field**
   - **ID / Name:** `VulnerabilityName`
   - **Type:** Text string
   - **Requirement:** Required, non-empty.
   - **Description:** A brief title or name describing the security bug or vulnerability.

3. **Submitter Email**
   - **ID / Name:** `ReporterEmail`
   - **Type:** Email string (HTML5 email validation)
   - **Requirement:** Required.
   - **Description:** Contact email address of the vulnerability reporter.

4. **Category / Severity Selection**
   - **ID / Name:** `Severity`
   - **Type:** Dropdown selection (`<select>`)
   - **Requirement:** Required; must select a valid severity level.
   - **Allowed Category / Severity Values:**
     - `Low`
     - `Medium`
     - `High`
     - `Critical`

5. **Content / Description**
   - **ID / Name:** `IssueDescription`
   - **Type:** Textarea (`rows="4"`, `cols="50"`)
   - **Requirement:** Required; must contain **more than 25 characters** (enforced by your JavaScript validation function).
   - **Description:** A comprehensive description of the vulnerability issue and reproduction details.

6. **Terms & Conditions**
   - **ID / Name:** `terms`
   - **Type:** Checkbox
   - **Requirement:** Must be checked to successfully submit the form.
   - **Description:** Agreement to the platform's terms and conditions (`I agree to the terms and conditions.`).