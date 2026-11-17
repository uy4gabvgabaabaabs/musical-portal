#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const ROOT = process.env.MUSICAL_PORTAL_ROOT || path.resolve(import.meta.dirname, "..");
const MASTER = path.join(ROOT, "public", "musical_portal_4409.csv");
const INPUT = process.argv[2];
const REPORT = path.join(ROOT, "public", "country_import_report.json");
const UNRESOLVED = path.join(ROOT, "public", "downloads", "country_unresolved.csv");

if (!INPUT) throw new Error("Usage: import-completed-countries.mjs <completed.csv>");

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (char === '"') {
      if (quoted && text[index + 1] === '"') { cell += '"'; index++; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[index + 1] === "\n") index++;
      row.push(cell); if (row.some(value => value !== "")) rows.push(row); row = []; cell = "";
    } else cell += char;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const headers = rows.shift().map(value => value.replace(/^\uFEFF/, ""));
  return { headers, rows: rows.map(values => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]))) };
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function csvText(headers, rows) {
  return "\uFEFF" + [headers.join(","), ...rows.map(row => headers.map(header => csvCell(row[header])).join(","))].join("\r\n") + "\r\n";
}

const [masterText, inputText] = await Promise.all([fs.readFile(MASTER, "utf8"), fs.readFile(INPUT, "utf8")]);
const [masterWorkbook, inputWorkbook] = await Promise.all([
  Workbook.fromCSV(masterText.replace(/^\uFEFF/, ""), { sheetName: "Portal" }),
  Workbook.fromCSV(inputText.replace(/^\uFEFF/, ""), { sheetName: "Completed" }),
]);
await Promise.all([
  masterWorkbook.inspect({ kind: "table", range: "'Portal'!A1:H4", include: "values", tableMaxRows: 4, tableMaxCols: 8 }),
  inputWorkbook.inspect({ kind: "table", range: "'Completed'!A1:L4", include: "values", tableMaxRows: 4, tableMaxCols: 12 }),
]);

const master = parseCsv(masterText);
const incoming = parseCsv(inputText);
const byFilmId = new Map(master.rows.map(row => [row.film_id, row]));
const seenFilmIds = new Set();
const seenImdbIds = new Set();
const rejected = [];
let imported = 0;

for (const row of incoming.rows) {
  const target = byFilmId.get(row.film_id);
  let reason = "";
  if (!target) reason = "film_id_not_found";
  else if (seenFilmIds.has(row.film_id)) reason = "duplicate_film_id";
  else if (seenImdbIds.has(row.imdb_id)) reason = "duplicate_imdb_id";
  else if (target.imdb_id !== row.imdb_id) reason = "imdb_mismatch";
  else if (target.title !== row.title) reason = "title_mismatch";
  else if (target.year !== row.year) reason = "year_mismatch";
  else if (target.country.trim()) reason = "country_already_present";
  else if (!row.country.trim()) reason = "country_not_found";
  else if (!["found", "confirmed"].includes(row.country_status.trim().toLowerCase())) reason = "status_not_confirmed";
  if (reason) rejected.push({ ...row, reason });
  else {
    target.country = row.country.trim();
    target.country_codes = row.country_codes.trim();
    target.country_source_url = row.country_source_url.trim();
    target.country_status = "confirmed_imdb";
    imported++;
  }
  seenFilmIds.add(row.film_id);
  seenImdbIds.add(row.imdb_id);
}

for (const field of ["country_codes", "country_source_url", "country_status"]) {
  if (!master.headers.includes(field)) master.headers.splice(master.headers.indexOf("country") + 1, 0, field);
}

const unitedStates = new Set(["usa", "us", "united states", "united states of america", "آمریکا", "ایالات متحده", "ایالات متحده آمریکا"]);
const totals = { total: master.rows.length, country_present: 0, country_missing: 0, global_any: 0, non_us_only: 0, us_and_global: 0, us_only: 0 };
for (const row of master.rows) {
  const countries = row.country.split(/[;؛|]/).map(value => value.trim().toLowerCase()).filter(Boolean);
  if (!countries.length) { totals.country_missing++; continue; }
  totals.country_present++;
  const hasUs = countries.some(value => unitedStates.has(value));
  const hasGlobal = countries.some(value => !unitedStates.has(value));
  if (hasGlobal) totals.global_any++;
  if (hasGlobal && hasUs) totals.us_and_global++;
  else if (hasGlobal) totals.non_us_only++;
  else totals.us_only++;
}

if (master.rows.length !== 4591) throw new Error(`Master row count changed: ${master.rows.length}`);
if (imported !== 3602) throw new Error(`Expected 3602 safe imports, got ${imported}`);

await fs.writeFile(MASTER, csvText(master.headers, master.rows), "utf8");
const unresolvedRows = master.rows.filter(row => !row.country.trim()).map(row => ({
  film_id: row.film_id, imdb_id: row.imdb_id, imdb_url: row.imdb_url, title: row.title,
  persian_title: row.persian_title, year: row.year, director: row.director,
  unresolved_reason: row.imdb_id ? "IMDb country not returned" : "IMDb ID missing",
}));
const unresolvedHeaders = ["film_id", "imdb_id", "imdb_url", "title", "persian_title", "year", "director", "unresolved_reason"];
await fs.mkdir(path.dirname(UNRESOLVED), { recursive: true });
await fs.writeFile(UNRESOLVED, csvText(unresolvedHeaders, unresolvedRows), "utf8");
await fs.writeFile(REPORT, JSON.stringify({ input_rows: incoming.rows.length, imported, rejected: rejected.length, rejected_reasons: Object.groupBy(rejected, row => row.reason), unresolved: unresolvedRows.length, totals }, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ imported, rejected: rejected.length, unresolved: unresolvedRows.length, totals }, null, 2));
