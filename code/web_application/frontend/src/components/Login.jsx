import React, { useEffect, useState } from "react";
import { login, logout, me } from "../api/usersApi.js";

export default function LoginBar({ auth, setAuth }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // On refresh, check if cookie session exists
    useEffect(() => {
        (async () => {
            try {
                const data = await me();

                setAuth({ loggedIn: true, userId: data.user_id});
            } catch {
                setAuth({ loggedIn: false, userId: null });
            }
        })();
    }, [setAuth]);

    async function handleLogin(e) {
        e.preventDefault();

        if (!email || !password) return;

        try {
            const res = await login(email, password);

            setAuth({ loggedIn: true, userId: res.user_id, email:email });
            
            setEmail("");
            setPassword("");
        } catch (err) {
            alert("Login failed. Double check email and password.");
            console.error(err);
        }
    }

    async function handleLogout() {
        try {
            await logout();
        } finally {
            setAuth({ loggedIn: false, userId: null, email: null});
        }
    }

    return (
        <div className="loginbar">
            {auth.loggedIn ? (
                <>
                    <div className="loginbar-text">
                        ✅ Logged in as <b>{auth.email}</b>
                    </div>
                    <button className="btn danger" onClick={handleLogout}>
                        Logout
                    </button>
                </>
            ) : (
                <form className="loginbar-form" onSubmit={handleLogin}>
                    <div className="loginbar-text">
                        🔒 Not logged in
                    </div>
                    
                    <input
                        className="loginbar-input"
                        type="email"
                        placeholder="Enter email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />

   
                    <input
                        className="loginbar-input"
                        type="password"
                        placeholder="Enter Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                    <button className="btn primary" type="submit">
                        Login
                    </button>
                </form>
            )}
        </div>
    );
}