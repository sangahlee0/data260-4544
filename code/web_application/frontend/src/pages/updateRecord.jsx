import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchVulnerabilityById } from "../api/usersApi.js";

export default function UpdateRecord({ onUpdate }) {
    const { id } = useParams();
    const vulnerabilityId = Number(id);

    const [packageName, setPackageName] = useState("");
    const [vulnerabilityName, setVulnerabilityName] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                setLoading(true);
                const vulnerability = await fetchVulnerabilityById(vulnerabilityId);
                setVulnerabilityName(vulnerability.vulnerability_name);
                setPackageName(vulnerability.package_name);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        })();
    }, [vulnerabilityId]);

    async function handleSubmit(e) {
        e.preventDefault();
        await onUpdate(vulnerabilityId, { package_name: packageName, vulnerability_name: vulnerabilityName });
    }

    if (loading) return <p>Loading vulnerability...</p>;

    return (
        <div className="card">
            <div className="card-header">
                <div className="page-title">Update Vulnerability (ID: {vulnerabilityId})</div>
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
                        Update Vulnerability
                    </button>
                </form>
            </div>
        </div>
    );
}