const form = document.querySelector("#analysis-form");
const fileInput = document.querySelector("#trips-csv");
const fileName = document.querySelector("#file-name");
const runButton = document.querySelector("#run-button");
const status = document.querySelector("#status");
const output = document.querySelector("#output");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "Choose a trip CSV";
});

function money(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function addText(parent, tag, text, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderTimeline(events = []) {
  const list = document.querySelector("#timeline");
  list.replaceChildren();
  events.forEach((event, index) => {
    const item = document.createElement("li");
    addText(item, "span", String(index + 1).padStart(2, "0"), "step-num");
    addText(item, "span", event.tool, "tool-name");
    const details = document.createElement("details");
    addText(details, "summary", "View input and observation");
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify({ input: event.input, observation: event.observation }, null, 2);
    details.append(pre);
    item.append(details);
    list.append(item);
  });
}

function renderResult(payload) {
  output.hidden = false;
  const errorBox = document.querySelector("#error-box");
  const content = document.querySelector("#results-content");
  const top = payload?.data ? payload : { ...payload, data: payload };
  const data = top.data || payload;
  const events = data.tool_calls || payload.tool_calls || [];
  renderTimeline(events);
  document.querySelector("#run-meta").textContent = `${data.total_time_ms ?? payload.total_time_ms ?? 0} ms · ${data.stop_reason || payload.stop_reason || "human_review"}`;
  if (!payload.success) {
    errorBox.hidden = false;
    errorBox.textContent = `${payload.error || "Analysis did not complete."} Stop reason: ${payload.stop_reason || "human_review"}.`;
    content.hidden = true;
    return;
  }
  errorBox.hidden = true;
  content.hidden = false;
  const costs = data.cost_breakdown;
  document.querySelector("#decision").textContent = data.decision;
  document.querySelector("#rationale").textContent = data.justification;
  document.querySelector("#steps").textContent = data.step_count;
  document.querySelector("#elapsed").textContent = `${data.total_time_ms} ms`;
  document.querySelector("#stop-reason").textContent = data.stop_reason;
  document.querySelector("#capture-date").textContent = data.citations.captured_at;
  document.querySelector("#hash").textContent = data.citations.sha256;
  const citation = document.querySelector("#pricing-citation");
  citation.href = data.citations.pricing_url;
  const chipBox = document.querySelector("#cost-comparison");
  chipBox.replaceChildren();
  [
    ["Pay per use", costs.pay_per_use_total],
    ["Membership + overage", costs.membership_total],
    ["Membership fees", costs.membership_fees],
    ["Residual overage", costs.membership_overage],
  ].forEach(([label, value]) => {
    addText(chipBox, "li", `${label}: ${money(value)}`);
  });
  const breakEvenRides = costs.break_even_rides_per_month ?? "Not reached";
  const breakEvenMinutes = costs.break_even_ride_minutes_per_month ?? "Not reached";
  document.querySelector("#actual-break-even").textContent =
    `Actual: ${costs.actual_rides_per_month} rides / ${costs.actual_ride_minutes_per_month} minutes per month. ` +
    `Break-even estimate: ${breakEvenRides} rides / ${breakEvenMinutes} minutes per month.`;
  const weekRows = document.querySelector("#weekly-rows");
  weekRows.replaceChildren();
  data.weekly_breakdown.forEach((week) => {
    const row = document.createElement("tr");
    [week.week, week.ride_count, `${week.average_duration_minutes} min`, money(week.pay_per_use_spend)].forEach((value) => addText(row, "td", String(value)));
    weekRows.append(row);
  });
  const passages = document.querySelector("#passages");
  passages.replaceChildren();
  (data.pricing_passages || []).forEach((passage) => {
    const item = document.createElement("li");
    item.textContent = `“${passage.text}” `;
    const link = document.createElement("a");
    link.href = passage.source;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "Source";
    item.append(link);
    passages.append(item);
  });
  document.querySelector("#caveats").textContent = data.assumptions_and_caveats.join("\n") || "No missing duration, date, member type, or bike type fields detected.";
  document.querySelector("#run-meta").textContent = `${data.cost_breakdown.trip_rows} trips · ${payload.total_time_ms ?? data.total_time_ms} ms · ${data.stop_reason}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files.length) return;
  runButton.disabled = true;
  status.textContent = "Reading trips and capturing the official pricing page…";
  output.hidden = true;
  const body = new FormData(form);
  try {
    const response = await fetch("/api/analyze", { method: "POST", body });
    const json = await response.json();
    const result = json.success ? { ...json.data, success: true } : { ...json, success: false };
    renderResult(result);
    status.textContent = result.success ? "Analysis complete." : "Analysis stopped; inspect the message and tool timeline.";
  } catch (error) {
    status.textContent = `Request failed: ${error.message}`;
  } finally {
    runButton.disabled = false;
  }
});