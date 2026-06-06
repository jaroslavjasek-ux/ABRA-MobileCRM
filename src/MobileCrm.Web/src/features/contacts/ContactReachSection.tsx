import type { Address } from "@/api/types";
import { ChannelDisplay } from "@/features/firms/ChannelDisplay";
import { collectReachChannels, formatLocation } from "@/features/firms/format";
import { useI18n } from "@/i18n";

export function ContactReachSection({ address }: { address?: Address }) {
  const { t } = useI18n();
  const location = formatLocation(address);
  const channels = collectReachChannels(address);

  if (!location && channels.phones.length === 0 && channels.emails.length === 0) {
    return null;
  }

  return (
    <section className="detail-section detail-section--compact">
      <h2>{t("contact.reachContact")}</h2>
      {location && <p className="location-line">{location}</p>}
      <ChannelDisplay phones={channels.phones} emails={channels.emails} />
    </section>
  );
}
