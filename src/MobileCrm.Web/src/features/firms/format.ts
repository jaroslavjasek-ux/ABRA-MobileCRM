import type { Address } from "@/api/types";

export function formatLocation(address?: Address): string | null {
  if (!address) {
    return null;
  }

  const line1 = address.line1?.trim();
  if (line1) {
    return line1;
  }

  const parts = [address.street, address.city, address.postCode].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : null;
}

function normalize(value: string): string {
  return value.replace(/\s+/g, " ").trim().toLowerCase();
}

export function isSameLocation(a?: Address, b?: Address): boolean {
  const la = formatLocation(a);
  const lb = formatLocation(b);
  if (!la || !lb) {
    return false;
  }
  return normalize(la) === normalize(lb);
}

export function collectReachChannels(
  main?: Address,
  electronic?: Address,
  website?: string,
): { phones: string[]; emails: string[]; website?: string } {
  const phones: string[] = [];
  const emails: string[] = [];

  const addPhone = (value?: string) => {
    if (value && !phones.includes(value)) {
      phones.push(value);
    }
  };

  const addEmail = (value?: string) => {
    if (value && !emails.includes(value)) {
      emails.push(value);
    }
  };

  for (const addr of [main, electronic]) {
    addPhone(addr?.phone1);
    addPhone(addr?.phone2);
    addEmail(addr?.email);
  }

  return {
    phones,
    emails,
    website: website?.trim() || undefined,
  };
}

export function telHref(phone: string): string {
  return `tel:${phone.replace(/\s/g, "")}`;
}

export function mailHref(email: string): string {
  return `mailto:${email}`;
}

export function webHref(url: string): string {
  return url.startsWith("http") ? url : `https://${url}`;
}
