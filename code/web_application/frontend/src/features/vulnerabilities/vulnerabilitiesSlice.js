import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/axios";

const errMsg = (err, fallback) => {
  if (err.response?.data?.detail) return err.response.data.detail;
  // Network-style errors (backend down, wrong port, CORS preflight failure)
  if (err.message) return `${fallback}: ${err.message}`;
  return fallback;
};

export const fetchVulnerabilities = createAsyncThunk("vulnerabilities/fetchVulnerabilities", async (_, thunkAPI) => {
  try {
    const res = await api.get("api/vulnerabilities");
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to fetch vulnerabilities"));
  }
});

export const createVulnerability = createAsyncThunk("vulnerabilities/createVulnerability", async (payload, thunkAPI) => {
  try {
    const res = await api.post("api/vulnerabilities", payload);
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to create vulnerability"));
  }
});

export const updateVulnerability = createAsyncThunk("vulnerabilities/updateVulnerability", async ({ id, payload }, thunkAPI) => {
  try {
    const res = await api.put(`api/vulnerabilities/${id}`, payload);
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to update vulnerability"));
  }
});

export const deleteVulnerability = createAsyncThunk("vulnerabilities/deleteVulnerability", async (id, thunkAPI) => {
  try {
    await api.delete(`api/vulnerabilities/${id}`);
    return id;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to delete vulnerability "));
  }
});



const vulnerabilitiesSlice = createSlice({
    name: "vulnerabilities",
    initialState: {items: [], loading: false, error: null},
    reducers: {},
    extraReducers: (builder) => {
    builder
      .addCase(fetchVulnerabilities.pending, (s) => { s.loading = true; s.error = null; })
      .addCase(fetchVulnerabilities.fulfilled, (s, a) => { s.loading = false; s.items = a.payload; })
      .addCase(fetchVulnerabilities.rejected, (s, a) => { s.loading = false; s.error = a.payload; })

      .addCase(createVulnerability.fulfilled, (s, a) => { s.items.push(a.payload); })
      .addCase(createVulnerability.rejected, (s, a) => { s.error = a.payload; })

      .addCase(updateVulnerability.fulfilled, (s, a) => {
        const idx = s.items.findIndex((v) => v.id === a.payload.id);
        if (idx !== -1) s.items[idx] = a.payload;
      })
      .addCase(updateVulnerability.rejected, (s, a) => { s.error = a.payload; })

      .addCase(deleteVulnerability.fulfilled, (s, a) => {
        s.items = s.items.filter((v) => v.id !== a.payload);
      })
      .addCase(deleteVulnerability.rejected, (s, a) => { s.error = a.payload; });
  }
});

export default vulnerabilitiesSlice.reducer;
