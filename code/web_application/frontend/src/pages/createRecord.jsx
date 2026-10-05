import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { createVulnerability } from "../features/vulnerabilities/vulnerabilitiesSlice";
import { api } from "../api/axios";
import {useNavigate } from "react-router-dom";

export default function CreateRecord() {
    const dispatch = useDispatch();
    const { error } = useSelector((s) => s.vulnerabilities);
    const navigate = useNavigate();

    const [form, setForm] = useState({
        package_name: "",
        vulnerability_name: "",
        vulnerability_code: "",
    });

    const onChange = (e) => {
        const { name, value } = e.target;

        setForm((p) => ({
            ...p,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const res = await api.get("/api/packages");

        let packageMatch = res.data.find(
            (p) => p.name.toLowerCase() === form.package_name.toLowerCase()
        );

        if (!packageMatch) {
            const newPackageRes = await api.post("/api/packages", {
                name: form.package_name,
                version: "unknown",
                package_code: form.package_name.toLowerCase().replace(/\s+/g, "-")
            });
            packageMatch = newPackageRes.data;
        }

        await dispatch(
            createVulnerability({
                package_id: packageMatch.id,
                vulnerability_name: form.vulnerability_name,
                vulnerability_code: form.vulnerability_code,
            })
        ).unwrap();
        navigate("/");
    };

    return (
        <div className="card">
            <div className="card-header">
                <div className="page-title">Add Vulnerability</div>
                <div className="subtitle">Enter vulnerability details below</div>
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
                            name="package_name"
                            value={form.package_name}
                            onChange={onChange}
                            required
                        />
                    </label>

                    <label>
                        Vulnerability Name
                        <input
                            name="vulnerability_name"
                            value={form.vulnerability_name}
                            onChange={onChange}
                            required
                        />
                    </label>
                    <label>
                        Vulnerability Code
                        <input
                            name="vulnerability_code"
                            value={form.vulnerability_code}
                            onChange={onChange}
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