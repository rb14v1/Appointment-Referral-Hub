/**
 * All appointment/slot times come back from the API as UTC ISO strings.
 * These helpers convert them to a clinic's local IANA timezone for display,
 * and never the other way around (bookings are always submitted as
 * UTC ISO strings built from a plain local Date, see BookAppointmentPage).
 */

export function formatInTimezone(isoUtc: string, timeZone: string, options?: Intl.DateTimeFormatOptions): string {
  const date = new Date(isoUtc);
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
    ...options,
  }).format(date);
}

export function formatDateInTimezone(isoUtc: string, timeZone: string): string {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeZone }).format(new Date(isoUtc));
}

export function formatTimeInTimezone(isoUtc: string, timeZone: string): string {
  return new Intl.DateTimeFormat("en-US", { timeStyle: "short", timeZone }).format(new Date(isoUtc));
}

/** Local browser timezone, used as a fallback when a clinic's timezone isn't loaded yet. */
export function browserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}
