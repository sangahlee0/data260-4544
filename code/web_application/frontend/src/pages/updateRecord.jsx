import React, { useEffect, useState } from "react";
import { useParams , useNavigate} from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { updateVulnerability } from "../features/vulnerabilities/vulnerabilitiesSlice";
import { fetchVulnerabilityById } from "../api/usersApi.js";
import { api } from "../api/axios";


export default function UpdateRecord() {
    const { id } = useParams();
    const vulnerabilityId = Number(id);

    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { error } = useSelector((s) => s.vulnerabilities);

    const [payload, setPayload] = useState({
        package_id: null,
        package_name: "",
        vulnerability_name: "",
        vulnerability_code: "",
    });

    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                setLoading(true);
                const vulnerability = await fetchVulnerabilityById(vulnerabilityId);
                setPayload({
                    package_id: vulnerability.package_id,
                    package_name: vulnerability.package_name,
                    vulnerability_name: vulnerability.vulnerability_name,
                    vulnerability_code: vulnerability.vulnerability_code
                });
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        })();
    }, [vulnerabilityId]);

    const onChange = (e) => {
        const { name, value } = e.target;
        setPayload((p) => ({
            ...p,
            [name]: value
        }));
    };

    async function handleSubmit(e) {
        e.preventDefault();
        const packageRes = await api.get("/api/packages");
        let packageMatch = packageRes.data.find(
            (p) => p.name.toLowerCase() === payload.package_name.toLowerCase()
        );

        if (!packageMatch) {
            const newPackageRes = await api.post("/api/packages", {
                name: payload.package_name,
                version: "unknown",
                package_code: payload.package_name.toLowerCase().replace(/\s+/g, "-")
            });
            packageMatch = newPackageRes.data;
        }
        await dispatch(updateVulnerability({ id: vulnerabilityId, payload: { package_id: packageMatch.id, vulnerability_name: payload.vulnerability_name, vulnerability_code: payload.vulnerability_code } })).unwrap();
        navigate("/");
    }

    if (loading) return <p>Loading vulnerability...</p>;

    return (
        <div className="card">
            <div className="card-header">
                <div className="page-title">Update Vulnerability (ID: {vulnerabilityId})</div>
            </div>

            <div className="card-body">
                {error && (
                    <div className="notice">
                        {String(error)}
                    </div>
                )}
                <form className="form" onSubmit={handleSubmit}>
                    <label>
                        Package Name
                        <input
                            value={payload.package_name}
                            onChange={onChange}
                            name="package_name"
                            required
                        />
                    </label>

                    <label>
                        Vulnerability Name
                        <input
                            value={payload.vulnerability_name}
                            onChange={onChange}
                            name="vulnerability_name"
                            required
                        />
                    </label>

                    <label>
                        Vulnerability Code
                        <input
                            value={payload.vulnerability_code}
                            onChange={onChange}
                            name="vulnerability_code"
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