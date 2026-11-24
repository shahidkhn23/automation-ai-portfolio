// Finds the notice period and end date in a contract text (German or English),
// works out the last day to cancel, and builds a calendar file with a reminder.
// The same code runs inside the n8n Code node (see build_workflow.py) and in test.js.

const DATE = "(\\d{1,2}\\.\\d{1,2}\\.\\d{4}|\\d{4}-\\d{2}-\\d{2})";

function parseDate(s) {
  let m = s.match(/(\d{1,2})\.(\d{1,2})\.(\d{4})/);
  if (m) return new Date(Date.UTC(+m[3], +m[2] - 1, +m[1]));
  m = s.match(/(\d{4})-(\d{2})-(\d{2})/);
  return m ? new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])) : null;
}

function minusMonths(d, n) {
  const y = d.getUTCFullYear(), mo = d.getUTCMonth() - n, day = d.getUTCDate();
  const lastDay = new Date(Date.UTC(y, mo + 1, 0)).getUTCDate();
  return new Date(Date.UTC(y, mo, Math.min(day, lastDay)));
}

const iso = (d) => d.toISOString().slice(0, 10);

function buildIcs(title, date, note) {
  const d = iso(date).replace(/-/g, "");
  const stamp = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
  return ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//contract-deadline-guard//EN",
    "BEGIN:VEVENT", `UID:${d}-cancel@contract-deadline-guard`, `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${d}`, `SUMMARY:${title}`, `DESCRIPTION:${note}`,
    "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-P14D", `DESCRIPTION:${title} in 14 days`, "END:VALARM",
    "END:VEVENT", "END:VCALENDAR"].join("\r\n");
}

function analyse(text, today) {
  const now = today ? parseDate(today) : new Date();
  const warnings = [];
  const out = { notice_period: null, end_date: null, auto_renewal: false, cancel_by: null,
                days_left: null, warnings, ics: null };

  const n = text.match(/(Kündigungsfrist|notice period|notice of)[^.\n]{0,80}?(\d+)\s*(Monat\w*|Woche\w*|month\w*|week\w*)/i);
  if (n) out.notice_period = `${n[2]} ${n[3]}`;
  const e = text.match(new RegExp(
    "(befristet bis|Mietende|Vertragsende|Laufzeit bis|endet am|ends on|fixed term until|until)[^\\d]{0,30}" + DATE, "i"));
  if (e) out.end_date = iso(parseDate(e[2]));
  out.auto_renewal = /(verlängert sich|automatisch[^.]{0,40}verlänger|renews automatically|auto-?renew)/i.test(text);

  if (!n) warnings.push("No notice period found. Check the contract by hand.");
  if (!e) warnings.push("No end date found. Check the contract by hand.");
  if (n && e) {
    const amount = +n[2], unit = /^m/i.test(n[3]) ? "m" : "w";
    const end = parseDate(out.end_date);
    const cancelBy = unit === "m" ? minusMonths(end, amount) : new Date(end.getTime() - amount * 7 * 86400000);
    out.cancel_by = iso(cancelBy);
    out.days_left = Math.ceil((cancelBy - now) / 86400000);
    if (out.days_left < 0) warnings.push("The last day to cancel has already passed. Check what the contract says about renewal.");
    if (out.auto_renewal) warnings.push("The contract renews automatically if you do not cancel in time.");
    out.ics = buildIcs("Last day to cancel the contract", cancelBy,
      `Notice period ${out.notice_period}, contract ends ${out.end_date}. Information, not legal advice.`);
  }
  return out;
}

if (typeof module !== "undefined") module.exports = { analyse, parseDate, minusMonths };
