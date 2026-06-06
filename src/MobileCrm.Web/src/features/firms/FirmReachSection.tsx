import type { Address } from "@/api/types";
import { ChannelDisplay } from "@/features/firms/ChannelDisplay";
import {
  collectReachChannels,
  formatLocation,
  isSameLocation,
} from "@/features/firms/format";
import { useI18n } from "@/i18n";

export function FirmReachSection({
  mainAddress,
  electronicAddress,
  website,
}: {
  mainAddress?: Address;
  electronicAddress?: Address;
  website?: string;
}) {
  const { t } = useI18n();
  const location = formatLocation(mainAddress);
  const altLocation =
    electronicAddress && !isSameLocation(mainAddress, electronicAddress)
      ? formatLocation(electronicAddress)
      : null;
  const channels = collectReachChannels(mainAddress, electronicAddress, website);

  if (
    !location &&
    !altLocation &&
    channels.phones.length === 0 &&
    channels.emails.length === 0 &&
    !channels.website
  ) {
    return null;
  }

  return (
    <section className="detail-section detail-section--compact">
      <h2>{t("firms.company")}</h2>
      {location && <p className="location-line">{location}</p>}
      {altLocation && (
        <p className="location-line location-line--alt">
          <span className="location-label">{t("firms.also")}</span> {altLocation}
        </p>
      )}
      <ChannelDisplay
        phones={channels.phones}
        emails={channels.emails}
        website={channels.website}
      />
    </section>
  );
}
