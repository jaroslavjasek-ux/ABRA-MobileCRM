import { mailHref, telHref, webHref } from "@/features/firms/format";
import { QuickActions } from "@/features/firms/QuickActions";
import { useI18n } from "@/i18n";

type ChannelDisplayProps = {
  phones?: string[];
  emails?: string[];
  website?: string;
  compact?: boolean;
  showWebsite?: boolean;
};

export function ChannelDisplay({
  phones = [],
  emails = [],
  website,
  compact = false,
  showWebsite = true,
}: ChannelDisplayProps) {
  const { t } = useI18n();
  const hasChannels =
    phones.length > 0 || emails.length > 0 || (showWebsite && Boolean(website));

  if (!hasChannels) {
    return null;
  }

  return (
    <div className={`channel-display${compact ? " channel-display--compact" : ""}`}>
      <dl className="channel-list">
        {phones.map((phone, index) => (
          <div key={`phone-${phone}`} className="channel-row">
            <dt>
              {phones.length > 1
                ? t("channel.phoneN", { n: index + 1 })
                : t("channel.phone")}
            </dt>
            <dd>
              <a href={telHref(phone)} className="channel-value">
                {phone}
              </a>
            </dd>
          </div>
        ))}
        {emails.map((email, index) => (
          <div key={`email-${email}`} className="channel-row">
            <dt>
              {emails.length > 1
                ? t("channel.emailN", { n: index + 1 })
                : t("channel.email")}
            </dt>
            <dd>
              <a href={mailHref(email)} className="channel-value">
                {email}
              </a>
            </dd>
          </div>
        ))}
        {showWebsite && website && (
          <div className="channel-row">
            <dt>{t("channel.website")}</dt>
            <dd>
              <a
                href={webHref(website)}
                className="channel-value"
                target="_blank"
                rel="noreferrer"
              >
                {website}
              </a>
            </dd>
          </div>
        )}
      </dl>
      <QuickActions
        phones={phones}
        emails={emails}
        website={showWebsite ? website : undefined}
        compact={compact}
      />
    </div>
  );
}
