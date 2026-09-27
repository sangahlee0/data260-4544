from .database import SessionLocal
from .models import Vulnerability, VulnerabilityDescription

import random

SEED = 4544 # based on my personal SEED value
random.seed(SEED)

package_names = [
    "react",
    "express",
    "axios",
    "django",
    "flask",
    "numpy",
    "pandas",
    "requests"
]

vulnerability_names = [
    "SQL Injection",
    "Cross-Site Scripting",
    "Path Traversal",
    "Command Injection",
    "Authentication Bypass",
    "Information Disclosure",
    "Denial of Service",
    "Remote Code Execution"
]

descriptions = [
    "Patch available",
    "Manual review recommended",
    "Potential exploit identified",
    "Affects older package versions",
    "Authentication logic should be reviewed",
    "Input validation issue detected",
    "Dependency should be upgraded",
    "Potential security risk",
    "Further investigation required",
    "Automated scan detected vulnerability"
]

def seed_data():
    db = SessionLocal()

    try:
        vulnerabilities = []

        # Seed 5000 vulnerability rows for testing
        for i in range(5000):
            vulnerability = Vulnerability(package_name=f"{random.choice(package_names)}-{i}", vulnerability_name=random.choice(vulnerability_names))

            db.add(vulnerability)
            vulnerabilities.append(vulnerability)

        # Commit so that MySQL generates the IDs into the database
        db.commit()

        # Refresh rows
        for vulnerability in vulnerabilities:
            db.refresh(vulnerability)

        # Create 200 related description records for testing (other table)
        for i in range(200):
            selected_vulnerability = random.choice(vulnerabilities)

            description = VulnerabilityDescription(vulnerability_id=selected_vulnerability.id, description=random.choice(descriptions))

            db.add(description)

        db.commit()

        print("Finished generating 5000 vulnerabilities.")
        print("Finished generating 200 vulnerability descriptions.")

    except Exception as e:
        db.rollback()
        print("There was an error while seeding", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()