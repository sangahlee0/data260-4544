import { configureStore } from "@reduxjs/toolkit";
import vulnerabilitiesReducer from "../features/vulnerabilities/vulnerabilitiesSlice";

export const store = configureStore({
  reducer: { vulnerabilities: vulnerabilitiesReducer }
});