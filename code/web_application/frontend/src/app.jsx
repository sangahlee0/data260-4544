import React, { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

//import Navbar from "./components/Navbar.jsx";
import LoginBar from "./components/Login.jsx";

import Home from "./pages/Home.jsx";
import CreateRecord from "./pages/createRecord.jsx";
import UpdateRecord from "./pages/updateRecord.jsx";
import DeleteRecord from "./pages/deleteRecord.jsx";

import { fetchVulnerabilities, createVulnerability, updateVulnerability, deleteVulnerability } from "./api/usersApi.js";

export default function App() {
  const navigate = useNavigate();

  function RequireAuth({ auth, children }) {
  if (!auth.loggedIn) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="page-title">Login Required</div>
        </div>
        <div className="card-body">
          <div className="notice">Please login to access this page.</div>
        </div>
      </div>
    );
  }
  return children;
}

  // Auth state (cookie session is checked inside LoginBar via /auth/me)
  const [auth, setAuth] = useState({ loggedIn: false, userId: null });

  // Users data
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch users only when logged in
  useEffect(() => {
    (async () => {
      if (!auth.loggedIn) {
        setVulnerabilities([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await fetchVulnerabilities();
        setVulnerabilities(data);
      } catch (e) {
        console.error("fetchVulnerability failed:", e);
        // If session expired, backend returns 401; UI will show not logged in after next /auth/me check.
      } finally {
        setLoading(false);
      }
    })();
  }, [auth.loggedIn]);

  // Create (props)
  async function onAdd(newVulnerability) {
    const created = await createVulnerability(newVulnerability);
    setVulnerabilities((prev) => [...prev, created]);
    navigate("/");
  }

  // Update (props)
  async function onUpdate(id, updatedVulnerability) {
    const updated = await updateVulnerability(id, updatedVulnerability);
    setVulnerabilities((prev) => prev.map((u) => (u.id === id ? updated : u)));
    navigate("/");
  }

  // Delete (props)
  async function onDelete(id) {
    await deleteVulnerability(id);
    setVulnerabilities((prev) => prev.filter((u) => u.id !== id));
    navigate("/");
  }

  return (
    <div className="container">
      {/*<Navbar auth={auth} />*/}

      {/* Login session demo UI */}
      <LoginBar auth={auth} setAuth={setAuth} />

      <Routes>
        <Route path="/" element={<Home vulnerabilities={vulnerabilities} loading={loading} auth={auth} />} />
        <Route path="/create" element={<RequireAuth auth={auth}> <CreateRecord onAdd={onAdd} auth={auth} /></RequireAuth> }/>
        <Route path="/update/:id" element={<RequireAuth auth={auth}> <UpdateRecord onUpdate={onUpdate} auth={auth} /></RequireAuth>} />
        <Route path="/delete/:id" element={<RequireAuth auth={auth}> <DeleteRecord onDelete={onDelete} auth={auth} /></RequireAuth>} />
      </Routes>
    </div>
  );
}