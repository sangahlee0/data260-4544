import React, { useState } from "react";

export default function CreateRecord({ onAdd }) {
    const [packageName, setPackageName] = useState("");
    const [vulnerabilityName, setVulnerabilityName] = useState("");

    async function handleSubmit(e) {
        e.preventDefault();
        await onAdd({ package_name: packageName, vulnerability_name: vulnerabilityName });
    }

    return (
        <div className="card">
            <div className="card-header">
                <div className="page-title">Add Vulnerability</div>
                <div className="subtitle">Enter vulnerability details below</div>
            </div>

            <div className="card-body">
                <form className="form" onSubmit={handleSubmit}>
                    <label>
                        Package Name
                        <input
                            value={packageName}
                            onChange={(e) => setPackageName(e.target.value)}
                            required
                        />
                    </label>

                    <label>
                        Vulnerability Name
                        <input
                            value={vulnerabilityName}
                            onChange={(e) => setVulnerabilityName(e.target.value)}
                            required
                        />
                    </label>

                    <button className="btn primary" type="submit">
                        Add Vulnerability
                    </button>
                </form>
            </div>
        </div>
    );
}