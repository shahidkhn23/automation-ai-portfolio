const assert = require("assert");
const fs = require("fs");
const { analyse, minusMonths, parseDate } = require("./extract.js");

// German sample: 3 months before 31.08.2027 is 31.05.2027
let r = analyse(fs.readFileSync("sample_contract_de.txt", "utf8"), "2026-11-24");
assert.strictEqual(r.cancel_by, "2027-05-31");
assert.strictEqual(r.end_date, "2027-08-31");
assert.strictEqual(r.auto_renewal, true);
assert.strictEqual(r.days_left, 188);
assert.ok(r.ics.includes("DTSTART;VALUE=DATE:20270531") && r.ics.includes("TRIGGER:-P14D"));

// English sample: 4 weeks before 2027-03-31 is 2027-03-03
r = analyse(fs.readFileSync("sample_contract_en.txt", "utf8"), "2026-11-24");
assert.strictEqual(r.cancel_by, "2027-03-03");
assert.strictEqual(r.notice_period, "4 weeks");

// Month arithmetic keeps the last day of a shorter month
assert.strictEqual(minusMonths(parseDate("31.05.2027"), 3).toISOString().slice(0, 10), "2027-02-28");

// Deadline already passed
r = analyse("Mietende 31.01.2026. Kündigungsfrist 3 Monate.", "2026-11-24");
assert.ok(r.days_left < 0 && r.warnings.some(w => w.includes("already passed")));

// Nothing found: no invented dates, a warning instead
r = analyse("Hello world", "2026-11-24");
assert.strictEqual(r.cancel_by, null);
assert.strictEqual(r.warnings.length, 2);

console.log("All contract-deadline tests passed.");
