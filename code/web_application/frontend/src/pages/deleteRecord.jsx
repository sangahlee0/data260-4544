import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchVulnerabilityById } from "../api/usersApi.js";

export default function DeleteRecord({ onDelete }) {
    const { id } = useParams();
    const vulnerabilityId = Number(id);

    const [vulnerability, setVulnerability] = useState(null);

    useEffect(() => {
        (async () => {
            try {
                const data = await fetchVulnerabilityById(vulnerabilityId);
                setVulnerability(data);
            } catch {
                setVulnerability(null);
            }
        })();
    }, [vulnerabilityId]);

    async function handleDelete() {
        await onDelete(vulnerabilityId);
    }

    return (
        <div className="card">
            <div className="card-header">
                <div className="page-title">Delete Vulnerability</div>
            </div>

            <div className="card-body">
                {vulnerability ? (
                    <>
                        <p style={{ fontSize: "18px", marginBottom: "24px" }}>
                            Are you sure you want to delete <strong>{vulnerability.vulnerability_name}</strong> ({vulnerability.package_name})?
                        </p>

                        <button className="btn danger" onClick={handleDelete}>
                            Delete Vulnerability
                        </button>
                    </>
                ) : (
                    <div className="notice">
                        Vulnerability not found (or already deleted).
                    </div>
                )}
            </div>
        </div>
    );
}