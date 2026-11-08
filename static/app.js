const $ = (id) => document.getElementById(id);

const PAGE_SIZE = 25;

let result = null;
let page = 0;
let busy = false;

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
}

function resetResults() {
  result = null;
  page = 0;

  $("results").hidden = true;
  $("error").hidden = true;
  $("status").textContent = "Ready when you are.";

  $("file-name").textContent =
    $("csv-file").files[0]?.name || "Choose a CSV file";
}

function setBusy(value) {
  busy = value;

  for (const id of ["csv-file", "analyze", "clear", "template"]) {
    $(id).disabled = value;
  }

  $("upload-form").setAttribute("aria-busy", String(value));

  $("analyze-label").textContent =
    value ? "Analyzing…" : "Analyze batch";
}

async function callApi(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(90000),
  });

  const contentType = response.headers.get("content-type") || "";

  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof data === "string"
        ? data
        : data.error || data.detail || data.message;

    throw new Error(
      typeof detail === "string"
        ? detail
        : JSON.stringify(detail || "The server rejected the request.")
    );
  }

  return data;
}

function downloadCsv(filename, rows) {
  const escapeCell = (value) =>
    `"${String(value).replaceAll('"', '""')}"`;

  const csv = rows
    .map((row) => row.map(escapeCell).join(","))
    .join("\r\n");

  const blob = new Blob([csv], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.append(link);
  link.click();
  link.remove();

  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$("csv-file").addEventListener("change", resetResults);

$("clear").addEventListener("click", () => {
  $("upload-form").reset();
  resetResults();
});

for (const eventName of [
  "dragenter",
  "dragover",
  "dragleave",
  "drop",
]) {
  $("dropzone").addEventListener(eventName, (event) => {
    event.preventDefault();

    const dragging =
      !busy && ["dragenter", "dragover"].includes(eventName);

    $("dropzone").classList.toggle("dragging", dragging);

    if (
      eventName === "drop" &&
      !busy &&
      event.dataTransfer.files.length
    ) {
      const transfer = new DataTransfer();

      transfer.items.add(event.dataTransfer.files[0]);

      $("csv-file").files = transfer.files;

      resetResults();
    }
  });
}

$("template").addEventListener("click", async () => {
  $("error").hidden = true;
  $("template").disabled = true;

  try {
    const schema = await callApi("/input_schema");

    downloadCsv(
      "networksecurity-template.csv",
      [schema.features]
    );

    $("status").textContent =
      "Column template downloaded. Add your encoded data rows.";
  } catch (error) {
    showError(error.message);
  } finally {
    $("template").disabled = busy;
  }
});

$("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  if (busy) return;

  const file = $("csv-file").files[0];

  resetResults();

  if (!file || !/\.csv$/i.test(file.name)) {
    showError("Choose a .csv file.");
    return;
  }

  if (file.size > 2 * 1024 * 1024) {
    showError("Choose a CSV file of 2 MiB or smaller.");
    return;
  }

  setBusy(true);

  $("status").textContent = "Reading and analyzing your batch…";

  try {
    // Decode explicitly so invalid UTF-8 does not silently change data.
    const buffer = await file.arrayBuffer();

    const csvText = new TextDecoder("utf-8", {
      fatal: true,
    }).decode(buffer);

    result = await callApi("/predict", {
      csv_text: csvText,
    });

    page = 0;
    $("filter").value = "all";

    $("total").textContent = result.total.toLocaleString();
    $("class-zero").textContent = result.class_0.toLocaleString();
    $("class-one").textContent = result.class_1.toLocaleString();
    $("result-file").textContent = file.name;

    renderTable();

    $("results").hidden = false;

    $("status").textContent =
      "Analysis complete. Your results are below.";

    $("results").scrollIntoView({
      block: "start",
    });
  } catch (error) {
    result = null;

    const message = ["TimeoutError", "AbortError"].includes(
      error.name
    )
      ? "The request timed out. Try a smaller batch."
      : error.message;

    showError(message || "Could not reach the prediction service.");

    $("status").textContent = "Analysis did not complete.";
  } finally {
    setBusy(false);
  }
});

function renderTable() {
  if (!result) return;

  const selectedClass = $("filter").value;

  const filteredRows = result.rows.filter(
    (row) =>
      selectedClass === "all" ||
      String(row.prediction) === selectedClass
  );

  const pageCount = Math.max(
    1,
    Math.ceil(filteredRows.length / PAGE_SIZE)
  );

  page = Math.max(0, Math.min(page, pageCount - 1));

  const header = document.createElement("tr");

  for (const column of result.columns) {
    const cell = document.createElement("th");

    cell.scope = "col";

    cell.textContent =
      column === "row_number" ? "Row" : column;

    header.append(cell);
  }

  $("table-head").replaceChildren(header);

  const fragment = document.createDocumentFragment();

  const visibleRows = filteredRows.slice(
    page * PAGE_SIZE,
    (page + 1) * PAGE_SIZE
  );

  for (const row of visibleRows) {
    const tableRow = document.createElement("tr");

    for (const column of result.columns) {
      const cell = document.createElement("td");

      if (column === "prediction") {
        const badge = document.createElement("span");

        badge.className = `badge badge-${row.prediction}`;
        badge.textContent = `Class ${row.prediction}`;

        cell.append(badge);
      } else {
        cell.textContent = row[column];
      }

      tableRow.append(cell);
    }

    fragment.append(tableRow);
  }

  $("table-body").replaceChildren(fragment);

  $("matching-count").textContent =
    `${filteredRows.length.toLocaleString()} matching rows`;

  $("page-info").textContent =
    `Page ${page + 1} of ${pageCount}`;

  $("previous").disabled = page === 0;
  $("next").disabled = page >= pageCount - 1;
}

$("filter").addEventListener("change", () => {
  page = 0;
  renderTable();
});

$("previous").addEventListener("click", () => {
  page -= 1;
  renderTable();
});

$("next").addEventListener("click", () => {
  page += 1;
  renderTable();
});

$("export").addEventListener("click", () => {
  if (!result) return;

  const rows = result.rows.map((row) =>
    result.columns.map((column) => row[column])
  );

  downloadCsv(
    "networksecurity-predictions.csv",
    [result.columns, ...rows]
  );
});