import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchVulnerabilities, deleteVulnerability } from "../features/vulnerabilities/vulnerabilitiesSlice";
import { api } from "../api/axios";

export default function Home({ auth }) {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector((s) => s.vulnerabilities);

  useEffect(() => {
    if (auth.loggedIn) {
      dispatch(fetchVulnerabilities());
    }
  }, [auth.loggedIn, dispatch]);

  const vulnerabilities = items;


  // If not logged in, show a clear message (since backend is protected)
  if (!auth.loggedIn) {
    return (
      <div className="card">
        <div className="card-header">
          <div>
            <div className="page-title">Vulnerabilities</div>
            <div className="subtitle">
              Login first to fetch vulnerability records from the protected API.
            </div>
          </div>
        </div>

        <div className="card-body">
          <div className="notice">
            You are not logged in. Please login.
          </div>
        </div>
      </div>
    );
  }

  // Logged in: show vulnerability table
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="page-title">Vulnerabilities</div>
          <div className="subtitle">
            Session-based access: these vulnerabilities are fetched from FastAPI + MySQL using your cookie session.
          </div>
        </div>

        <Link className="btn primary" to="/create">
          + Add Vulnerability
        </Link>
      </div>

      <div className="card-body">
        {error && (
          <div className="notice">
            {String(error)}
          </div>
        )}
        {loading ? (
          <div className="notice">Loading vulnerabilities...</div>
        ) : vulnerabilities.length === 0 ? (
          <div className="notice">No vulnerabilities found. </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                    <th>ID</th>
                    <th>Package</th>
                    <th>Vulnerability</th>
                    <th>Code</th>
                    <th>Urgency</th>
                    <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {vulnerabilities.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.package_name}</td>
                    <td>{u.vulnerability_name}</td>
                    <td>{u.vulnerability_code}</td>
                    <td>{u.urgency_score}</td>
                    <td className="actions">
                      <Link className="btn" to={`/update/${u.id}`}>
                        Update
                      </Link>
                      <button
                        className="btn danger"
                        onClick={() => dispatch(deleteVulnerability(u.id))}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}